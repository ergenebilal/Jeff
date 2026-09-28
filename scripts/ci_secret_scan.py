"""Report credential locations without ever printing credential values."""
import argparse
from pathlib import Path
import re
import subprocess
import sys


PATTERNS = {
    'telegram_bot_token': re.compile(rb'\b[0-9]{8,12}:[A-Za-z0-9_-]{30,}\b'),
    'github_token': re.compile(rb'\b(?:gh[pousr]_[A-Za-z0-9_]{30,}|github_pat_[A-Za-z0-9_]{30,})\b'),
    'openai_key': re.compile(rb'\bsk-[A-Za-z0-9_-]{20,}\b'),
    'aws_access_key': re.compile(rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'google_api_key': re.compile(rb'\bAIza[A-Za-z0-9_-]{35}\b'),
    'slack_token': re.compile(rb'\bxox[baprs]-[A-Za-z0-9-]{20,}\b'),
}
ASSIGNMENT = re.compile(
    rb'(?i)\b(?:app_pw|password|passwd|api_key|secret|bot_token|tg_token)\s*=\s*'
    rb'[\'\"]([^\'\"\r\n]{8,})[\'\"]')
PLACEHOLDERS = (b'example', b'fixture', b'dummy', b'placeholder', b'changeme',
                b'your_', b'test-', b'fake', b'<', b'xxx', b'none', b'development')
TEXT_SUFFIXES = {'.py', '.sh', '.js', '.ts', '.json', '.yaml', '.yml', '.toml',
                 '.md', '.env', '.txt', '.service', '.timer'}


def findings(data):
    result = []
    for number, line in enumerate(data.splitlines(), 1):
        for name, pattern in PATTERNS.items():
            if pattern.search(line):
                result.append((number, name))
        match = ASSIGNMENT.search(line)
        if match:
            value = match.group(1).lower()
            if (not any(item in value for item in PLACEHOLDERS)
                    and not value.startswith((b'http:', b'https:', b'os.environ', b'getenv'))):
                result.append((number, 'literal_credential_assignment'))
    return result


def blob_kinds(data):
    """Fast presence-only scan for historical blobs; no line-level output."""
    kinds = {name for name, pattern in PATTERNS.items() if pattern.search(data)}
    for match in ASSIGNMENT.finditer(data):
        value = match.group(1).lower()
        if (not any(item in value for item in PLACEHOLDERS)
                and not value.startswith((b'http:', b'https:', b'os.environ', b'getenv'))):
            kinds.add('literal_credential_assignment')
            break
    return kinds


def tracked_scan(root):
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).split(b'\0')
    result = []
    for raw in names:
        if not raw:
            continue
        relative = raw.decode('utf-8', errors='replace')
        path = root / relative
        if path.suffix.lower() not in TEXT_SUFFIXES or not path.is_file():
            continue
        if path.stat().st_size > 2_000_000:
            continue
        for line, kind in findings(path.read_bytes()):
            result.append((relative, line, kind))
    return result


def history_scan(root):
    """Scan all locally available Git blob objects; report object IDs only."""
    process = subprocess.Popen(
        ['git', '-c', 'gc.auto=0', 'cat-file', '--batch-all-objects', '--batch'],
        cwd=root, stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL)
    result = set()
    try:
        while header := process.stdout.readline():
            object_id, object_type, raw_size = header.split()
            size = int(raw_size)
            data = process.stdout.read(size)
            process.stdout.read(1)  # Git's object separator newline.
            if object_type == b'blob' and size <= 2_000_000 and b'\0' not in data:
                for kind in blob_kinds(data):
                    result.add((object_id[:12].decode(), kind))
    finally:
        process.stdout.close()
        process.wait()
    if process.returncode:
        raise RuntimeError('Git history scan failed')
    return sorted(result)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--history', action='store_true')
    parser.add_argument('--summary-only', action='store_true')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    root = args.root.resolve()
    if args.history:
        result = history_scan(root)
        if not args.summary_only:
            for object_id, kind in result:
                print(f'git-object:{object_id}: {kind}')
    else:
        result = tracked_scan(root)
        for path, line, kind in result:
            print(f'{path}:{line}: {kind}')
    print(f'SECRET_FINDINGS={len(result)}')
    return 1 if result else 0


if __name__ == '__main__':
    sys.exit(main())
