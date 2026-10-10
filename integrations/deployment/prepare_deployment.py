"""Online backups and least-disruptive config changes; prints no credentials."""
from pathlib import Path
import hashlib
import json
import os
import secrets
import shutil
import sqlite3
import subprocess
import time
import yaml

root=Path('/home/hermes/jeff-surgery-20261004')
backup=root/'evidence/P11-backups';backup.mkdir(mode=0o700,exist_ok=False)
manifest={'created_at':time.time(),'files':[],'databases':[],'baseline_commit':subprocess.check_output(['git','-C','/home/hermes/jeff_repo','rev-parse','HEAD'],text=True).strip()}
for path in ['/home/hermes/.hermes/config.yaml','/home/hermes/.hermes/cron/jobs.json','/home/hermes/cybergeneos/docs/cybergeneos/server/app.py','/home/hermes/.hermes/plugins/evey/reflect/__init__.py']:
    p=Path(path);dest=backup/(hashlib.sha256(path.encode()).hexdigest()[:12]+'-'+p.name);shutil.copy2(p,dest)
    manifest['files'].append({'path':path,'backup':str(dest),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
envdata=subprocess.check_output(['sudo','-n','cat','/etc/jeff-bridge.env'])
(backup/'jeff-bridge.env').write_bytes(envdata);os.chmod(backup/'jeff-bridge.env',0o600)
manifest['files'].append({'path':'/etc/jeff-bridge.env','backup':str(backup/'jeff-bridge.env'),'sha256':hashlib.sha256(envdata).hexdigest()})
for path in ['/home/hermes/jeff2/bridge/bridge.db','/home/hermes/cybergeneos-data/cgos.db','/home/hermes/.hermes/state.db']:
    with sqlite3.connect(Path(path).as_uri()+'?mode=ro',uri=True) as source,sqlite3.connect(backup/Path(path).name) as target:
        source.backup(target);check=target.execute('PRAGMA integrity_check').fetchone()[0]
        if check!='ok':raise RuntimeError('Invalid database backup')
        manifest['databases'].append({'path':path,'backup':str(backup/Path(path).name),'integrity':check})
changed=subprocess.check_output(['git','-C',str(root),'diff','--name-only',manifest['baseline_commit']+'..HEAD'],text=True).splitlines()
for relative in changed:
    p=Path('/home/hermes/jeff_repo')/relative
    if p.exists():
        dest=backup/'repo'/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
        manifest['files'].append({'path':str(p),'backup':str(dest),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})

env={}
for line in envdata.decode().splitlines():
    if '=' in line and not line.lstrip().startswith('#'):
        k,v=line.split('=',1);env[k]=v.strip().strip('"\'')
key=env.get('APPROVAL_DECISION_KEY') or secrets.token_hex(32)
if key==env.get('BRIDGE_KEY'):raise RuntimeError('Owner key must differ from bridge key')
owner=(__import__('os').environ.get('TELEGRAM_OWNER_CHAT_ID', ''))
config={'auth_token':env['BRIDGE_KEY'],'approval_decision_key':key,'jeff_bridge_api_url':'http://100.80.122.74:7700','owner_id':owner}
secret_file=backup/'approval-gateway.json';secret_file.write_text(json.dumps(config));os.chmod(secret_file,0o600)
panel_config=Path('/home/hermes/cybergeneos-data/approval-gateway.json')
if panel_config.exists():shutil.copy2(panel_config,backup/'panel-approval-gateway.json')
panel_config.write_text(json.dumps(config));os.chmod(panel_config,0o600)
lines=envdata.decode().splitlines()
for name,value in [('APPROVAL_DECISION_KEY',key),('TASK_APPROVAL_OWNER',owner)]:
    lines=[l for l in lines if not l.startswith(name+'=')];lines.append(name+'='+value)
staged=backup/'new-bridge.env';staged.write_text('\n'.join(lines)+'\n');os.chmod(staged,0o600)
subprocess.run(['sudo','-n','install','-m','600',str(staged),'/etc/jeff-bridge.env'],check=True)

cfgpath=Path('/home/hermes/.hermes/config.yaml')
cfg=yaml.safe_load(cfgpath.read_text());plugins=cfg.setdefault('plugins',{})
enabled=plugins.setdefault('enabled',[])
if not isinstance(enabled,list):raise RuntimeError('Unexpected enabled plugins format')
if 'model-route-receipts' not in enabled:enabled.append('model-route-receipts')
cfgpath.write_text(yaml.safe_dump(cfg,allow_unicode=True,sort_keys=False));os.chmod(cfgpath,0o600)

cronpath=Path('/home/hermes/.hermes/cron/jobs.json');cron=json.loads(cronpath.read_text())
jobs=cron['jobs'] if isinstance(cron,dict) else cron
changes=[]
for job in jobs:
    if job.get('id') in ('99ed138e81b3','9b7d3d6d2ee3'):
        changes.append({'id':job['id'],'old_deliver':job.get('deliver'),'new_deliver':'local'})
        job['deliver']='local';job['failure_deliver']='local'
temp=cronpath.with_suffix('.surgery-tmp');temp.write_text(json.dumps(cron,ensure_ascii=False,indent=2));os.replace(temp,cronpath)
manifest['notification_config_changes']=changes
(root/'evidence/P11-deployment-manifest.json').write_text(json.dumps(manifest,indent=2))
print(json.dumps({'backup':str(backup),'database_integrity':[d['integrity'] for d in manifest['databases']],
 'plugins_enabled':enabled,'notification_changes':changes,'credentials_provisioned':True},ensure_ascii=False))
