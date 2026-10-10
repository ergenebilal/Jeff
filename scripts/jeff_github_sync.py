"""Tool-independent, privacy-gated source mirror. Never changes production Git state.

The target is a dedicated GitHub branch, never the repository's development branch.
Incoming commit history is not exported: only stable current source bytes are copied.
Private runtime data, symlinks, oversized files and unknown binary formats are excluded.
"""
import argparse
import ast
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
import time
import tokenize
import io

SUFFIXES = {'.py', '.sh', '.ps1', '.js', '.cjs', '.mjs', '.ts', '.css', '.html',
            '.astro', '.md', '.json', '.yaml', '.yml', '.toml', '.ini', '.patch',
            '.service', '.timer', '.txt'}
PRIVATE_PARTS = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', 'evidence',
                 'reports', 'raporlar', 'backups', 'backup-jeff', '_archive',
                 '_on_hold', 'sessions', 'secrets', 'future'}
SECRET_PATTERNS = [
    re.compile(rb'\b[0-9]{8,12}:[A-Za-z0-9_-]{30,}\b'),
    re.compile(rb'\b(?:gh[pousr]_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{30,})\b'),
    re.compile(rb'\bsk-[A-Za-z0-9_-]{20,}\b'),
    re.compile(rb'\bAIza[A-Za-z0-9_-]{35}\b'),
    re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    re.compile(rb'\bxox[baprs]-[A-Za-z0-9-]{20,}\b'),
    re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
]
ASSIGNMENT = re.compile(rb'''(?i)\b(?:app_pw|password|passwd|api_key|secret|bot_token|tg_token|auth_token|access_token|refresh_token)['"]?\s*[:=]\s*['"]([^'"\r\n]{8,})['"]''')
PLACEHOLDERS = (b'example', b'fixture', b'dummy', b'placeholder', b'changeme',
                b'your_', b'test-', b'fake', b'<', b'xxx', b'none', b'development')
MAX_FILE = 2_000_000


class Blocked(RuntimeError):
    pass


def allowed(name):
    path = PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
        return False
    if any(part.lower() in PRIVATE_PARTS for part in path.parts):
        return False
    lower = path.name.lower()
    if (lower.startswith(('soul', 'user.', 'memory.', '.env', 'secrets', 'credentials'))
            or '.bak' in lower or lower.endswith(('.db', '.sqlite3', '.log', '.jsonl'))
            or lower in {'config.yaml', 'gateway.env', '.beyin-runtime.json', 'brain-state.json',
                         'pablo_human_behavior.py', 'test_pablo_human_behavior.py'}
            or lower.startswith('patch_') or lower.endswith('_workcopy.py')):
        return False
    return path.suffix.lower() in SUFFIXES or lower == '.gitignore'


def secret(data):
    if any(pattern.search(data) for pattern in SECRET_PATTERNS):
        return True
    for match in ASSIGNMENT.finditer(data):
        value = match.group(1).lower()
        if (not any(item in value for item in PLACEHOLDERS)
                and not value.startswith((b'http:', b'https:', b'os.environ', b'getenv', b'${'))):
            return True
    return False


