"""Nightly backup of everything that cannot be rebuilt from git: Jeff's brain and memory included.

    python scripts/jeff_backup.py [--dest DIR] [--keep N] [--home DIR]

What it does, in order:
 1. Takes a consistent snapshot of every SQLite database (online backup API) and checks each copy.
 2. Packs configs, memory, sessions, skills, cron jobs, Jeff's own code and the site/chat/bridge data.
    Big things that can be re-installed (node, git checkouts, caches, logs, the old backups) are skipped.
 3. Re-opens the finished archive and checks that the files we cannot live without are inside.
 4. Keeps the newest N archives.
Exit code is non-zero (and the archive is discarded) if any required item is missing or unreadable.
"""
import argparse
import fnmatch
import glob
import json
import os
import re
import shutil
import sqlite3
import sys
import io
import subprocess
import tarfile
import time
import hashlib
from pathlib import Path, PurePosixPath

REQUIRED = [
    'home/hermes/.hermes/config.yaml',
    'home/hermes/.hermes/gateway.env',
    'db/home__hermes__.hermes__state.db',
]
CORE_SOURCE_PATHS = (
    '.hermes/skills/system/jeff-beyin/SKILL.md',
    'jeff_repo/scripts/jeff_memory_context.py', 'jeff_repo/scripts/jeff_status.py',
    'jeff_repo/jeff2/bridge/jeff_bridge_api.py', 'jeff_repo/jeff2/bridge/approval_ledger.py',
    'jeff_repo/pablo/hermes_node.py', 'jeff_repo/pablo/pablo_task_guard.py',
    'jeff_repo/pablo/pablo_work_plans.py', 'jeff-v0.21.5/src/run_agent.py',
    'jeff-v0.21.5/site/openai/__init__.py',
    'jeff-beyin/.beyin-runtime.json', 'jeff-beyin/.claude/scripts/beyin_v3.py',
    '.venv/lib/python3.12/site-packages/aiosqlite/__init__.py',
)
CORE_DATABASE_PATHS = ('jeff_repo/jeff2/bridge/bridge.db', '.local/share/beyin-v3/memory.sqlite3')
# Directory names that are skipped anywhere inside a backed-up tree.
SKIP_DIRS = {'node_modules', '__pycache__', '.git', 'venv', '.venv', '.cache', 'cache', 'logs', 'backups',
             '.playwright-mcp', 'lsp', 'node', 'hermes-agent', 'tests', 'site', 'checkpoints', 'dist-packages'}
SKIP_FILE_PATTERNS = ['*.pyc', '*.log', '*.db-wal', '*.db-shm', '*.sqlite-wal', '*.sqlite-shm', '*.tmp', '*.sock']
DB_SUFFIXES = ('.db', '.sqlite', '.sqlite3')


OPT_TREES = (Path('/opt/hermes'), Path('/usr/lib/python3/dist-packages'))


def trees(home, opt_trees=OPT_TREES):
    h = Path(home)
    return [h / '.hermes', h / 'jeff_cognitive', h / 'jeff-v0.21.5' / 'src', h / 'cybergene-chat', h / 'pipeline',
            h / 'jeff-beyin', h / 'cybergeneos-data', h / 'cybergeneos', h / 'jeff-artifacts',
            h / '.alert.env', h / '.config', h / 'jeff_repo',
            h / 'jeff-v0.21.5' / 'live_ext', h / 'jeff-v0.21.5' / 'site',
            h / '.local/share/beyin-v3',
            *sorted((h / '.local/lib').glob('python*/site-packages')),
            *sorted((h / '.venv/lib').glob('python*/site-packages')), *opt_trees]


ETC_PATTERNS = [
    '/etc/nginx/sites-available/cybergene.co',
    '/etc/systemd/system/hermes-*.service', '/etc/systemd/system/hermes-*.service.d/*.conf',
    '/etc/systemd/system/jeff-*.service', '/etc/systemd/system/alfred-*.service',
    '/etc/systemd/system/cybergene-*.service', '/etc/systemd/system/cybergeneos.service',
    '/etc/systemd/system/cybergeneos.service.d/*.conf', '/etc/systemd/system/mail-webhook.service',
    '/etc/jeff-*.env', '/etc/supervisor/conf.d/*.conf', '/etc/fail2ban/jail.local',
    '/etc/ssh/sshd_config.d/*.conf',
]


