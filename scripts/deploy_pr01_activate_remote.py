"""Activate already staged PR-01 files on Jeff, leaving services running."""
from pathlib import Path
import os
import py_compile
import shutil
import stat
import subprocess

backup = Path('/home/hermes/pr01-20260928-deploy-backup')
if not (backup / 'bridge.db').is_file():
    raise SystemExit('Verified deployment backup is missing')

staged = (
    (Path('/home/hermes/jeff2/bridge/jeff_bridge_api_pr01_staged.py'), Path('/home/hermes/jeff2/bridge/jeff_bridge_api.py')),
    (Path('/home/hermes/jeff2/bridge/alfred_client_pr01_staged.py'), Path('/home/hermes/jeff2/bridge/alfred_client.py')),
    (Path('/home/hermes/jeff2/bridge/self_healing_engine_pr01_staged.py'), Path('/home/hermes/jeff2/bridge/self_healing_engine.py')),
    (Path('/opt/hermes/antigravity_telegram_bot_hybrid.py.pr01-staged.py'), Path('/opt/hermes/antigravity_telegram_bot_hybrid.py')),
    (Path('/opt/hermes/telegram_claude_bot.py.pr01-staged.py'), Path('/opt/hermes/telegram_claude_bot.py')),
    (Path('/home/hermes/.hermes/scripts/alfred_tool.py.pr01-staged.py'), Path('/home/hermes/.hermes/scripts/alfred_tool.py')),
    (Path('/home/hermes/jeff-github-repo/scripts/alfred_tool.py.pr01-staged.py'), Path('/home/hermes/jeff-github-repo/scripts/alfred_tool.py')),
)
for candidate, active in staged:
    if not candidate.is_file() or not active.is_file():
        raise SystemExit(f'Missing staged or active file: {active}')
    py_compile.compile(str(candidate), doraise=True)
    if not (backup / active.relative_to('/')).is_file():
        raise SystemExit(f'Missing backup for {active}')

key_file = Path('/home/hermes/jeff-bridge.env.pr01-staged')
service_file = Path('/home/hermes/jeff-bridge.service.pr01-staged')
if not key_file.is_file() or not service_file.is_file():
    raise SystemExit('Missing staged service configuration')
subprocess.run(['sudo', 'install', '-o', 'root', '-g', 'hermes', '-m', '0640',
                str(key_file), '/etc/jeff-bridge.env'], check=True)
subprocess.run(['sudo', 'install', '-o', 'root', '-g', 'root', '-m', '0644',
                str(service_file), '/etc/systemd/system/jeff-bridge.service'], check=True)
for unit in ('antigravity-telegram-bot.service', 'telegram-claude-bot.service'):
    directory = Path('/etc/systemd/system') / (unit + '.d')
    subprocess.run(['sudo', 'install', '-d', '-m', '0755', str(directory)], check=True)
    source = Path('/home/hermes') / (unit + '.pr01.conf')
    source.write_text('[Service]\nEnvironmentFile=/etc/jeff-bridge.env\n')
    subprocess.run(['sudo', 'install', '-m', '0644', str(source),
                    str(directory / 'pr01-bridge-key.conf')], check=True)
for candidate, active in staged:
    candidate.chmod(stat.S_IMODE(active.stat().st_mode))
    os.replace(candidate, active)
subprocess.run(['sudo', 'systemctl', 'daemon-reload'], check=True)
print('remote_activation_files=', len(staged), 'services_not_restarted')
