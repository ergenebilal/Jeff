"""Does the code Pablo actually runs (C:\\CyberGene\\HermesNode, not a git folder) match the repository's pablo/ folder?

    python scripts/pablo_drift.py [--live C:\\CyberGene\\HermesNode] [--repo <repo>/pablo] [--sync]

Only Python source is compared; configs, databases, logs, backups and anything that may hold secrets are
never read. Without --sync it only reports. With --sync it copies files that differ FROM the live folder
INTO the repository folder (the live node is the one that runs, so it is the truth); committing stays a
separate, reviewed step.
"""
import argparse
import fnmatch
import hashlib
import shutil
import sys
from pathlib import Path

SKIP_PARTS = {'__pycache__', '.git', 'node_modules', 'venv', '.venv', 'logs', 'backups'}
SKIP_NAMES = {'config.json', '.env'}
# Differences that are on purpose: scratch copies, one-off patches, and the human-behaviour layer that was
# deliberately kept out of the public repository (plan 1.9). Tests only exist in git, not in the running folder.
INTENTIONAL_LIVE_ONLY = ('*_workcopy.py', 'patch_*.py', 'pablo_human_behavior.py', 'test_pablo_human_behavior.py')


def _ignored(path):
    name = path.name
    return (any(p in SKIP_PARTS for p in path.parts) or name in SKIP_NAMES or '.bak' in name
            or name.endswith(('.pyc', '.log', '.db', '.sqlite', '.tmp')))


def _digest(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()   # line endings are not a difference


def python_files(root):
    root = Path(root)
    return {p.relative_to(root).as_posix(): p for p in root.rglob('*.py') if not _ignored(p.relative_to(root))}


def compare(live, repo):
    live_files, repo_files = python_files(live), python_files(repo)
    changed = sorted(n for n in live_files.keys() & repo_files.keys() if _digest(live_files[n]) != _digest(repo_files[n]))
    return {
        'live_only': sorted(n for n in live_files.keys() - repo_files.keys()
                            if not any(fnmatch.fnmatch(Path(n).name, pat) for pat in INTENTIONAL_LIVE_ONLY)),
        'repo_only': sorted(n for n in repo_files.keys() - live_files.keys() if not Path(n).name.startswith('test_')),
        'changed': changed,
        'same': len(live_files.keys() & repo_files.keys()) - len(changed),
    }


def sync(live, repo, names):
    for name in names:
        target = Path(repo) / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(Path(live) / name, target)


def report(result):
    lines = [f"Ayni: {result['same']} dosya"]
    for key, label in (('changed', 'Canli klasorde FARKLI (git eski)'), ('live_only', 'Calisiyor ama git\'te YOK'),
                       ('repo_only', 'Git\'te var, calisan klasorde yok')):
        if result[key]:
            lines.append(f'{label}: {len(result[key])}')
            lines.extend(f'   - {n}' for n in result[key][:15])
    return '\n'.join(lines)


def main(argv=None):
    here = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser()
    ap.add_argument('--live', default=r'C:\CyberGene\HermesNode')
    ap.add_argument('--repo', default=str(here / 'pablo'))
    ap.add_argument('--sync', action='store_true', help='copy live -> repo for files that differ or are missing in git')
    args = ap.parse_args(argv)
    if not Path(args.live).is_dir():
        print(f'live folder not found: {args.live}', file=sys.stderr)
        return 2
    result = compare(args.live, args.repo)
    print(report(result))
    if args.sync and (result['changed'] or result['live_only']):
        sync(args.live, args.repo, result['changed'] + result['live_only'])
        print(f"kopyalandi: {len(result['changed']) + len(result['live_only'])} dosya (canli -> git klasoru); simdi gozden gecirip commit edin")
    return 0 if not (result['changed'] or result['live_only']) else 1


if __name__ == '__main__':
    sys.exit(main())
