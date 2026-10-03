"""Stage the two static panel files; refuse unknown edits and preserve a source backup."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def install(repo_root, apply=False):
    bundle = Path(__file__).resolve().parent
    root = repo_root.resolve()
    panel = root / 'docs/cybergeneos'
    baseline = json.loads((bundle / 'baseline-normalized-hashes.json').read_text())
    target = json.loads((bundle / 'target-hashes.json').read_text())
    assert set(baseline) == set(target) == {'app.js', 'index.html'}

    def digest(path):
        return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest() if path.exists() else None

    if all(digest(panel / name) == value for name, value in target.items()):
        print('Decision-first files already installed; no changes.')
        return
    for name, value in baseline.items():
        if digest(panel / name) != value:
            raise RuntimeError('Panel changed; reconcile first: ' + name)
    with tempfile.TemporaryDirectory(prefix='cgos-decision-first-') as temp:
        stage = Path(temp)
        staged = stage / 'docs/cybergeneos'
        staged.mkdir(parents=True)
        for name in target:
            (staged / name).write_bytes((panel / name).read_bytes().replace(b'\r\n', b'\n'))
        subprocess.run(['git', 'apply', '--ignore-space-change', str(bundle / 'decision-first.patch')], cwd=stage, check=True, capture_output=True)
        for name, value in target.items():
            if digest(staged / name) != value:
                raise RuntimeError('Staged fingerprint differs: ' + name)
        if not apply:
            print('Patch staged; both fingerprints match. Live files unchanged.')
            return
        for name, value in baseline.items():
            if digest(panel / name) != value:
                raise RuntimeError('Panel changed during staging: ' + name)
        backup = Path(tempfile.mkdtemp(prefix='cgos-decision-first-backup-', dir=root.parent))
        os.chmod(backup, 0o700)
        for name in target:
            shutil.copy2(panel / name, backup / name)
            os.chmod(backup / name, 0o600)
        for name in target:
            pending = panel / (name + '.decision-first-temp')
            shutil.copy2(staged / name, pending)
            os.replace(pending, panel / name)
        print('Two static files installed; source backup:', backup)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', required=True, type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    install(args.repo_root, args.apply)