def public_bytes(name, data):
    """Only explicit, documented private-setting transformations; never modify live files."""
    if len(data) > MAX_FILE or b'\0' in data:
        raise Blocked('unsupported_source')
    text = data.decode('utf-8-sig')
    if name.endswith('jeff_bridge_api.py') and 'DANISMAN_SABLON' in text:
        match = re.search(r'MÜKELLEF\n.*?\nDÖRT KOVA', text, re.S)
        if not match:
            raise Blocked('private_template_shape_changed')
        text = text[:match.start()] + ('MÜKELLEF\n'
            '- Mükellef, faaliyet, araç ve belge bilgilerini yalnız BAĞLAM alanından al.\n'
            '- Verilmeyen kişisel ayrıntıları varsayma; eksik bilgi için SUPHELI de.\n'
            '\nDÖRT KOVA') + text[match.end():]
    if name.endswith('notebooklm-health-check.sh'):
        text = re.sub(r'^CHAT_ID="[0-9]+"$',
                      'CHAT_ID="${TELEGRAM_OWNER_CHAT_ID:-${TELEGRAM_CHAT_ID:-}}"', text, flags=re.M)
        text = text.replace('if [ -n "$TELEGRAM_TOKEN" ] &&',
                            'if [ -n "$TELEGRAM_TOKEN" ] && [ -n "$CHAT_ID" ] &&')
    if name.endswith('notify-nlm-down.py'):
        if 'import os\n' not in text:
            text = 'import os\n' + text
        text = re.sub(r'^CHAT = "[0-9]+"$',
            'CHAT = os.environ.get("TELEGRAM_OWNER_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")\n'
            'if not CHAT:\n    print("OWNER CHAT NOT CONFIGURED")\n    sys.exit(1)', text, flags=re.M)
    result = text.replace('\r\n', '\n').encode('utf-8')
    if secret(result):
        raise Blocked('credential_gate')
    return result


def private_settings(name, data, identifiers):
    """Replace configured literal owner settings only in the public copy, not live source."""
    identifiers = [value.decode() for value in identifiers if value.decode().isdigit()]
    if not identifiers or not any(value.encode() in data for value in identifiers):
        return data
    text = data.decode('utf-8')
    if name.endswith('.py'):
        result = []
        for token in tokenize.generate_tokens(io.StringIO(text).readline):
            value = token.string
            if token.type == tokenize.STRING and any(item in value for item in identifiers):
                try:
                    literal = ast.literal_eval(value)
                except (SyntaxError, ValueError):
                    raise Blocked('private_setting_shape_changed')
                if not isinstance(literal, str):
                    raise Blocked('private_setting_shape_changed')
                parts = re.split('(' + '|'.join(re.escape(item) for item in identifiers) + ')', literal)
                fragments = ["__import__('os').environ.get('TELEGRAM_OWNER_CHAT_ID', '')"
                             if item in identifiers else repr(item) for item in parts if item]
                value = '(' + ' + '.join(fragments) + ')'
            elif token.type == tokenize.NUMBER and value in identifiers:
                value = "int(__import__('os').environ.get('TELEGRAM_OWNER_CHAT_ID', '0'))"
            elif token.type == tokenize.COMMENT:
                for item in identifiers:
                    value = value.replace(item, '<private-owner>')
            result.append(token._replace(string=value))
        text = tokenize.untokenize(result)
        compile(text, name, 'exec')
    elif name.endswith('.sh'):
        for item in identifiers:
            text = text.replace(item, '${TELEGRAM_OWNER_CHAT_ID:?owner not configured}')
    elif name.endswith('.md'):
        for item in identifiers:
            text = text.replace(item, '${TELEGRAM_OWNER_CHAT_ID}')
    else:
        raise Blocked('personal_identifier_gate')
    result = text.encode()
    if any(value.encode() in result for value in identifiers) or secret(result):
        raise Blocked('personal_identifier_gate')
    return result


