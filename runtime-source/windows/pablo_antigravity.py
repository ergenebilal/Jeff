"""Bind opaque Antigravity execution to an approved executable and arguments."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys

ALIASES={'antigravity','run_antigravity','antigravity_task','antigravity_post'}
DESIGNER=Path(r'C:\Users\lenovo\.gemini\antigravity-ide\scratch\cybergene-post-designer\cg_post.py')

def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def binding(params):
    prompt=params.get('prompt','')
    if not isinstance(prompt,str) or not prompt.strip():
        raise ValueError('Antigravity prompt required')
    is_post=params.get('task_type','general')=='instagram_post' or any(w in prompt.lower() for w in ('post','instagram','slayt','carousel'))
    if is_post:
        arg='--next' if any(w in prompt.lower() for w in ('siradaki','sıradaki','next','plan')) else prompt
        argv=[sys.executable,str(DESIGNER),arg]
        paths=[sys.executable,str(DESIGNER)]
    else:
        executable=shutil.which('agy')
        if not executable:
            raise FileNotFoundError('Antigravity executable unavailable')
        argv=[executable,'-p',prompt]; paths=[executable]
    return {'argv':argv,'sha256':{str(p):file_digest(p) for p in paths},'task_type':'instagram_post' if is_post else 'antigravity_general'}

def prepare(params):
    params=dict(params)
    params['_antigravity_binding']=binding(params)
    return params

def execute(params):
    try:
        expected=params.get('_antigravity_binding')
        if not expected or binding(params)!=expected:
            return {'ok':False,'status':'BLOCKED','error':'Antigravity executable or arguments changed; new approval required'}
        result=subprocess.run(expected['argv'],capture_output=True,text=True,timeout=180,encoding='utf-8',
                              creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        return {'ok':result.returncode==0,'status':'EXECUTION_SUCCEEDED' if result.returncode==0 else 'ERROR',
                'verified':False,'outcome_verified':False,'delivered':False,
                'result':{'exit_code':result.returncode,'task_type':expected['task_type'],
                          'stdout':result.stdout,'stderr':result.stderr,'verified':False,'delivered':False}}
    except subprocess.TimeoutExpired:
        return {'ok':False,'status':'PENDING_VERIFICATION','verified':False,'delivered':False,
                'error':'Antigravity timeout; reconcile output before retry'}
    except Exception as exc:
        return {'ok':False,'status':'ERROR','error':type(exc).__name__,'verified':False,'delivered':False}
