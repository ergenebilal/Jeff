"""Fixed private-policy launcher; accepted normal or read-only recovery, no historical replay."""
import hashlib,importlib.util,json,os
from pathlib import Path
import re,socket,subprocess,sys,time
from urllib.request import urlopen
NODE_DIR=Path('C:/CyberGene/HermesNode')
POLICY_PATH=NODE_DIR/'pablo-start-accepted.json'
READER_PATH=Path.home()/'JeffJarvis-runtime/scripts/pablo_runtime_readiness.py'
PYTHON_PATH=Path.home()/'AppData/Local/Programs/Python/Python313/python.exe'
PING_URL='http://127.0.0.1:7788/ping'
LISTENER=('127.0.0.1',7788)
SOURCE_NAMES=frozenset(('clinic_lead_hunter.py', 'cybergene_site_taxonomy.py', 'hermes_node.py', 'instagram_editorial_gate.py', 'marketing_autonomous_runner.py', 'marketing_pipeline.py', 'marketing_telegram_gateway.py', 'pablo_antigravity.py', 'pablo_approval_client.py', 'pablo_approval_maintenance.py', 'pablo_brain.py', 'pablo_browser_grounding.py', 'pablo_capability_policy.py', 'pablo_human_behavior.py', 'pablo_local_drafts.py', 'pablo_marketing_playbooks.py', 'pablo_notification_policy.py', 'pablo_os_grounding.py', 'pablo_outcome_observer.py', 'pablo_pilot_runner.py', 'pablo_read_outcome.py', 'pablo_recovery.py', 'pablo_rnd_engine.py', 'pablo_task_criterion.py', 'pablo_task_guard.py', 'pablo_work_plans.py', 'rnd_pipeline.py'))
REQUIRED_CHECKS=frozenset(('config.json','deployment.json','task-journal.sqlite3','intent_guard.sqlite3',
'configuration','journal_schema','journal_integrity','intent_schema','intent_integrity','recovery_write_lock'))
def digest(path):
 return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def unique(pairs):
 result={}
 for key,value in pairs:
  if key in result:raise ValueError('Duplicate field')
  result[key]=value
 return result
def policy():
 if POLICY_PATH.is_symlink() or not POLICY_PATH.is_file() or POLICY_PATH.stat().st_size>50000:
  raise ValueError('Missing accepted policy')
 value=json.loads(POLICY_PATH.read_text(encoding='utf-8'),object_pairs_hook=unique)
 if not isinstance(value,dict) or set(value)!={'version','launcher_sha256','reader_sha256','source_sets'} or type(value['version']) is not int or value['version']!=1:
  raise ValueError('Invalid accepted policy')
 for key in ('launcher_sha256','reader_sha256'):
  if not isinstance(value[key],str) or re.fullmatch('[a-f0-9]{64}',value[key]) is None:raise ValueError('Invalid source digest')
 if digest(__file__)!=value['launcher_sha256'] or READER_PATH.is_symlink() or digest(READER_PATH)!=value['reader_sha256']:
  raise ValueError('Launcher or reader changed')
 sets=value['source_sets']
 if not isinstance(sets,list) or not 1<=len(sets)<=2:raise ValueError('Invalid accepted source sets')
 for variant in sets:
  if not isinstance(variant,dict) or set(variant)!=SOURCE_NAMES or any(not isinstance(v,str) or re.fullmatch('[a-f0-9]{64}',v) is None for v in variant.values()):
   raise ValueError('Invalid accepted source set')
 if NODE_DIR.is_symlink() or not NODE_DIR.is_dir():raise ValueError('Invalid fixed node root')
 current={}
 for name in SOURCE_NAMES:
  path=NODE_DIR/name
  if path.is_symlink() or not path.is_file():raise ValueError('Accepted source unavailable')
  current[name]=digest(path)
 if current not in sets:raise ValueError('Installed sources outside accepted set')
 spec=importlib.util.spec_from_file_location('_pablo_fixed_start_reader',READER_PATH)
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 return module.inspect,current
def read_ping():
 try:
  with urlopen(PING_URL,timeout=2) as response:return json.load(response)
 except (OSError,ValueError):return None
def listener_present():
 try:
  with socket.socket() as probe:
   if hasattr(socket,'SO_EXCLUSIVEADDRUSE'):
    probe.setsockopt(socket.SOL_SOCKET,socket.SO_EXCLUSIVEADDRUSE,1)
   probe.bind(LISTENER)
  return False
 except OSError:return True

def allowed(health,*,running):
 checks=health.get('checks',{}) if isinstance(health,dict) else {}
 if not isinstance(checks,dict) or not REQUIRED_CHECKS<=checks.keys() or health.get('mode') not in ('normal','read_only_recovery'):return False
 if running:return health.get('runtime_ready') is True and all(v is True for v in checks.values())
 return all(v is True for k,v in checks.items() if k not in ('release','running_sources'))
CHILD_BOOT = '''
import runpy,sys
sys.path.insert(0,sys.argv[1])
node=runpy.run_path(sys.argv[1]+'/hermes_node.py')
state=node['main'].__globals__
original_mode=state['current_recovery_mode']
def read_only_mode():
 mode=original_mode()
 if mode not in ('normal','read_only_recovery'):
  raise RuntimeError('Accepted runtime mode required')
 return mode
def forbidden_worker():
 raise RuntimeError('Background work is closed in accepted startup')
state['current_recovery_mode']=read_only_mode
if original_mode()=='read_only_recovery':
 for name in ('run_bridge_worker','run_telegram_worker','run_tailscale_watchdog'):
  state[name]=forbidden_worker
read_only_mode()
state['main']()
'''

def launch():
 if not PYTHON_PATH.is_file() or PYTHON_PATH.is_symlink():raise ValueError('Pinned Windows interpreter unavailable')
 env=dict(os.environ)
 for name in ('PYTHONPATH','PYTHONHOME'):env.pop(name,None)
 return subprocess.Popen([str(PYTHON_PATH),'-I','-B','-c',CHILD_BOOT,str(NODE_DIR)],cwd=str(NODE_DIR),env=env,
  stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
  creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
def run():
 child=None;accepted=False
 try:
  inspector,expected=policy()
  ping=read_ping()
  if ping is not None:return 0 if allowed(inspector(NODE_DIR,ping),running=True) else 3
  if listener_present():return 3
  if not allowed(inspector(NODE_DIR,{}),running=False):return 3
  private_before={name:digest(NODE_DIR/name) for name in ('config.json','deployment.json')}
  child=launch();deadline=time.monotonic()+20
  while child.poll() is None and time.monotonic()<deadline:
   ping=read_ping()
   if ping is not None:
    if (allowed(inspector(NODE_DIR,ping),running=True) and {name:digest(NODE_DIR/name) for name in SOURCE_NAMES}==expected
     and all(digest(NODE_DIR/name)==v for name,v in private_before.items())):
     accepted=True;return 0
    return 3
   time.sleep(.2)
  return 3
 except Exception:return 3
 finally:
  if child is not None and not accepted and child.poll() is None:child.terminate();child.wait(timeout=10)
if __name__=='__main__':raise SystemExit(run() if len(sys.argv)==1 else 3)
