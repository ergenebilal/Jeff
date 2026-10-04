#!/usr/bin/env python3
"""Submit or advance a bounded private draft plan; record an event input signal.

Person waits require the separate owner interface, never the agent key here.
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys
from urllib.request import Request,urlopen
from urllib.error import HTTPError
try:
    from .pablo_dispatch import bridge_key
except ImportError:
    from pablo_dispatch import bridge_key


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task-id',required=True)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--file',type=Path)
    mode.add_argument('--advance',action='store_true')
    mode.add_argument('--cancel',action='store_true')
    mode.add_argument('--signal',metavar='STEP')
    parser.add_argument('--key')
    parser.add_argument('--source')
    args=parser.parse_args(argv)
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',args.task_id):parser.error('Invalid task-id')
    if args.signal and not (args.key and args.source):parser.error('Signal needs key and source')
    if args.file:
        try:
            with args.file.open('rb') as file:data=file.read(2_100_001)
            if len(data)>2_100_000:raise ValueError()
            plan=json.loads(data.decode('utf-8'))
            if not isinstance(plan,dict):raise ValueError()
        except (OSError,ValueError):
            print('Plan okunamadı veya boyutu uygun değil.',file=sys.stderr);return 2
        path='/execute';body={'action':'local_draft_plan','params':plan,'request_id':args.task_id}
    elif args.signal:
        path='/work/'+args.task_id+'/signal';body={'step':args.signal,'key':args.key,'source':args.source}
    else:
        path='/work/'+args.task_id+('/cancel' if args.cancel else '/advance');body={}
    key=bridge_key()
    if not key:
        print('Görev bağlantısı okunamadı.',file=sys.stderr);return 2
    host=os.environ.get('ALFRED_HOST','100.89.26.86')
    req=Request('http://'+host+':7788'+path,data=json.dumps(body).encode(),
                headers={'X-Bridge-Key':key,'Content-Type':'application/json'})
    try:
        with urlopen(req,timeout=20) as response:result=json.load(response)
    except HTTPError as exc:
        print(json.dumps({'task_id':args.task_id,'http':exc.code,'recorded':False,'replayed':False}));return 1
    except (OSError,ValueError):
        print('Cevap alınamadı; işlem tekrarlanmadı. Görev kimliğiyle durumunu oku.',file=sys.stderr);return 1
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 1 if result.get('status') in ('ERROR','CONFLICT','RECOVERY_BLOCKED','NOT_FOUND','NEEDS_REVIEW') else 0


if __name__=='__main__':raise SystemExit(main())
