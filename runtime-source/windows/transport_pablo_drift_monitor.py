"""Read-only Windows source/runtime comparison. No pull, sync, restart or messages."""

import argparse

import hashlib

import json

from pathlib import Path

import subprocess

import sys

import time

import urllib.request



# Windows'ta ssh/scp konsol penceresi acmasin (surekli yanip sonen terminalin sebeplerinden biri).

_NO_WINDOW = getattr(subprocess, 'CREATE_NO_WINDOW', 0) if sys.platform == 'win32' else 0



from scripts.pablo_drift import python_files,INTENTIONAL_LIVE_ONLY

import fnmatch



LOADED=('hermes_node.py','pablo_brain.py','pablo_task_guard.py','pablo_antigravity.py',

        'pablo_approval_client.py','pablo_approval_maintenance.py','pablo_notification_policy.py',

        'pablo_local_drafts.py','pablo_work_plans.py','pablo_capability_policy.py',

        'pablo_outcome_observer.py','pablo_task_criterion.py','pablo_read_outcome.py')

REMOTE_CODE="\nfrom pathlib import Path\nimport json,base64,hashlib,importlib.util,subprocess,re,time\nroot=Path('/home/hermes/.local/state/jeff-github-sync')\nconfig_path=root/'config.json';state_path=root/'state.json'\nconfig_before=config_path.read_bytes();config=json.loads(config_before)\nstate_before=state_path.read_bytes();state=json.loads(state_before)\ninbox=Path(config['windows_inbox']);packet_before=inbox.read_bytes();packet=json.loads(packet_before)\nspec=importlib.util.spec_from_file_location('_readonly_current_publisher_projection','/home/hermes/.local/lib/jeff-github-sync/jeff_github_sync.py')\nif hashlib.sha256(Path(spec.origin).read_bytes()).hexdigest()!='3a295a85156454e94de74c71e398bc095878707c465f3d107284dbb1428400fa':raise RuntimeError('Publisher source changed')\npublisher=importlib.util.module_from_spec(spec);spec.loader.exec_module(publisher)\nif packet.get('version')!=1 or not isinstance(packet.get('files'),dict) or not 0<len(packet['files'])<=100:raise RuntimeError('Invalid Windows packet')\nif type(packet.get('observed_at')) not in (int,float) or not 0<=time.time()-packet['observed_at']<=4500:raise RuntimeError('Windows observation old or unavailable')\nif config.get('branch')!='codex/automatic-jeff' or config.get('mirror_repo')!='/home/hermes/.local/state/jeff-github-sync/public-mirror':raise RuntimeError('Publication reference changed')\nmirror=Path(config['mirror_repo'])\nallowed_remotes={'git@github.com:ergenebilal/Jeff.git','https://github.com/ergenebilal/Jeff.git'}\nif config.get('remote') not in allowed_remotes or subprocess.check_output(['git','-C',str(mirror),'config','--get','remote.origin.url'],text=True).strip()!=config['remote']:raise RuntimeError('Publication remote changed')\nif subprocess.check_output(['git','-C',str(mirror),'branch','--show-current'],text=True).strip()!=config['branch']:raise RuntimeError('Mirror branch changed')\nhead=subprocess.check_output(['git','-C',str(mirror),'rev-parse','HEAD'],text=True).strip()\nremote=subprocess.check_output(['git','-C',str(mirror),'ls-remote','origin','refs/heads/'+config['branch']],text=True).split()[0]\nidentifiers=[value.encode() for value in config.get('private_identifiers',[]) if len(value)>=7]\nraw={};public={};changed=[];missing=[]\nfor name,item in packet['files'].items():\n if name.startswith(('recovery_','transport_')):continue\n if re.fullmatch(r'[A-Za-z0-9_-]+\\.py',name) is None or not publisher.allowed(name) or name=='pablo_human_behavior.py':raise RuntimeError('Unsafe source inventory')\n data=base64.b64decode(item['content'],validate=True)\n if hashlib.sha256(data).hexdigest()!=item['sha256']:raise RuntimeError('Raw packet hash mismatch')\n target='runtime-source/windows/'+name\n projected=publisher.private_settings(target,publisher.public_bytes(target,data),identifiers)\n if any(value in projected for value in identifiers):raise RuntimeError('Private identity in projection')\n digest=hashlib.sha256(projected).hexdigest();raw[name]=item['sha256'];public[name]=digest\n if state['published_manifest'].get(target)!=digest:changed.append(name)\n if target not in state['published_manifest']:missing.append(name)\n blob=subprocess.run(['git','-C',str(mirror),'show',head+':'+target],capture_output=True)\n if blob.returncode or hashlib.sha256(blob.stdout).hexdigest()!=digest:changed.append(name)\nassert config_path.read_bytes()==config_before and inbox.read_bytes()==packet_before and state_path.read_bytes()==state_before,'Concurrent source metadata change'\nif changed or missing or head!=remote or state['last_success']['remote_commit']!=head:raise RuntimeError('Windows publication not confirmed')\nif not raw:raise RuntimeError('Windows source inventory empty')\nprint(json.dumps({'commit':head,'files':raw,'reference_kind':'confirmed_automatic_windows_publication',\n 'public_projection_verified':True,'collector_observed_at':packet['observed_at'],\n 'private_source_content_exported':False,'expected_sources_are_current_raw_hashes':True}))\n"




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

        response=subprocess.run(['ssh','-o','BatchMode=yes','-o','ClearAllForwardings=yes','-o','ConnectTimeout=15','hermes','/home/hermes/.venv/bin/python -'],input=REMOTE_CODE,text=True,capture_output=True,timeout=40,creationflags=_NO_WINDOW)

        if response.returncode:raise RuntimeError('Source unavailable')

        expected=json.loads(response.stdout)

        with urllib.request.urlopen('http://127.0.0.1:7788/ping',timeout=8) as resp:ping=json.loads(resp.read())

        result.update(compare_sources(Path(args.live),expected,ping))

    except Exception as exc:result['failure_class']=type(exc).__name__

    path=Path(args.report);path.parent.mkdir(parents=True,exist_ok=True)

    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(result,indent=2),encoding='utf-8');temp.replace(path)

    if args.publish:

        try:

            publish=subprocess.run(['scp','-o','BatchMode=yes','-o','ClearAllForwardings=yes','-o','ConnectTimeout=15',str(path),'hermes:/home/hermes/jeff-artifacts/pablo-drift.json'],capture_output=True,timeout=40,creationflags=_NO_WINDOW)

            if publish.returncode:raise RuntimeError('Report transport unavailable')

        except Exception as exc:

            print(json.dumps({'published':False,'failure_class':type(exc).__name__,'ok':False}));return 2

    print(json.dumps(result));return 0 if result['ok'] else 1





if __name__=='__main__':raise SystemExit(main())