def git(root, *args):
    result = subprocess.run(['git', '-c', 'gc.auto=0', '-C', str(root), *args],
                            capture_output=True, timeout=90,
                            env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'})
    if result.returncode:
        # Never expose remote error bodies, URLs with credentials or source contents.
        raise Blocked('git_' + args[0] + '_failed')
    return result.stdout


def repo_catalog(root):
    names = git(root, 'ls-files', '-z', '--cached', '--others', '--exclude-standard')
    return sorted({n.decode('utf-8') for n in names.split(b'\0') if n})


def add_file(files, output, path, private_identifiers):
    if not allowed(output) or not path.exists():
        return
    if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.is_file():
        raise Blocked('unsafe_source_path')
    if path.stat().st_size > MAX_FILE:
        raise Blocked('oversized_source')
    data = public_bytes(output, path.read_bytes())
    data = private_settings(output, data, private_identifiers)
    if any(identifier in data for identifier in private_identifiers):
        # Retain an explicit coverage gap, never silently publish personal identifiers.
        raise Blocked('personal_identifier_gate')
    files[output] = data


def capture(config):
    root = Path(config['source_repo']).resolve()
    identifiers = [value.encode() for value in config.get('private_identifiers', []) if len(value) >= 7]
    files = {}
    for name in repo_catalog(root):
        if name in config.get('private_paths', []):
            continue
        add_file(files, name, root / name, identifiers)
    for entry in config.get('installed_sources', []):
        if entry['target'] in config.get('private_paths', []):
            continue
        path = Path(entry['source'])
        if not path.is_file():
            raise Blocked('installed_source_missing')
        add_file(files, entry['target'], path, identifiers)
    inbox = config.get('windows_inbox')
    if inbox:
        packet = json.loads(Path(inbox).read_text())
        if packet.get('version') != 1 or not isinstance(packet.get('files'), dict):
            raise Blocked('windows_packet_invalid')
        files_from_windows = packet['files']
        if len(files_from_windows) > 100:
            raise Blocked('windows_packet_oversized')
        for name, item in files_from_windows.items():
            if not allowed(name) or not name.endswith('.py') or '/' in name:
                raise Blocked('windows_path_invalid')
            data = base64.b64decode(item['content'], validate=True)
            if hashlib.sha256(data).hexdigest() != item['sha256']:
                raise Blocked('windows_digest_invalid')
            target = 'runtime-source/windows/' + name
            data = public_bytes(target, data)
            data = private_settings(target, data, identifiers)
            if any(identifier in data for identifier in identifiers):
                raise Blocked('personal_identifier_gate')
            files[target] = data
        if not files_from_windows:
            raise Blocked('windows_coverage_empty')
    manifest = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}
    fingerprint = hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()
    return files, manifest, fingerprint


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2))
    temporary.chmod(0o600)
    temporary.replace(path)


def checked_sources(files, previous, syntax_exemptions=None):
    syntax_exemptions = syntax_exemptions or {}
    changed = [name for name, data in files.items() if previous.get(name) != hashlib.sha256(data).hexdigest()]
    for name in changed:
        if name.endswith('.py'):
            if syntax_exemptions.get(name) == hashlib.sha256(files[name]).hexdigest():
                continue  # Exact pinned invalid fixture; changed bytes still fail the gate.
            compile(files[name], name, 'exec')
    return changed


