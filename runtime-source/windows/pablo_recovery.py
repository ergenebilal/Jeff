"""Private consistent Node snapshots and validated restore into a NEW directory.

Does not start workers, consume approvals, replay tasks or overwrite live state.
"""
import argparse
import ast
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sqlite3
import subprocess
import sys
import time

CORE = ('hermes_node.py','pablo_brain.py','pablo_task_guard.py','pablo_antigravity.py',
        'pablo_approval_client.py','pablo_approval_maintenance.py','pablo_notification_policy.py',
        'pablo_local_drafts.py','pablo_work_plans.py','marketing_telegram_gateway.py',
        'config.json','deployment.json','task-journal.sqlite3','intent_guard.sqlite3')


def digest(path):
    with Path(path).open('rb') as handle:
        return hashlib.file_digest(handle,'sha256').hexdigest()


def private_directory(path):
    path=Path(path).absolute()
    path.mkdir(mode=0o700)
    if os.name=='nt':
        # SID avoids translated account names; grant only the current user.
        who=subprocess.check_output(['whoami','/user','/fo','csv','/nh'],text=True)
        import csv
        sid=next(csv.reader([who.strip()]))[1]
        if not sid.startswith('S-1-'):raise ValueError('Cannot determine snapshot owner')
        # Numeric SIDs require '*' per the Windows icacls contract.
        result=subprocess.run(['icacls',str(path),'/inheritance:r','/grant:r','*'+sid+':(OI)(CI)F'],capture_output=True)
        if result.returncode:raise OSError('Cannot protect private snapshot')
        import win32security
        acl=win32security.GetFileSecurity(str(path),win32security.DACL_SECURITY_INFORMATION).GetSecurityDescriptorDacl()
        if acl is None:raise OSError('Private snapshot has no access boundary')
        principals={win32security.ConvertSidToStringSid(acl.GetAce(index)[2]) for index in range(acl.GetAceCount())}
        # Current owner, owner-rights, system and local administrators only.
        if not principals <= {sid,'S-1-3-4','S-1-5-18','S-1-5-32-544'}:
            raise OSError('Private snapshot has an unexpected reader')
    else:path.chmod(0o700)
    return path


def checked_file(base,relative):
    name=PurePosixPath(relative)
    if name.is_absolute() or not name.parts or any(p in ('','..','.') or ':' in p for p in name.parts) or '\\' in relative:
        raise ValueError('Unsafe recovery path')
    base=Path(base).absolute();path=base.joinpath(*name.parts)
    for part in [base]+[base.joinpath(*name.parts[:n]) for n in range(1,len(name.parts)+1)]:
        info=part.lstat()
        if part.is_symlink() or getattr(info,'st_file_attributes',0)&0x400:raise ValueError('Redirected recovery path')
    if not path.resolve().is_relative_to(base.resolve()) or not path.is_file():raise ValueError('Invalid recovery file')
    return path


def private_parent(target,root):
    target.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    if os.name!='nt':
        current=target.parent
        while current!=root:
            current.chmod(0o700);current=current.parent


