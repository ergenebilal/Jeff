"""Confirm the intentionally broken sandbox fixture stays outside active compile."""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'jeff2' / 'self_healing_sandbox' / 'test_broken.py'


def main():
    try:
        compile(FIXTURE.read_text(encoding='utf-8'), str(FIXTURE), 'exec')
    except SyntaxError:
        print('NEGATIVE_FIXTURE_REJECTED=1')
        return
    raise AssertionError('Broken sandbox fixture unexpectedly compiled')


if __name__ == '__main__':
    main()
