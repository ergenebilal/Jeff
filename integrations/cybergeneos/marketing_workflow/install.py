"""Review/stage the integration against its inspected panel source; no services or DBs touched."""
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
    panel = repo_root.resolve() / 'docs/cybergeneos'
    baseline = json.loads((bundle / 'baseline-normalized-hashes.json').read_text())
    target = json.loads((bundle / 'target-hashes.json').read_text())
    def normalized_hash(path):
        return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest() if path.exists() else None
    if all(normalized_hash(panel / name) == expected for name, expected in target.items()):
        print('Panel integration already matches all target fingerprints. No files changed.')
        return
    for name in target:
        path = panel / name
        if name in baseline:
            actual = normalized_hash(path)
            if actual != baseline[name]:
                raise RuntimeError('Panel source changed; reconcile before installation: ' + name)
        elif path.exists():
            raise RuntimeError('New target already exists: ' + name)
    with tempfile.TemporaryDirectory(prefix='cgos-marketing-') as temp:
        stage = Path(temp)
        for name in target:
            old, new = panel / name, stage / 'docs/cybergeneos' / name
            new.parent.mkdir(parents=True, exist_ok=True)
            if old.exists():
                new.write_bytes(old.read_bytes().replace(b'\r\n', b'\n'))
        result = subprocess.run(['git', 'apply', '--ignore-space-change', str(bundle / 'marketing.patch')],
                                cwd=stage, capture_output=True)
        if result.returncode:
            raise RuntimeError('Panel patch could not be staged')
        for name in ('server/jeff.py', 'server/marketing.py'):
            shutil.copy2(bundle / name, stage / 'docs/cybergeneos' / name)
        for name, expected in target.items():
            staged_path = stage / 'docs/cybergeneos' / name
            staged_path.write_bytes(staged_path.read_bytes().replace(b'\r\n', b'\n'))
            if hashlib.sha256((stage / 'docs/cybergeneos' / name).read_bytes()).hexdigest() != expected:
                raise RuntimeError('Staged fingerprint differs: ' + name)
        if apply:
            # The replaced legacy module had a literal fallback. Do not strand a connection.
            if not os.environ.get('HERMES_API_KEY') or not os.environ.get('HERMES_API_URL'):
                raise RuntimeError('Set the private Hermes environment before replacing the legacy connection')
            backup = Path(tempfile.mkdtemp(prefix='cgos-marketing-backup-', dir=repo_root.resolve().parent))
            os.chmod(backup, 0o700)
            for name in target:
                old = panel / name
                if old.exists():
                    saved = backup / name
                    saved.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(old, saved)
                    os.chmod(saved, 0o600)
            for name in target:
                old, new = panel / name, stage / 'docs/cybergeneos' / name
                temp_path = old.with_suffix(old.suffix + '.marketing-temp')
                shutil.copy2(new, temp_path)
                os.replace(temp_path, old)
            print('Panel files installed; backup contains private legacy source:', backup)
        else:
            print('Panel integration staged and all target fingerprints matched. No live files changed.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', required=True, type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    install(args.repo_root, args.apply)