def snapshot(live,destination,collect_packages=True):
    live=Path(live).absolute();started=time.time()
    for name in CORE:checked_file(live,name)
    dest=private_directory(destination);files=dest/'files';files.mkdir(mode=0o700)
    names=set(CORE)
    names.update(p.name for p in live.glob('*.py') if not p.name.startswith(('test_','patch_')) and not p.name.endswith('_workcopy.py'))
    drafts=live/'verified-drafts'
    if drafts.exists():
        for directory,children,filenames in os.walk(drafts,followlinks=False):
            for name in children:
                child=Path(directory)/name
                if child.is_symlink() or getattr(child.lstat(),'st_file_attributes',0)&0x400:raise ValueError('Redirected draft directory')
            names.update((Path(directory)/name).relative_to(live).as_posix() for name in filenames)
    entries=[]
    for name in sorted(names):
        source=checked_file(live,name);target=files/name;private_parent(target,dest)
        if name.endswith('.sqlite3'):
            conn=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True);copy=sqlite3.connect(target)
            try:conn.backup(copy)
            finally:copy.close();conn.close()
            with closing(sqlite3.connect(target)) as db:
                if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Corrupt database snapshot')
            kind='sqlite'
        else:shutil.copy2(source,target);kind='file'
        if os.name!='nt':target.chmod(0o600)
        entries.append({'path':'files/'+name,'sha256':digest(target),'bytes':target.stat().st_size,'kind':kind})
    if collect_packages:
        result=subprocess.run([sys.executable,'-m','pip','freeze','--all'],capture_output=True,text=True,timeout=45)
        if result.returncode:raise RuntimeError('Runtime package inventory unavailable')
        target=files/'runtime-packages.txt';target.write_text(result.stdout,encoding='utf-8')
        if os.name!='nt':target.chmod(0o600)
        entries.append({'path':'files/runtime-packages.txt','sha256':digest(target),'bytes':target.stat().st_size,'kind':'file'})
    manifest={'version':1,'started_at':started,'finished_at':time.time(),'python_version':sys.version.split()[0],'source_release':json.loads((files/'deployment.json').read_text(encoding='utf-8'))['commit'],'entries':entries,'workers_started':False,'cross_database_atomic_snapshot':False}
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    if os.name!='nt':(dest/'manifest.json').chmod(0o600)
    validate(dest)
    return {'snapshot':str(dest),'files':len(entries),'source_release':manifest['source_release'],'verified':True,'workers_started':False}


def validate(snapshot_dir):
    base=Path(snapshot_dir);manifest=json.loads(checked_file(base,'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('version')!=1 or not isinstance(manifest.get('entries'),list):raise ValueError('Invalid recovery manifest')
    seen=set()
    for entry in manifest['entries']:
        name=entry['path']
        if not isinstance(name,str) or not name.startswith('files/') or name in seen:raise ValueError('Invalid recovery entry')
        source=checked_file(base,name)
        if source.stat().st_size!=entry['bytes'] or digest(source)!=entry['sha256']:raise ValueError('Recovery file mismatch')
        if entry['kind']=='sqlite':
            with closing(sqlite3.connect(source.as_uri()+'?mode=ro&immutable=1',uri=True)) as db:
                if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Recovery database mismatch')
        elif entry['kind']!='file':raise ValueError('Invalid recovery kind')
        seen.add(name)
    if not {'files/'+name for name in CORE}<=seen:raise ValueError('Required recovery file missing')
    tree=ast.parse(checked_file(base,'files/hermes_node.py').read_text(encoding='utf-8'))
    needs_policy=any((isinstance(n,ast.ImportFrom) and n.module=='pablo_capability_policy') or
                     (isinstance(n,ast.Import) and any(a.name=='pablo_capability_policy' for a in n.names))
                     for n in ast.walk(tree))
    if needs_policy and 'files/pablo_capability_policy.py' not in seen:
        raise ValueError('Runtime capability policy missing')
    return manifest


def restore(snapshot_dir,destination):
    manifest=validate(snapshot_dir)  # Validate ALL sources before making any destination.
    dest=private_directory(destination)
    for entry in manifest['entries']:
        relative=entry['path'][6:];source=checked_file(snapshot_dir,entry['path']);target=dest/relative
        private_parent(target,dest);shutil.copy2(source,target)
        if os.name!='nt':target.chmod(0o600)
        if digest(target)!=entry['sha256']:raise ValueError('Restored file mismatch')
    return {'restored':str(dest),'files':len(manifest['entries']),'verified':True,'workers_started':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live',default=r'C:\CyberGene\HermesNode')
    group=parser.add_mutually_exclusive_group(required=True);group.add_argument('--snapshot');group.add_argument('--restore-from')
    parser.add_argument('--destination')
    args=parser.parse_args()
    try:
        if args.snapshot:result=snapshot(args.live,args.snapshot)
        else:
            if not args.destination:parser.error('--destination required for restore')
            result=restore(args.restore_from,args.destination)
        print(json.dumps(result));return 0
    except Exception as exc:print(json.dumps({'verified':False,'failure_class':type(exc).__name__,'workers_started':False}));return 1


if __name__=='__main__':sys.exit(main())
