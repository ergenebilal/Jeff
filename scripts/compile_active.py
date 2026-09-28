"""Compile only Python paths declared active in ACTIVE_CODE.json."""
import json
from pathlib import Path
import py_compile


ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / 'ACTIVE_CODE.json').read_text(encoding='utf-8'))
    paths = (manifest['production_entrypoints'] + manifest['active_modules']
             + manifest['active_tests'])
    for relative in paths:
        path = ROOT / relative
        if path.suffix != '.py' or not path.is_file():
            raise ValueError(f'Active Python file missing: {relative}')
        py_compile.compile(str(path), doraise=True)
    print(f'COMPILED_ACTIVE={len(paths)}')


if __name__ == '__main__':
    main()
