"""Content-addressed source inventory. No database, memory, or secret files."""
import argparse
import hashlib
import json
from pathlib import Path


def inventory(root):
    root = Path(root).resolve()
    return {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob('*.py')) if '__pycache__' not in path.parts and path.is_file()}


def differences(expected, actual):
    return {'missing': sorted(set(expected) - set(actual)), 'extra': sorted(set(actual) - set(expected)),
            'changed': sorted(name for name in set(expected) & set(actual) if expected[name] != actual[name])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1] / 'jeff_cognitive')
    parser.add_argument('--compare', type=Path)
    args = parser.parse_args()
    result = inventory(args.root)
    if args.compare:
        delta = differences(json.loads(args.compare.read_text(encoding='utf-8'))['files'], result)
        print(json.dumps(delta, indent=2))
        return int(any(delta.values()))
    print(json.dumps({'files': result}, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
