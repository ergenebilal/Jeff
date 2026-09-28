"""Clean checkout bootstrap: one command creates a venv and runs active tests."""
from pathlib import Path
import subprocess
import sys
import venv


ROOT = Path(__file__).resolve().parents[1]
ENV_DIR = ROOT / '.venv-active'


def main():
    if not ENV_DIR.exists():
        venv.EnvBuilder(with_pip=True).create(ENV_DIR)
    python = (ENV_DIR / 'Scripts' / 'python.exe' if sys.platform == 'win32'
              else ENV_DIR / 'bin' / 'python')
    subprocess.run([str(python), '-m', 'pip', 'install', '-r',
                    str(ROOT / 'jeff2' / 'bridge' / 'requirements.txt')], check=True)
    subprocess.run([str(python), str(ROOT / 'scripts' / 'run_active_tests.py')],
                   cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