def etc_files(patterns=ETC_PATTERNS):
    found = []
    for pattern in patterns:
        found += sorted(glob.glob(pattern))
    return [f for f in found if os.path.isfile(f) and '.bak' not in os.path.basename(f)]


def etc_arcname(path):
    """Files under /etc keep their whole location in the name, so no two can collide and the manifest is mechanical."""
    posix = rel(path)
    if posix.startswith('etc/'):
        return 'etc/' + posix[4:].replace('/', '__')
    parent = Path(path).parent.name
    return 'etc/' + (parent + '__' if parent.endswith('.d') else '') + Path(path).name


def extra_db_paths(home):
    h = Path(home)
    return [h / 'jeff_repo/jeff2/bridge/bridge.db', h / '.n8n/database.sqlite']


def find_databases(home, opt_trees=OPT_TREES):
    """Every *.db / *.sqlite that belongs to a backed-up tree (skipping the folders we skip)."""
    found = set(p for p in extra_db_paths(home) if p.is_file())
    for root in trees(home, opt_trees):
        if not root.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in filenames:
                if name.endswith(DB_SUFFIXES):
                    found.add(Path(dirpath) / name)
    return sorted(found)


def rel(path):
    """Archive-style path: forward slashes, no drive letter, no leading slash (same on Linux and Windows)."""
    return re.sub(r'^[A-Za-z]:', '', Path(path).as_posix()).lstrip('/')


def flat_name(path):
    return rel(path).replace('/', '__')


def _integrity(path):
    conn = sqlite3.connect(path)
    try:
        return conn.execute('PRAGMA integrity_check').fetchone()[0]
    finally:
        conn.close()


def snapshot_databases(paths, workdir, log):
    """Consistent copy of each database via SQLite's online backup API.
    A copy that cannot be made is an error. A copy that is made but fails integrity_check (for example a
    damaged search index) is still KEPT, because a slightly damaged backup beats none, and reported as a warning."""
    out = Path(workdir) / 'db'
    out.mkdir(parents=True, exist_ok=True)
    copied, errors, warnings = {}, [], []
    for src in paths:
        dst = out / flat_name(src)
        try:
            source = sqlite3.connect(Path(src).resolve().as_uri() + '?mode=ro', uri=True, timeout=30)
            target = sqlite3.connect(dst)
            try:
                source.backup(target)
            finally:
                target.close()
                source.close()
            verdict = _integrity(dst)
            if verdict != 'ok':
                warnings.append(f'{src}: integrity_check says "{verdict[:80]}"')
            copied[str(src)] = dst
        except (sqlite3.Error, OSError) as exc:
            errors.append(f'{src}: {type(exc).__name__}')
            dst.unlink(missing_ok=True)
    (out / 'MANIFEST.json').write_text(json.dumps({flat_name(src): str(src) for src in copied}, indent=1), encoding='utf-8')
    log(f'databases: {len(copied)} copied, {len(errors)} failed, {len(warnings)} with integrity warnings')
    for line in errors:
        log('FAILED: ' + line)
    for line in warnings:
        log('WARNING: ' + line)
    return copied, errors + warnings


def _skipped(name):
    return any(fnmatch.fnmatch(name, pat) for pat in SKIP_FILE_PATTERNS)


def add_tree(tar, root, db_sources, log):
    """Add a folder or file, skipping heavy/re-creatable folders and the live database files
    (their consistent snapshots are stored separately)."""
    root = Path(root)
    if not root.exists():
        log(f'skip (missing): {root}')
        return 0
    added = 0
    if root.is_file():
        tar.add(root, arcname=rel(root))
        return 1
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            path = Path(dirpath) / name
            if _skipped(name) or str(path) in db_sources or name.endswith(DB_SUFFIXES):
                continue
            try:
                if path.is_symlink() or path.is_file():
                    tar.add(path, arcname=rel(path), recursive=False)
                    added += 1
            except OSError as exc:
                log(f'unreadable, skipped: {path} ({type(exc).__name__})')
    return added


