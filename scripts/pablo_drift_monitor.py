"""Read-only Windows source/runtime comparison. No pull, sync, restart or messages."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time
import urllib.request

from scripts.pablo_drift import python_files,INTENTIONAL_LIVE_ONLY
import fnmatch

LOADED=('hermes_node.py','pablo_brain.py','pablo_task_guard.py','pablo_antigravity.py',
        'pablo_approval_client.py','pablo_approval_maintenance.py','pablo_notification_policy.py',
        'pablo_local_drafts.py','pablo_work_plans.py','pablo_capability_policy.py',
        'pablo_outcome_observer.py','pablo_task_criterion.py')
REMOTE_CODE="""
import json,hashlib,subprocess,sys
from pathlib import Path
sys.path.insert(0,'/home/hermes/jeff_repo')
from scripts.pablo_drift import python_files
root=Path('/home/hermes/jeff_repo/pablo')
files={name:hashlib.sha256(p.read_bytes().replace(b'\\r\\n',b'\\n')).hexdigest() for name,p in python_files(root).items() if not p.name.startswith('test_')}
print(json.dumps({'commit':subprocess.check_output(['git','-C',str(root.parent),'rev-parse','HEAD'],text=True).strip(),'files':files}))
"""


def compare_sources(live,expected,ping):
    if not isinstance(expected,dict) or not isinstance(expected.get('files'),dict) or len(expected.get('commit',''))!=40:
        raise ValueError('Invalid source manifest')
    files=expected['files']
    if not set(LOADED)<=set(files):raise ValueError('Runtime source coverage missing')
    for name,digest in files.items():
        if Path(name).is_absolute() or '..' in Path(name).parts or '\\' in name or ':' in name or not name.endswith('.py'):
            raise ValueError('Unsafe source path')
        if len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):raise ValueError('Invalid source hash')
    actual={name:hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
            for name,p in python_files(live).items()
            if not p.name.startswith('test_') and not any(fnmatch.fnmatch(p.name,pat) for pat in INTENTIONAL_LIVE_ONLY)}
    changed=sorted(n for n in actual.keys()&files.keys() if actual[n]!=files[n])
    missing=sorted(files.keys()-actual.keys());extra=sorted(actual.keys()-files.keys())
    if not isinstance(ping,dict) or ping.get('ok') is not True or ping.get('result')!='pong':raise ValueError('No runtime proof')
    loaded=ping.get('loaded_source_sha256')
    if not isinstance(loaded,dict) or set(loaded)!=set(LOADED):raise ValueError('Incomplete runtime coverage')
    runtime_changed=sorted(n for n in LOADED if loaded[n]!=files[n])
    return {'ok':not(changed or missing or extra or runtime_changed),'repo_commit':expected['commit'],
            'installed_compared':len(files),'runtime_compared':len(LOADED),'changed':changed,
            'missing':missing,'extra':extra,'runtime_changed':runtime_changed,
            'intentional_private_layer_excluded':True,'notification_policy':'dashboard_only'}


def read_report(path,now=None,max_age=4500):
    now=time.time() if now is None else now
    try:
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        ts=data['observed_at']
        if type(ts) not in (int,float) or not 0<=now-ts<=max_age:return False,'kaynak kontrolu eski veya zamani bilinmiyor'
        if data.get('version')!=1 or type(data.get('ok')) is not bool:return False,'kaynak kontrolu bicimi gecersiz'
        if data['ok'] is False:return False,'kaynak uyusmazligi veya kontrol belirsiz'
        if data.get('runtime_compared')!=len(LOADED) or data.get('installed_compared',0)<len(LOADED):return False,'kaynak kontrolu kapsami eksik'
        if any(data.get(k) != [] for k in ('changed','missing','extra','runtime_changed')):return False,'kaynak kontrolu celiskili'
        return True,f"{data['installed_compared']} kurulu / {len(LOADED)} calisan kaynak eslesiyor"
    except Exception:return False,'kaynak kontrolu okunamadi'


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--live',default=r'C:\CyberGene\HermesNode')
    ap.add_argument('--report',required=True);ap.add_argument('--publish',action='store_true');args=ap.parse_args(argv)
    result={'version':1,'observed_at':time.time(),'ok':False,'notification_policy':'dashboard_only'}
    try:
        response=subprocess.run(['ssh','-o','BatchMode=yes','-o','ClearAllForwardings=yes','-o','ConnectTimeout=15','hermes','/home/hermes/.venv/bin/python -'],input=REMOTE_CODE,text=True,capture_output=True,timeout=40)
        if response.returncode:raise RuntimeError('Source unavailable')
        expected=json.loads(response.stdout)
        with urllib.request.urlopen('http://127.0.0.1:7788/ping',timeout=8) as resp:ping=json.loads(resp.read())
        result.update(compare_sources(Path(args.live),expected,ping))
    except Exception as exc:result['failure_class']=type(exc).__name__
    path=Path(args.report);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(result,indent=2),encoding='utf-8');temp.replace(path)
    if args.publish:
        try:
            publish=subprocess.run(['scp','-o','BatchMode=yes','-o','ClearAllForwardings=yes','-o','ConnectTimeout=15',str(path),'hermes:/home/hermes/jeff-artifacts/pablo-drift.json'],capture_output=True,timeout=40)
            if publish.returncode:raise RuntimeError('Report transport unavailable')
        except Exception as exc:
            print(json.dumps({'published':False,'failure_class':type(exc).__name__,'ok':False}));return 2
    print(json.dumps(result));return 0 if result['ok'] else 1


if __name__=='__main__':raise SystemExit(main())
