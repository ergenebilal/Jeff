"""Private bounded current-provider worker. Input never appears in arguments."""
from pathlib import Path
import json,subprocess

def invoke(packet,*,expected):
    request=json.dumps(dict(packet=packet,expected=expected),ensure_ascii=False)
    if len(request)>50000:return dict(status='unavailable',provider_request_attempts=0)
    try:
        result=subprocess.run(['/usr/bin/python3.11',str(Path(__file__).with_name('advice_worker.py'))],
            input=request,capture_output=True,encoding='utf-8',timeout=50)
        if result.returncode!=0 or len(result.stdout)>60000:
            return dict(status='unavailable',provider_request_attempts=None)
        return json.loads(result.stdout)
    except Exception:return dict(status='unavailable',provider_request_attempts=None)