def package_inventory(home, runner=subprocess.run):
    """What is installed where, so a rebuild on a fresh machine does not miss a package (the 'mcp' SDK once did)."""
    h = Path(home)
    sources = {
        'etc/pip-freeze-jeff-site.txt': ['python3.11', '-m', 'pip', 'freeze', '--path', str(h / 'jeff-v0.21.5' / 'site')],
        'etc/pip-freeze-user.txt': ['python3.11', '-m', 'pip', 'freeze', '--user'],
        'etc/pip-freeze-bridge.txt': [str(h / '.venv/bin/python'), '-m', 'pip', 'freeze'],
        'etc/host-os-release.txt': ['cat', '/etc/os-release'],
        'etc/node-global.txt': ['npm', 'ls', '-g', '--depth=0'],
        'etc/crontab-hermes.txt': ['crontab', '-l'],
    }
    out = {}
    for name, cmd in sources.items():
        try:
            res = runner(cmd, capture_output=True, text=True, timeout=120,
                         env={**os.environ, 'PATH': f'{h}/.hermes/node/bin:' + os.environ.get('PATH', '')})
            text = (res.stdout or '').strip()
            if text:
                out[name] = text + '\n'
        except (OSError, subprocess.SubprocessError):
            continue
    return out


def add_system_file(tar, path, now, log, runner=subprocess.run):
    """Add a file from /etc. If this user may not read it, try passwordless sudo; if that fails too, say so and go on:
    one unreadable file must never cost the whole backup."""
    name = etc_arcname(path)
    try:
        tar.add(path, arcname=name)
        return True
    except OSError:   # PermissionError in practice; anything unreadable gets the sudo attempt
        pass
    try:
        res = runner(['sudo', '-n', 'cat', str(path)], capture_output=True, timeout=30)
        if res.returncode == 0:
            info = tarfile.TarInfo(name)
            info.size, info.mtime, info.mode = len(res.stdout), int(now()), 0o600
            tar.addfile(info, io.BytesIO(res.stdout))
            return True
    except (OSError, subprocess.SubprocessError):
        pass
    log(f'WARNING: could not read {path}')
    return False


def verify_archive(archive, required):
    with tarfile.open(archive, 'r:gz') as tar:
        names = set(tar.getnames())
    return [r for r in required if r not in names]


def core_sources(home):
    """Hashes of current required infrastructure; no config/credential content in this manifest."""
    return {rel(Path(home) / name): hashlib.sha256((Path(home) / name).read_bytes()).hexdigest()
            for name in CORE_SOURCE_PATHS}


def verify_core_sources(archive):
    try:
        with tarfile.open(archive, 'r:gz') as tar:
            manifest = json.load(tar.extractfile('etc/CORE-SOURCES.json'))
            if not isinstance(manifest, dict) or not manifest:
                return ['invalid core source manifest']
            for name, expected in manifest.items():
                member = tar.getmember(name)
                if not member.isfile() or hashlib.sha256(tar.extractfile(member).read()).hexdigest() != expected:
                    return ['core source hash mismatch: ' + name]
    except (KeyError, TypeError, ValueError, OSError, tarfile.TarError):
        return ['unreadable core source manifest']
    return []


