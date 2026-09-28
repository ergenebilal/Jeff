"""Apply fatal Ruff rules only to manifest-listed active Python files."""
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / 'ACTIVE_CODE.json').read_text(encoding='utf-8'))
    paths = (manifest['production_entrypoints'] + manifest['active_modules']
             + manifest['active_tests'])
    subprocess.run([sys.executable, '-m', 'ruff', 'check', '--select', 'E9,F63,F7,F82', *paths],
                   cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
