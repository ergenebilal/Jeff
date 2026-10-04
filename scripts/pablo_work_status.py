#!/usr/bin/env python3
"""Read Pablo's durable work record or reconcile file evidence without replay."""
import argparse
import json
import os
import re
import sys
import urllib.error
from urllib.request import Request, urlopen
try:
    from .pablo_dispatch import bridge_key
except ImportError:
    from pablo_dispatch import bridge_key


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task-id')
    parser.add_argument('--reconcile', action='store_true')
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--include-history', action='store_true', help='Include quiet legacy failures; they remain unverified')
    args = parser.parse_args(argv)
    if args.reconcile and not args.task_id:
        parser.error('Reconciliation requires one task-id')
    if args.task_id and not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', args.task_id):
        parser.error('Invalid task-id')
    if args.offset < 0:
        parser.error('Invalid offset')
    key = bridge_key()
    if not key:
        print('Görev bağlantısı okunamadı.', file=sys.stderr)
        return 2
    host = os.environ.get('ALFRED_HOST', '100.89.26.86')
    path = '/work/' + args.task_id if args.task_id else '/work?offset=' + str(args.offset)
    if args.include_history and not args.task_id:
        path += '&include_history=1'
    if args.reconcile:
        path += '/reconcile'
    req = Request('http://' + host + ':7788' + path,
                  data=b'{}' if args.reconcile else None,
                  headers={'X-Bridge-Key': key, 'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=10) as response:
            result = json.load(response)
    except (OSError, ValueError):
        print('İş kaydı okunamadı; işlem tekrarlanmadı.', file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result.get('status') == 'NOT_FOUND' else 0


if __name__ == '__main__':
    raise SystemExit(main())
