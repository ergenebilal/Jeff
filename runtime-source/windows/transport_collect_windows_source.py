"""Read installed Windows code only; send a private packet, never credentials or runtime data."""
import argparse
import base64
import fnmatch
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time


def collect(root):
    root = Path(root).resolve()
    files = {}
    for path in sorted(root.glob('*.py')):
        if (path.name.startswith(('test_', '.', '_')) or any(fnmatch.fnmatch(path.name, pattern)
                for pattern in ('*_workcopy.py', 'patch_*.py', 'pablo_human_behavior.py'))):
            continue
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000:
            raise ValueError('Unsafe installed source')
        data = path.read_bytes().replace(b'\r\n', b'\n')
        compile(data, str(path), 'exec')
        files[path.name] = {'content': base64.b64encode(data).decode(),
                            'sha256': hashlib.sha256(data).hexdigest()}
    if not files or len(files) > 100:
        raise ValueError('Installed source coverage invalid')
    return {'version': 1, 'observed_at': time.time(), 'files': files}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', default=r'C:\CyberGene\HermesNode')
    parser.add_argument('--status', required=True)
    parser.add_argument('--helper', default=str(Path.home() / 'JeffJarvis-runtime' / 'scripts' / 'pablo_recovery_monitor.py'))
    args = parser.parse_args()
    status = {'version': 1, 'observed_at': time.time(), 'ok': False, 'production_modified': False}
    try:
        packet = collect(args.root)
        from pablo_runtime_readiness import inspect
        import urllib.request
        try:
            with urllib.request.urlopen('http://127.0.0.1:7788/ping', timeout=8) as response:
                ping = json.load(response)
        except Exception:
            ping = {}
        packet['runtime_health'] = inspect(args.root, ping)
        status['runtime_mode'] = packet['runtime_health']['mode']
        status['runtime_ready'] = packet['runtime_health']['runtime_ready']
        helper = Path(args.helper)
        if not helper.is_file() or helper.is_symlink():
            raise ValueError('Recovery helper missing')
        data = helper.read_bytes().replace(b'\r\n', b'\n')
        compile(data, str(helper), 'exec')
        packet['files']['recovery_pablo_recovery_monitor.py'] = {
            'content': base64.b64encode(data).decode(), 'sha256': hashlib.sha256(data).hexdigest()}
        # Include the actual installed transport and readiness reader, without settings.
        for source_name, source_path in (
                ('transport_collect_windows_source.py', Path(__file__)),
                ('transport_pablo_runtime_readiness.py', Path(__file__).with_name('pablo_runtime_readiness.py'))):
            source_data = source_path.read_bytes().replace(b'\r\n', b'\n')
            compile(source_data, str(source_path), 'exec')
            packet['files'][source_name] = {'content': base64.b64encode(source_data).decode(),
                                           'sha256': hashlib.sha256(source_data).hexdigest()}
        payload = json.dumps(packet)
        remote = "import pathlib,json,sys,os; p=pathlib.Path('/home/hermes/.local/state/jeff-github-sync/windows-source.json'); p.parent.mkdir(parents=True,exist_ok=True); d=json.load(sys.stdin); assert d['version']==1 and 0<len(d['files'])<=100; t=p.with_suffix('.tmp'); t.write_text(json.dumps(d)); t.chmod(0o600); t.replace(p); print(json.dumps({'accepted':True,'source_files':len(d['files'])}))"
        # Server code is a fixed string; no path, source bytes or user input enter shell syntax.
        command = ['ssh', '-o', 'BatchMode=yes', '-o', 'ClearAllForwardings=yes',
                   '-o', 'ConnectTimeout=15', 'hermes', '/home/hermes/.venv/bin/python',
                   '-c', "'" + remote.replace("'", "'\"'\"'") + "'"]
        result = subprocess.run(command, input=payload, capture_output=True, encoding='utf-8',
                                timeout=90, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if result.returncode:
            raise RuntimeError('Private source transport failed')
        ack = json.loads(result.stdout)
        if ack.get('accepted') is not True:
            raise RuntimeError('Private source transport unverified')
        status.update(ok=True, source_files=ack['source_files'])
    except Exception as error:
        status['failure_class'] = type(error).__name__
    path = Path(args.status)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(status, indent=2), encoding='utf-8')
    temporary.replace(path)
    print(json.dumps(status))
    return 0 if status['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
