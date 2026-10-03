from pathlib import Path
import hashlib
import json
import os
import py_compile
import runpy
import shutil
import sqlite3
import subprocess
import sys
import time
from urllib.request import urlopen

root=Path('/home/hermes/jeff-surgery-20261004');repo=Path('/home/hermes/jeff_repo')
baseline='04299067ff96630d45af41affc4914aa0bbeeba8'
if subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()!=baseline:raise RuntimeError('Main checkout advanced; revalidate before deploy')
for p in [root/'pablo/hermes_node.py',root/'pablo/pablo_task_guard.py',root/'jeff2/bridge/jeff_bridge_api.py',root/'jeff2/bridge/approval_ledger.py']:
    py_compile.compile(str(p),doraise=True)
plugin=Path('/home/hermes/.hermes/plugins/model-route-receipts')
if plugin.exists():raise RuntimeError('Receipt plugin already exists; preserve and reconcile')
panel=Path('/home/hermes/cybergeneos/docs/cybergeneos/server')
for name in ('approval_adapter.py','pablo_approval_client.py'):
    if (panel/name).exists():raise RuntimeError('Panel adapter target already exists')
units=['hermes-gateway','jeff-bridge','cybergeneos']
with sqlite3.connect('/home/hermes/.hermes/state.db') as db:
    if db.execute('SELECT count(*) FROM session_turn_leases WHERE expires_at>?',(time.time(),)).fetchone()[0]:
        raise RuntimeError('Active turn; wait for it to finish before deploying')
try:
    subprocess.run(['sudo','-n','systemctl','stop',*units],check=True)
    runpy.run_path(str(root/'integrations/deployment/prepare_deployment.py'),run_name='__main__')
    subprocess.run(['git','-C',str(repo),'merge','--ff-only','codex/jeff-surgery-20261004'],check=True,stdout=subprocess.DEVNULL)
    shutil.copy2(repo/'integrations/evey/reflect/__init__.py','/home/hermes/.hermes/plugins/evey/reflect/__init__.py')
    shutil.copytree(repo/'integrations/model-route-receipts',plugin,ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copy2(repo/'integrations/cybergeneos/approval_adapter.py',panel/'approval_adapter.py')
    shutil.copy2(repo/'pablo/pablo_approval_client.py',panel/'pablo_approval_client.py')
    sys.path.insert(0,str(repo/'integrations/cybergeneos'))
    from install_approval_adapter import patch
    source=patch((panel/'app.py').read_text());compile(source,'app.py','exec')
    temp=panel/'app.py.surgery-tmp';temp.write_text(source);os.replace(temp,panel/'app.py')
    commit=subprocess.check_output(['git','-C',str(repo),'rev-parse','HEAD'],text=True).strip()
    Path('/home/hermes/jeff-surgery-20261004/evidence/P11-release.json').write_text(json.dumps({'commit':commit,'deployed_at':time.time()}))
finally:
    subprocess.run(['sudo','-n','systemctl','start','jeff-bridge','cybergeneos','hermes-gateway'],check=True)
for _ in range(40):
    try:
        with urlopen('http://100.80.122.74:7700/health',timeout=2) as response:health=json.load(response)
        expected=hashlib.sha256((repo/'jeff2/bridge/approval_ledger.py').read_bytes()).hexdigest()
        if health.get('loaded_source_sha256',{}).get('approval_ledger.py')==expected:break
    except Exception:pass
    time.sleep(.5)
else:raise RuntimeError('Bridge did not load the new ledger')
print(json.dumps({'commit':commit,'bridge_loaded_new_ledger':True,'units':subprocess.check_output(['systemctl','show',*units,'-p','Id','-p','ActiveState','-p','MainPID'],text=True)},ensure_ascii=False))