def prune(dest, keep):
    archives = sorted(Path(dest).glob('jeff-backup-*.tar.gz'), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in archives[keep:]:
        old.unlink()
    return min(len(archives), keep)


def run(home='/home/hermes', dest='/home/hermes/backups', keep=10, extra_files=(), log=print, now=time.time,
        opt_trees=OPT_TREES):
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    os.chmod(dest, 0o700)
    stamp = time.strftime('%Y%m%d-%H%M%S', time.localtime(now()))
    archive, partial = dest / f'jeff-backup-{stamp}.tar.gz', dest / f'.jeff-backup-{stamp}.tar.gz.tmp'
    work = dest / f'.work-{stamp}'
    work.mkdir(mode=0o700)
    try:
        try:
            core = core_sources(home)
        except OSError as exc:
            log('ERROR: required core source missing or unreadable (' + type(exc).__name__ + ')')
            return 1
        dbs = find_databases(home, opt_trees)
        copied, errors = snapshot_databases(dbs, work, log)
        with tarfile.open(partial, 'w:gz', compresslevel=3) as tar:
            tar.add(work / 'db', arcname='db')
            data = json.dumps(core, indent=1).encode('utf-8')
            info = tarfile.TarInfo('etc/CORE-SOURCES.json')
            info.size, info.mtime, info.mode = len(data), int(now()), 0o600
            tar.addfile(info, io.BytesIO(data))
            etc_manifest = {}
            for extra in extra_files:
                if not Path(extra).is_file():
                    continue
                if add_system_file(tar, extra, now, log):
                    etc_manifest[etc_arcname(extra)[len('etc/'):]] = str(extra)
                else:
                    errors.append(f'{extra}: unreadable')
            manifest_bytes = json.dumps(etc_manifest, indent=1).encode('utf-8')
            info = tarfile.TarInfo('etc/MANIFEST.json')
            info.size, info.mtime, info.mode = len(manifest_bytes), int(now()), 0o600
            tar.addfile(info, io.BytesIO(manifest_bytes))
            for name, text in package_inventory(home).items():
                data = text.encode('utf-8')
                info = tarfile.TarInfo(name)
                info.size, info.mtime, info.mode = len(data), int(now()), 0o600
                tar.addfile(info, io.BytesIO(data))
                log(f'package inventory: {name} ({len(text.splitlines())} lines)')
            files = sum(add_tree(tar, root, {str(p) for p in dbs}, log) for root in trees(home, opt_trees))
        log(f'files packed: {files}')
        missing = verify_archive(partial, REQUIRED_FOR(home)) + verify_core_sources(partial)
        if missing:
            partial.unlink(missing_ok=True)
            log('ERROR: archive is missing required items: ' + ', '.join(missing))
            return 1
        os.chmod(partial, 0o600)
        partial.rename(archive)
        log(f'OK {archive.name} {archive.stat().st_size / 1e6:.0f} MB; archives kept: {prune(dest, keep)}')
        return 0 if not errors else 3   # 3 = archive is good but some database could not be copied
    finally:
        for path in sorted(work.rglob('*'), reverse=True):
            path.unlink() if path.is_file() or path.is_symlink() else path.rmdir()
        work.rmdir()
        partial.unlink(missing_ok=True)


def verify_latest(dest, home='/home/hermes', log=print, max_age_hours=30, now=time.time):
    """Restore drill: unpack the newest archive's databases into a temp folder, check each one,
    and confirm the files Jeff cannot live without are inside. Touches nothing that is live."""
    archives = sorted(Path(dest).glob('jeff-backup-*.tar.gz'), key=lambda p: p.stat().st_mtime)
    if not archives:
        log('ERROR: no backup found')
        return 1
    newest = archives[-1]
    age_h = (now() - newest.stat().st_mtime) / 3600
    problems = []
    if age_h > max_age_hours:
        problems.append(f'newest backup is {age_h:.0f} hours old')
    try:
        missing = verify_archive(newest, REQUIRED_FOR(home))
    except (tarfile.TarError, OSError, EOFError) as exc:
        log(f'ERROR: archive unreadable ({type(exc).__name__})')
        return 1
    problems += [f'missing {m}' for m in missing] + verify_core_sources(newest)
    checked = 0
    import tempfile
    with tempfile.TemporaryDirectory() as tmp, tarfile.open(newest, 'r:gz') as tar:
        members = [m for m in tar.getmembers() if m.isfile() and m.name.startswith('db/') and not m.name.endswith('MANIFEST.json')]
        for member in members:
            # Do not trust archive paths, links or extraction filters of older Python versions.
            target = Path(tmp) / Path(member.name).name
            with tar.extractfile(member) as source, target.open('wb') as dest:
                shutil.copyfileobj(source, dest)
            conn = sqlite3.connect(target)
            try:
                verdict = conn.execute('PRAGMA integrity_check').fetchone()[0]
                conn.execute('SELECT count(*) FROM sqlite_master').fetchone()
            except sqlite3.Error as exc:
                verdict = type(exc).__name__
            finally:
                conn.close()
            checked += 1
            if verdict != 'ok':
                problems.append(f'{member.name}: {verdict}')
    log(f'{newest.name}: {checked} databases restored and checked, {age_h:.0f} hours old')
    for problem in problems:
        log('PROBLEM: ' + problem)
    return 1 if problems else 0


def restore(staging, root='/', apply=False, log=print):
    """Copy every database and /etc file of an UNPACKED archive back to its original location (from the manifests).
    Never overwrites an existing file; a rehearsal unless apply=True."""
    staging, root = Path(staging), Path(root)
    plan = []
    for area in ('db', 'etc'):
        manifest = staging / area / 'MANIFEST.json'
        if not manifest.is_file():
            log(f'ERROR: {manifest} is missing (was the archive unpacked into {staging}?)')
            return 1
        try:
            entries = json.loads(manifest.read_text(encoding='utf-8'))
            if not isinstance(entries, dict):
                raise ValueError('invalid manifest')
            for name, original in entries.items():
                if not isinstance(name, str) or not isinstance(original, str):
                    raise ValueError('invalid manifest entry')
                if '/' in name or '\\' in name or name in ('', '.', '..') or ':' in name:
                    raise ValueError('unsafe source name')
                relative = original.replace('\\', '/')
                if '..' in PurePosixPath(relative).parts:
                    raise ValueError('unsafe target path')
                source, target = staging / area / name, root / rel(relative)
                if source.is_symlink() or not source.resolve().is_relative_to((staging / area).resolve()):
                    raise ValueError('unsafe source link')
                if not target.resolve().is_relative_to(root.resolve()):
                    raise ValueError('unsafe target link')
                plan.append((source, target))
        except (ValueError, TypeError, OSError):
            log('ERROR: invalid or unsafe restore manifest')
            return 1
    # Validate every source before writing any part of a restore.
    if any(not source.is_file() for source, _ in plan):
        log('ERROR: a manifest source is missing')
        return 1
    copied = skipped = 0
    for source, target in plan:
        if not source.is_file():
            log(f'ERROR: {source} listed in the manifest but not unpacked')
            return 1
        if target.exists():
            skipped += 1
            log(f'exists, left alone: {target}')
            continue
        log(('copy ' if apply else 'would copy ') + f'{source.name} -> {target}')
        if apply:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        copied += 1
    log(f'{copied} to restore, {skipped} already present' + ('' if apply else ' (rehearsal: nothing written, add --apply)'))
    return 0


def REQUIRED_FOR(home):
    """Required archive members, rewritten for a non-default home directory."""
    prefix = rel(home)
    out = []
    for item in REQUIRED:
        if item.startswith('home/hermes/'):
            out.append(item.replace('home/hermes', prefix, 1))
        elif item.startswith('db/home__hermes__'):
            out.append(item.replace('home__hermes', prefix.replace('/', '__'), 1))
        else:
            out.append(item)
    return out + [prefix + '/' + name for name in CORE_SOURCE_PATHS] + [
        'db/' + flat_name(Path(home) / name) for name in CORE_DATABASE_PATHS] + ['etc/CORE-SOURCES.json']


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--home', default='/home/hermes')
    ap.add_argument('--dest', default='/home/hermes/backups')
    ap.add_argument('--keep', type=int, default=10)
    ap.add_argument('--verify-latest', action='store_true', help='restore drill on the newest archive; changes nothing')
    ap.add_argument('--extra', action='append', default=[])
    ap.add_argument('--restore', metavar='STAGING_DIR', help='put databases and /etc files from an unpacked archive back where they came from (rehearsal unless --apply)')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--root', default='/', help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    args.extra = list(args.extra) or etc_files()
    if args.restore:
        return restore(args.restore, args.root, args.apply, log=lambda m: print(f'[restore] {m}', flush=True))
    if args.verify_latest:
        return verify_latest(args.dest, args.home, log=lambda m: print(f'[backup-drill] {m}', flush=True))
    return run(args.home, args.dest, args.keep, args.extra, log=lambda m: print(f'[backup] {m}', flush=True))


if __name__ == '__main__':
    sys.exit(main())