def mirror(config, files):
    root = Path(config['mirror_repo'])
    branch = config['branch']
    if not branch.startswith('codex/') or branch in {'main', 'master'}:
        raise Blocked('invalid_publication_branch')
    if not (root / '.git').exists():
        root.mkdir(parents=True, exist_ok=True)
        git(root, 'init')
        git(root, 'remote', 'add', 'origin', config['remote'])
        git(root, 'fetch', 'origin', 'refs/heads/' + config['seed_branch'])
        git(root, 'checkout', '-b', branch, 'FETCH_HEAD')
        for key in ['user.name', 'user.email']:
            value = git(Path(config['source_repo']), 'config', '--get', key).decode().strip()
            git(root, 'config', key, value)
    if git(root, 'branch', '--show-current').decode().strip() != branch:
        raise Blocked('mirror_branch_changed')
    remote_lines = git(root, 'ls-remote', 'origin', 'refs/heads/' + branch).decode().strip()
    if remote_lines:
        remote_head = remote_lines.split()[0]
        git(root, 'fetch', 'origin', 'refs/heads/' + branch)
        local_head = git(root, 'rev-parse', 'HEAD').decode().strip()
        if remote_head != local_head:
            local_is_ancestor = subprocess.run(['git', '-C', str(root), 'merge-base',
                '--is-ancestor', local_head, remote_head], capture_output=True).returncode == 0
            remote_is_ancestor = subprocess.run(['git', '-C', str(root), 'merge-base',
                '--is-ancestor', remote_head, local_head], capture_output=True).returncode == 0
            if local_is_ancestor:
                if git(root, 'status', '--porcelain').strip():
                    raise Blocked('publication_concurrent_edit')
                git(root, 'merge', '--ff-only', 'FETCH_HEAD')
            elif not remote_is_ancestor:
                raise Blocked('publication_history_diverged')
    # Managed worktree only: never unlink or alter the source checkout.
    for raw in git(root, 'ls-files', '-z').split(b'\0'):
        if not raw:
            continue
        name = raw.decode()
        if name not in files:
            target = root / name
            if not target.parent.resolve().is_relative_to(root.resolve()):
                raise Blocked('unsafe_mirror_path')
            if target.is_symlink() or target.is_file():
                # Unlink the tracked leaf only. Never follow a legacy seed link or alter its target.
                target.unlink()
    for name, data in files.items():
        target = root / name
        if target.is_symlink() or any(p.is_symlink() for p in target.parents if p != root.parent):
            raise Blocked('unsafe_mirror_path')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    git(root, 'add', '-A')
    changed = bool(git(root, 'diff', '--cached', '--name-only').strip())
    if changed:
        git(root, 'commit', '-m', 'chore: synchronize stable current Jeff source')
    head = git(root, 'rev-parse', 'HEAD').decode().strip()
    git(root, 'push', 'origin', 'HEAD:refs/heads/' + branch)
    verified = git(root, 'ls-remote', 'origin', 'refs/heads/' + branch).decode().split()
    if not verified or verified[0] != head:
        raise Blocked('remote_ref_not_verified')
    return head, changed


def cycle(config, now=None):
    now = time.time() if now is None else now
    state_path = Path(config['state'])
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    output = {'version': 1, 'observed_at': now, 'status': 'blocked',
              'last_success': state.get('last_success'), 'production_modified': False}
    try:
        files, manifest, fingerprint = capture(config)
        output['source_files'] = len(files)
        if state.get('candidate') != fingerprint:
            state.update(candidate=fingerprint, candidate_since=now)
            output['status'] = 'waiting_stable'
        elif now - state['candidate_since'] < config.get('settle_seconds', 60):
            output['status'] = 'waiting_stable'
        elif state.get('published') == fingerprint:
            output['status'] = 'no_change'
        else:
            changed = checked_sources(files, state.get('published_manifest', {}), config.get('syntax_exemptions'))
            # Check the whole source again immediately before staging/publication.
            if capture(config)[2] != fingerprint:
                raise Blocked('source_changed_during_capture')
            head, committed = mirror(config, files)
            # Changes during transport are observed on the next cycle, never called published.
            still_current = capture(config)[2] == fingerprint
            output.update(status='published' if still_current else 'published_previous_snapshot',
                          remote_commit=head, changed_files=len(changed), committed=committed,
                          latest_sources_match=still_current)
            state.update(published=fingerprint, published_manifest=manifest,
                         last_success={'observed_at': now, 'remote_commit': head,
                                       'source_files': len(files)})
            output['last_success'] = state['last_success']
    except Exception as error:
        output['failure_class'] = str(error) if isinstance(error, Blocked) else type(error).__name__
    state['last_status'] = output
    write_json(state_path, state)
    write_json(config['status'], output)
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    config = json.loads(Path(args.config).read_text())
    # This worker runs on Linux. A separate Windows collector does no Git operations.
    import fcntl
    lock_path = Path(config['state']).with_suffix('.lock')
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0
        result = cycle(config)
        print(json.dumps({k: result[k] for k in ('status', 'observed_at', 'production_modified')}))
        return 1 if result['status'] == 'blocked' else 0


if __name__ == '__main__':
    raise SystemExit(main())
