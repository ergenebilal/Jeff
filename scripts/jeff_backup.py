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
import os
import re
import sqlite3
import sys
import io
import subprocess
import tarfile
import time
from pathlib import Path

REQUIRED = [
    'home/hermes/.hermes/config.yaml',
    'home/hermes/.hermes/gateway.env',
    'db/home__hermes__.hermes__state.db',
]
# Directory names that are skipped anywhere inside a backed-up tree.
SKIP_DIRS = {'node_modules', '__pycache__', '.git', 'venv', '.venv', '.cache', 'cache', 'logs', 'backups',
             '.playwright-mcp', 'lsp', 'node', 'hermes-agent', 'tests', 'site', 'checkpoints', 'dist-packages'}
SKIP_FILE_PATTERNS = ['*.pyc', '*.log', '*.db-wal', '*.db-shm', '*.sqlite-wal', '*.sqlite-shm', '*.tmp', '*.sock']
DB_SUFFIXES = ('.db', '.sqlite')


OPT_TREES = (Path('/opt/hermes'),)


def trees(home, opt_trees=OPT_TREES):
    h = Path(home)
    return [h / '.hermes', h / 'jeff_cognitive', h / 'jeff-v0.21.5' / 'src', h / 'cybergene-chat', h / 'pipeline',
            h / '.alert.env', h / '.config', *opt_trees]


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
        'etc/node-global.txt': ['npm', 'ls', '-g', '--depth=0'],
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


def verify_archive(archive, required):
    with tarfile.open(archive, 'r:gz') as tar:
        names = set(tar.getnames())
    return [r for r in required if r not in names]


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
        dbs = find_databases(home, opt_trees)
        copied, errors = snapshot_databases(dbs, work, log)
        with tarfile.open(partial, 'w:gz') as tar:
            tar.add(work / 'db', arcname='db')
            for extra in extra_files:
                if Path(extra).is_file():
                    tar.add(extra, arcname='etc/' + Path(extra).name)
            for name, text in package_inventory(home).items():
                data = text.encode('utf-8')
                info = tarfile.TarInfo(name)
                info.size, info.mtime, info.mode = len(data), int(now()), 0o600
                tar.addfile(info, io.BytesIO(data))
                log(f'package inventory: {name} ({len(text.splitlines())} lines)')
            files = sum(add_tree(tar, root, {str(p) for p in dbs}, log) for root in trees(home, opt_trees))
        log(f'files packed: {files}')
        missing = verify_archive(partial, REQUIRED_FOR(home))
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
    problems += [f'missing {m}' for m in missing]
    checked = 0
    import tempfile
    with tempfile.TemporaryDirectory() as tmp, tarfile.open(newest, 'r:gz') as tar:
        members = [m for m in tar.getmembers() if m.isfile() and m.name.startswith('db/')]
        for member in members:
            tar.extract(member, tmp)
            conn = sqlite3.connect(Path(tmp) / member.name)
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
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--home', default='/home/hermes')
    ap.add_argument('--dest', default='/home/hermes/backups')
    ap.add_argument('--keep', type=int, default=10)
    ap.add_argument('--verify-latest', action='store_true', help='restore drill on the newest archive; changes nothing')
    ap.add_argument('--extra', action='append', default=[
        '/etc/nginx/sites-available/cybergene.co', '/etc/systemd/system/hermes-gateway.service',
        '/etc/systemd/system/cybergene-chat.service', '/etc/systemd/system/jeff-bridge.service',
        '/etc/jeff-bridge.env'])
    args = ap.parse_args(argv)
    if args.verify_latest:
        return verify_latest(args.dest, args.home, log=lambda m: print(f'[backup-drill] {m}', flush=True))
    return run(args.home, args.dest, args.keep, args.extra, log=lambda m: print(f'[backup] {m}', flush=True))


if __name__ == '__main__':
    sys.exit(main())
