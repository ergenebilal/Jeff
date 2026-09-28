"""Create a cold-code and consistent SQLite backup before PR-01 deployment."""
from pathlib import Path
import shutil
import sqlite3

root = Path('/home/hermes/pr01-20260928-deploy-backup')
root.mkdir(mode=0o700, exist_ok=False)
paths = (
    Path('/home/hermes/jeff2/bridge/jeff_bridge_api.py'),
    Path('/home/hermes/jeff2/bridge/alfred_client.py'),
    Path('/home/hermes/jeff2/bridge/self_healing_engine.py'),
    Path('/etc/systemd/system/jeff-bridge.service'),
    Path('/opt/hermes/antigravity_telegram_bot_hybrid.py'),
    Path('/opt/hermes/telegram_claude_bot.py'),
    Path('/home/hermes/.hermes/scripts/alfred_tool.py'),
    Path('/home/hermes/jeff-github-repo/scripts/alfred_tool.py'),
)
for source in paths:
    target = root / source.relative_to('/')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
with sqlite3.connect('/home/hermes/jeff2/bridge/bridge.db') as source:
    with sqlite3.connect(str(root / 'bridge.db')) as target:
        source.backup(target)
print('backup_files=', len(paths), 'backup_db_bytes=', (root / 'bridge.db').stat().st_size)
