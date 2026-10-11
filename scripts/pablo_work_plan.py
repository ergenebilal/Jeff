#!/usr/bin/env python3
"""Submit a private plan once after durable original-byte capture.

Advance/cancel/signal paths retain their existing transport behavior. A receipt
is neither execution evidence nor owner approval. No private content is printed.
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError
try:
    from .pablo_dispatch import bridge_key
except ImportError:
    from pablo_dispatch import bridge_key
try:
    from .pablo_plan_receipts import DEFAULT_STORE, AlreadyCaptured, ReceiptConflict, ReceiptError, capture_original, decode_plan_input
except ImportError:
    from pablo_plan_receipts import DEFAULT_STORE, AlreadyCaptured, ReceiptConflict, ReceiptError, capture_original, decode_plan_input


_FAILURES = {'ERROR', 'CONFLICT', 'RECOVERY_BLOCKED', 'NOT_FOUND', 'NEEDS_REVIEW',
             'RECOVERY_READ_ONLY', 'RECOVERY_UNAVAILABLE'}
_SAFE_STATUSES = _FAILURES | {'SUCCESS', 'IN_PROGRESS', 'WAITING_FOR_EVENT', 'WAITING_FOR_TIME',
    'WAITING_FOR_PERSON', 'CANCELLED', 'RECOVERY_READ_ONLY', 'RECOVERY_UNAVAILABLE',
    'WAITING_FOR_APPROVAL', 'PENDING', 'QUEUED', 'UNVERIFIED'}



# Preserve the installed P109 current-node admission before any new dispatch.
def _p109_admission(action):
    __import__('sys').path.insert(0, '/home/hermes/.local/lib/jeff-pablo-guard')
    from pablo_readiness_gate import admission
    return admission(action)

def main(argv=None, *, receipt_store=DEFAULT_STORE, clock=time.time):
    try:
        readiness = _p109_admission('local_draft_plan')
    except Exception:
        readiness = None
    if not isinstance(readiness, dict) or readiness.get('admitted') is not True:
        status = readiness.get('status') if isinstance(readiness, dict) else None
        print(json.dumps({'status': status if isinstance(status, str) and status in {'RECOVERY_READ_ONLY', 'RECOVERY_UNAVAILABLE'} else 'RECOVERY_UNAVAILABLE',
                          'admitted': False, 'submission_verified': False,
                          'execution_authorized': False, 'replayed': False}))
        return 3
    # Trusted local harness injection is not a CLI/model argument.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task-id', required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--file', type=Path)
    mode.add_argument('--advance', action='store_true')
    mode.add_argument('--cancel', action='store_true')
    mode.add_argument('--signal', metavar='STEP')
    parser.add_argument('--key')
    parser.add_argument('--source')
    args = parser.parse_args(argv)
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', args.task_id):
        parser.error('Invalid task-id')
    if args.signal and not (args.key and args.source):
        parser.error('Signal needs key and source')
    if args.file:
        try:
            with args.file.open('rb') as file:
                data = file.read(2_100_001)
            if len(data) > 2_100_000:
                raise ValueError()
            plan = decode_plan_input(data)
            if not isinstance(plan, dict):
                raise ValueError()
        except (ReceiptError, OSError, ValueError, RecursionError):
            print(json.dumps({'task_id': args.task_id, 'status': 'invalid_input',
                              'submission_verified': False})); return 2
        path = '/execute'
        body = {'action': 'local_draft_plan', 'params': plan, 'request_id': args.task_id}
    elif args.signal:
        path = '/work/' + args.task_id + '/signal'
        body = {'step': args.signal, 'key': args.key, 'source': args.source}
    else:
        path = '/work/' + args.task_id + ('/cancel' if args.cancel else '/advance')
        body = {}
    key = bridge_key()
    if not key:
        print(json.dumps({'task_id': args.task_id, 'status': 'connection_unavailable',
                          'submission_verified': False})); return 2
    try:
        # Produce one bytes object. It is both durable receipt input and HTTP data.
        request_bytes = json.dumps(body, ensure_ascii=False, allow_nan=False).encode('utf-8')
        if args.file:
            capture_original(request_bytes, store=receipt_store, clock=clock)
    except (ReceiptError, OSError, ValueError, TypeError, RecursionError) as exc:
        reason = ('original_dispatch_already_captured' if isinstance(exc, AlreadyCaptured)
                  else 'receipt_conflict' if isinstance(exc, ReceiptConflict) else 'receipt_unavailable')
        print(json.dumps({'task_id': args.task_id, 'status': reason,
                          'submission_verified': False, 'replayed': False})); return 2
    host = os.environ.get('ALFRED_HOST', '100.89.26.86')
    try:
        req = Request('http://' + host + ':7788' + path, data=request_bytes,
                      headers={'X-Bridge-Key': key, 'Content-Type': 'application/json'})
        with urlopen(req, timeout=20) as response:
            result = json.load(response)
    except HTTPError as exc:
        print(json.dumps({'task_id': args.task_id, 'http': exc.code,
                          'submission_verified': False, 'replayed': False})); return 1
    except (OSError, ValueError, TypeError, RecursionError):
        print(json.dumps({'task_id': args.task_id, 'status': 'response_unavailable',
                          'submission_verified': False, 'replayed': False})); return 1
    status = result.get('status') if isinstance(result, dict) else None
    if not isinstance(status, str):
        status = None
    print(json.dumps({'task_id': args.task_id,
                      'status': status if status in _SAFE_STATUSES else 'unknown',
                      'transport_response_received': True,
                      'original_receipt_captured': bool(args.file),
                      'submission_verified': False, 'semantic_goal_verified': False,
                      'owner_approval_verified': False, 'replayed': False}))
    return 1 if status in _FAILURES or status not in _SAFE_STATUSES else 0


if __name__ == '__main__':
    raise SystemExit(main())