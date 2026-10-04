"""Daily private Windows recovery copy; SSH verification, no workers or messages."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time
import urllib.request
import uuid
import zipfile

from scripts.pablo_drift_monitor import LOADED

REMOTE_ROOT='/home/hermes/jeff-artifacts/pablo-recovery'
REMOTE_REPORT='/home/hermes/jeff-artifacts/pablo-recovery-status.json'
SSH=['ssh','-o','BatchMode=yes','-o','ClearAllForwardings=yes','-o','ConnectTimeout=15','hermes']


def remote(script):
    result=subprocess.run(SSH+['/home/hermes/.venv/bin/python -c '+shlex.quote(script)],capture_output=True,text=True,timeout=120)
    if result.returncode:raise RuntimeError('Private recovery transport or verification unavailable')
    return json.loads(result.stdout) if result.stdout.strip() else None


def check_runtime(manifest,ping):
    if ping.get('ok') is not True or ping.get('result')!='pong':raise ValueError('Runtime unavailable')
    loaded=ping.get('loaded_source_sha256')
    if not isinstance(loaded,dict) or set(loaded)!=set(LOADED):raise ValueError('Runtime coverage missing')
    if manifest['source_release']!=ping.get('source_commit'):raise ValueError('Release changed during snapshot')
    return loaded


def report_ok(data,now,expected):
    if data.get('version')!=1 or data.get('ok') is not True or data.get('remote_manifest_verified') is not True:return False
    ts=data.get('verified_at')
    if type(ts) not in (int,float) or not math.isfinite(ts) or not 0<=now-ts<=30*3600:return False
    return data.get('loaded_source_sha256')==expected and set(expected)==set(LOADED)


def read_report(path,source='/home/hermes/jeff_repo/pablo',now=None):
    try:
        expected={n:hashlib.sha256((Path(source)/n).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for n in LOADED}
        good=report_ok(json.loads(Path(path).read_text()),time.time() if now is None else now,expected)
        return good,('son ozel Windows kurtarma kopyasi dogrulandi ve kaynakla uyumlu' if good else 'Windows kurtarma kopyasi eski, uyumsuz veya dogrulanmadi')
    except Exception:return False,'Windows kurtarma kopyasi bilinmiyor'


VERIFY_REMOTE=r'''
from pathlib import Path,PurePosixPath
import hashlib,json,zipfile,sys,shutil,stat,os,time
base=Path(BASE);archive=base/'windows-snapshot.zip'
archive.chmod(0o600)
with archive.open('rb') as handle:assert hashlib.file_digest(handle,'sha256').hexdigest()==EXPECTED
target=base/'snapshot';target.mkdir(mode=0o700)
seen=set();total=0
with zipfile.ZipFile(archive) as bundle:
 assert len(bundle.infolist())<=10000
 for entry in bundle.infolist():
  path=PurePosixPath(entry.filename);total+=entry.file_size
  assert total<=2*1024**3 and entry.file_size<=512*1024**2
  assert not path.is_absolute() and '..' not in path.parts and '\\' not in entry.filename and ':' not in entry.filename
  assert entry.filename not in seen and not entry.is_dir() and not stat.S_ISLNK(entry.external_attr>>16)
  seen.add(entry.filename);dest=target.joinpath(*path.parts)
  assert dest.resolve().is_relative_to(target.resolve())
  dest.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
  current=dest.parent
  while current!=target:current.chmod(0o700);current=current.parent
  with bundle.open(entry) as source,dest.open('xb') as output:shutil.copyfileobj(source,output)
  dest.chmod(0o600)
sys.path.insert(0,'/home/hermes/jeff_repo/pablo')
from pablo_recovery import validate
manifest=validate(target)
assert manifest['source_release']==REPORT['source_release']
assert all(p.stat().st_mode&0o077==0 for p in [base]+list(base.rglob('*')))
REPORT.update(remote_manifest_verified=True,verified_at=time.time(),remote_files=len(manifest['entries']),ok=True)
status=Path('/home/hermes/jeff-artifacts/pablo-recovery-status.json')
pending=status.with_name(status.name+'.'+base.name);pending.write_text(json.dumps(REPORT,indent=2));pending.chmod(0o600);os.replace(pending,status)
print(json.dumps(REPORT))
'''


def run(live,storage,report):
    live=Path(live);storage=Path(storage);report=Path(report)
    public={'version':1,'ok':False,'observed_at':time.time(),'notification_policy':'dashboard_only','workers_started':False}
    try:
        # Import only the already installed private-copy helper, never Node.
        sys.path.insert(0,str(live));from pablo_recovery import snapshot,validate,private_directory,digest
        if not storage.exists():private_directory(storage)
        if storage.is_symlink():raise ValueError('Redirected private storage')
        name=time.strftime('%Y%m%dT%H%M%SZ',time.gmtime())+'-'+uuid.uuid4().hex
        assert re.fullmatch(r'\d{8}T\d{6}Z-[a-f0-9]{32}',name)
        with urllib.request.urlopen('http://127.0.0.1:7788/ping',timeout=8) as response:before=json.load(response)
        dest=storage/name;snapshot(live,dest);manifest=validate(dest)
        loaded=check_runtime(manifest,before)
        for source,expected in loaded.items():
            if hashlib.sha256((dest/'files'/source).read_bytes().replace(b'\r\n',b'\n')).hexdigest()!=expected:raise ValueError('Snapshot differs from loaded runtime')
        with urllib.request.urlopen('http://127.0.0.1:7788/ping',timeout=8) as response:after=json.load(response)
        if after.get('process_started_at')!=before.get('process_started_at') or check_runtime(manifest,after)!=loaded:raise ValueError('Runtime changed during snapshot')
        archive=dest/'windows-snapshot.zip'
        with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as bundle:
            for member in ['manifest.json']+[e['path'] for e in manifest['entries']]:bundle.write(dest/member,arcname=member)
        if sys.platform!='win32':archive.chmod(0o600)
        public.update(source_release=manifest['source_release'],loaded_source_sha256=loaded,archive_sha256=digest(archive),archive_bytes=archive.stat().st_size,
                      cross_database_atomic_snapshot=False,private_settings_in_archive=True)
        base=REMOTE_ROOT+'/'+name
        prepare='from pathlib import Path;import os;os.umask(0o077);root=Path('+repr(REMOTE_ROOT)+');assert root.is_dir() and not root.is_symlink();root.chmod(0o700);(root/'+repr(name)+').mkdir(mode=0o700)'
        remote(prepare)
        transfer=subprocess.run(['scp','-o','BatchMode=yes','-o','ClearAllForwardings=yes','-o','ConnectTimeout=15',str(archive),'hermes:'+base+'/windows-snapshot.zip'],capture_output=True,timeout=120)
        if transfer.returncode:raise RuntimeError('Private archive transport failed')
        code='BASE='+repr(base)+'\nEXPECTED='+repr(public['archive_sha256'])+'\nREPORT='+repr(public)+'\n'+VERIFY_REMOTE
        public=remote(code)
        if public.get('ok') is not True:raise RuntimeError('No verification receipt')
    except Exception as exc:
        public.update(ok=False,failure_class=type(exc).__name__)
        # Report failure without secrets. Preserve all prior valid archives.
        try:
            remote('from pathlib import Path;import json,os;data='+repr(public)+';p=Path('+repr(REMOTE_REPORT)+');t=p.with_suffix(".failure-pending");t.write_text(json.dumps(data,indent=2));t.chmod(0o600);os.replace(t,p)')
        except Exception:public['failure_report_published']=False
    pending=report.with_suffix('.pending');pending.write_text(json.dumps(public,indent=2));pending.replace(report)
    return public


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--live',default=r'C:\CyberGene\HermesNode');ap.add_argument('--storage',required=True);ap.add_argument('--report',required=True)
    args=ap.parse_args(argv);result=run(args.live,args.storage,args.report);print(json.dumps(result));return 0 if result['ok'] else 1


if __name__=='__main__':raise SystemExit(main())
