#!/usr/bin/env bash
# Existing cron script contract: empty stdout is quiet; no model or direct message sender.
exec /home/hermes/jeff-candidates/P157-v0.22.2/venv/bin/python -B - "$@" <<'PY'
import argparse
import asyncio
import fcntl
import hashlib
import json
import math
import os
import subprocess
import tempfile
import time
from pathlib import Path

SCHEMA = 1
MIN_CONFIRM_SECONDS = 300
MAX_GAP_SECONDS = 10800


def classify(protocol, google):
    if protocol.get('protocol_ok') is not True:
        return 'protocol_unverified'
    if google.get('passive_google_ok') is not True:
        return 'google_auth_unverified'
    # A cold MCP client can report ready/authenticated false while passive Google auth succeeds.
    return 'ok'


def transition(previous, health, now):
    previous = previous if isinstance(previous, dict) else {}
    valid_number = lambda v: type(v) in (int, float) and math.isfinite(v)
    if previous and not (previous.get('version') == SCHEMA
                         and valid_number(previous.get('checked_at'))
                         and type(previous.get('failures')) is int and 0 <= previous['failures'] <= 100000
                         and type(previous.get('notified')) is bool
                         and (previous.get('status') == 'ok' or valid_number(previous.get('first_failure_at')))):
        previous = {}
    last = previous.get('checked_at')
    if isinstance(last, (int, float)) and now <= last:
        return previous, ''
    state = {'version': SCHEMA, 'checked_at': now, 'status': health,
             'failures': 0, 'first_failure_at': None, 'notified': False}
    if health == 'ok':
        return state, ('NotebookLM bağlantısı yeniden doğrulandı.' if previous.get('notified') is True else '')
    recent = (isinstance(last, (int, float)) and 0 < now-last <= MAX_GAP_SECONDS
              and previous.get('status') not in (None, 'ok'))
    state['failures'] = previous.get('failures', 0) + 1 if recent else 1
    state['first_failure_at'] = previous.get('first_failure_at', last) if recent else now
    state['notified'] = previous.get('notified') is True if recent else False
    confirmed = (recent and now-state['first_failure_at'] >= MIN_CONFIRM_SECONDS
                 and state['failures'] >= 2)
    message = ''
    if confirmed and not state['notified']:
        state['notified'] = True
        detail = ('MCP bağlantısı yanıtı doğrulanamadı.' if health == 'protocol_unverified'
                  else 'Google oturumunun ağ üzerinden kabulü doğrulanamadı.' if health == 'google_auth_unverified'
                  else 'Sağlık kontrolünün ayarları veya sonucu okunamadı.')
        message = 'NotebookLM iki ayrı kontrolde doğrulanamadı. ' + detail + ' Otomatik yeniden başlatma yapılmadı.'
    return state, message


async def protocol_probe(entry, env):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    with tempfile.TemporaryFile(mode='w+') as error_log:
        params = StdioServerParameters(command=entry['command'], args=entry.get('args', []), env=env)
        async with stdio_client(params, errlog=error_log) as (read, write):
            async with ClientSession(read, write) as client:
                await client.initialize()
                result = await client.call_tool('server_info', {'include_account': False})
                data = getattr(result, 'structured_content', None)
                if data is None:
                    data = json.loads(next(c.text for c in result.content if getattr(c, 'type', None) == 'text'))
                error = getattr(result, 'is_error', getattr(result, 'isError', True))
                auth = data.get('auth') if isinstance(data, dict) else None
                return {'protocol_ok': error is False and isinstance(auth, dict),
                        'local_authenticated_hint': auth.get('authenticated') if isinstance(auth, dict) else None,
                        'ready_hint': data.get('ready') if isinstance(data, dict) else None}


def passive_google_probe(entry, env):
    cli = Path(entry['command']).parent / 'notebooklm'
    args = entry.get('args', [])
    profile = args[args.index('--profile')+1] if '--profile' in args else 'default'
    child_env = dict(env)
    # The CLI treats an empty inline-auth variable as explicit inline data; use the configured file.
    if not child_env.get('NOTEBOOKLM_AUTH_JSON'):
        child_env.pop('NOTEBOOKLM_AUTH_JSON', None)
    run = subprocess.run([str(cli), '--profile', profile, 'auth', 'check', '--test', '--passive', '--json'],
                         env=child_env, capture_output=True, text=True, timeout=40)
    try:
        data = json.loads(run.stdout)
    except (ValueError, TypeError):
        data = {}
    checks = data.get('checks', {}) if isinstance(data, dict) else {}
    return {'passive_google_ok': run.returncode == 0 and checks.get('token_fetch') is True}


def check():
    import yaml
    home = Path(os.environ.get('HERMES_HOME', '/home/hermes/.hermes'))
    cfg = home / 'config.yaml'
    entry = yaml.safe_load(cfg.read_bytes())['mcp_servers']['notebooklm']
    before = hashlib.sha256(json.dumps(entry, sort_keys=True).encode()).hexdigest()
    if entry.get('enabled') is False:
        return {'status': 'configuration_unverified', 'protocol_ok': None, 'passive_google_ok': None}
    env = {k: v for k, v in os.environ.items() if not k.startswith(('NOTEBOOKLM_', 'NLM_'))}
    env.update(entry.get('env', {}))
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    try:
        protocol = asyncio.run(asyncio.wait_for(protocol_probe(entry, env), timeout=35))
    except Exception:
        protocol = {'protocol_ok': False}
    try:
        google = passive_google_probe(entry, env)
    except Exception:
        google = {'passive_google_ok': False}
    current = yaml.safe_load(cfg.read_bytes())['mcp_servers']['notebooklm']
    same = hashlib.sha256(json.dumps(current, sort_keys=True).encode()).hexdigest() == before
    return {**protocol, **google, 'status': classify(protocol, google) if same else 'configuration_unverified'}


def atomic_state(path, state):
    fd, temporary = tempfile.mkstemp(prefix='.health-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            os.fchmod(stream.fileno(), 0o600)
            stream.write((json.dumps(state, sort_keys=True)+'\n').encode())
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--probe-only', action='store_true')
    args = parser.parse_args()
    if args.probe_only:
        try:
            result = check()
        except Exception:
            result = {'status': 'configuration_unverified', 'protocol_ok': None, 'passive_google_ok': None}
        print(json.dumps(result))
        return 0 if result['status'] == 'ok' else 2
    folder = Path('/home/hermes/.local/state/jeff-notebooklm-health')
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    folder.chmod(0o700)
    lock_fd = os.open(folder/'state.lock', os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW, 0o600)
    with os.fdopen(lock_fd, 'r+') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:
            return 0
        path = folder/'state.json'
        try:
            previous = json.loads(path.read_bytes()) if path.exists() else {}
        except (ValueError, OSError):
            previous = {}
        try:
            result = check()
        except Exception:
            result = {'status': 'configuration_unverified', 'protocol_ok': None, 'passive_google_ok': None}
        state, message = transition(previous, result['status'], time.time())
        state['last_probe'] = result
        atomic_state(path, state)
        # Cron owns the existing delivery route. A completed check is not a claim that health is good.
        if message:
            print(message)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
PY
