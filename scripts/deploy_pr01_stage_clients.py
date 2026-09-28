"""Stage existing Jeff Bridge clients with an environment supplied key."""
from pathlib import Path
import py_compile
import re

PATHS = (
    Path('/opt/hermes/antigravity_telegram_bot_hybrid.py'),
    Path('/opt/hermes/telegram_claude_bot.py'),
    Path('/home/hermes/.hermes/scripts/alfred_tool.py'),
    Path('/home/hermes/jeff-github-repo/scripts/alfred_tool.py'),
)

for path in PATHS:
    raw = path.read_bytes()
    patched, count = re.subn(
        rb'(?m)^BRIDGE_KEY = .*$',
        b'BRIDGE_KEY = os.environ.get("BRIDGE_KEY")',
        raw,
    )
    if count != 1:
        raise RuntimeError(f'Expected one key assignment in {path.name}; found {count}')
    staged = path.with_name(path.name + '.pr01-staged.py')
    staged.write_bytes(patched)
    py_compile.compile(str(staged), doraise=True)
    print(path.name, 'staged and compiled')
