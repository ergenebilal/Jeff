#!/usr/bin/env python3
"""Ask Pablo for a bounded local draft; show its recorded file observation.

Does not send a customer message or declare the legacy Bridge task verified.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import uuid

try:
    from .pablo_dispatch import bridge_key, call
except ImportError:
    from pablo_dispatch import bridge_key, call



# P109: current node evidence is required before creating any new work.
def _p109_admission(action):
    __import__('sys').path.insert(0, '/home/hermes/.local/lib/jeff-pablo-guard')
    from pablo_readiness_gate import admission
    return admission(action)

def recorded_outcome(task_id, params, record):
    """Validate binding and evidence shape; never promote Bridge's trust level."""
    raw = record.get('result') if isinstance(record, dict) else None
    try:
        result = json.loads(raw) if isinstance(raw, str) else raw
    except (ValueError, TypeError):
        return {'task_id': task_id, 'status': 'evidence_unavailable', 'outcome_verified': False}
    if not isinstance(result, dict):
        return {'task_id': task_id, 'status': 'evidence_unavailable', 'outcome_verified': False}
    proof = result.get('outcome_evidence')
    expected_data = params['content'].encode('utf-8')
    expected_digest = hashlib.sha256(json.dumps(['local_draft', params | {'request_id': task_id}],
                                               sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    match = (record.get('task_id') == task_id and record.get('worker_id') == 'pablo-windows-node-01'
             and result.get('request_id') == task_id and result.get('status') == 'SUCCESS'
             and result.get('outcome_verified') is True and isinstance(proof, dict)
             and proof.get('method') == 'independent_file_read' and proof.get('status') == 'matched'
             and proof.get('request_id') == task_id and proof.get('input_digest') == expected_digest
             and proof.get('expected_sha256') == proof.get('observed_sha256') == hashlib.sha256(expected_data).hexdigest()
             and type(proof.get('expected_bytes')) is int and type(proof.get('observed_bytes')) is int
             and proof['expected_bytes'] == proof['observed_bytes'] == len(expected_data))
    return {'task_id': task_id, 'status': 'recorded_file_match' if match else 'needs_review',
            'outcome_verified': match, 'bridge_recorded_status': record.get('recorded_status'),
            'worker_status': result.get('status'), 'outcome_evidence': proof if isinstance(proof, dict) else None,
            'path': (result.get('result') or {}).get('path') if isinstance(result.get('result'), dict) else None,
            'delivered': False}


def main(argv=None):
    readiness = _p109_admission('local_draft')
    if readiness['admitted'] is not True:
        print(json.dumps(readiness, ensure_ascii=False)); return 3
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file', required=True, type=Path)
    parser.add_argument('--name', default='draft')
    parser.add_argument('--format', choices=('txt', 'md', 'json'), default='txt')
    parser.add_argument('--task-id', default=None)
    parser.add_argument('--wait-seconds', type=int, default=30)
    parser.add_argument('--deadline-at', type=float, help='Optional deadline as UTC Unix seconds; not an execution schedule')
    args = parser.parse_args(argv)
    if not 1 <= args.wait_seconds <= 60:
        parser.error('wait-seconds must be between 1 and 60')
    try:
        with args.file.open('rb') as file:
            data = file.read(500_001)
        if not data or len(data) > 500_000:
            raise ValueError()
        content = data.decode('utf-8')
    except (OSError, ValueError):
        print('Taslak okunamadı veya boyutu uygun değil.', file=sys.stderr)
        return 2
    params = {'name': args.name, 'format': args.format, 'content': content}
    if args.deadline_at is not None:
        import math
        if not math.isfinite(args.deadline_at) or not 0 < args.deadline_at <= 253402300799:
            parser.error('Invalid UTC deadline')
        params['deadline_at'] = args.deadline_at
    task_id = args.task_id or 'local-draft-' + uuid.uuid4().hex
    if (not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', task_id)
            or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', args.name)):
        parser.error('Invalid task-id or draft name')
    key = bridge_key()
    if not key:
        print('Görev bağlantısı okunamadı.', file=sys.stderr)
        return 2
    created = call('/alfred/task', key, {'task_id': task_id, 'type': 'local_draft', 'payload': params, 'policy': {}})
    if not isinstance(created, dict) or created.get('task_id') != task_id or '_http' in created:
        print('Görev kaydedilemedi; otomatik tekrar yapılmadı.', file=sys.stderr)
        return 1
    deadline = time.monotonic() + args.wait_seconds
    while time.monotonic() < deadline:
        record = call('/alfred/task/' + task_id + '/result', key)
        if isinstance(record, dict) and record.get('task_id') == task_id:
            outcome = recorded_outcome(task_id, params, record)
            print(json.dumps(outcome, ensure_ascii=False, indent=2))
            return 0 if outcome['outcome_verified'] else 1
        time.sleep(1)
    print(json.dumps({'task_id': task_id, 'status': 'waiting_for_result', 'outcome_verified': False}))
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
