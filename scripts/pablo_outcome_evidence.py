#!/usr/bin/env python3
"""Bind a dated receipt or authenticated current observation to an explicit criterion.

No action submission, reconciliation, retry, delivery or memory write.
The default reads a dated receipt; --current independently observes existing draft bytes.
"""
import argparse
import json
import math
import os
import re
import sys
import time
from urllib.request import Request, urlopen
try:
    from .pablo_dispatch import bridge_key
except ImportError:
    from pablo_dispatch import bridge_key

MAX_RECEIPT_BYTES = 262144
CURRENT_FIELDS = {
    'schema_version', 'request_id', 'status', 'method', 'observed_at', 'input_digest',
    'expected_sha256', 'expected_bytes', 'observed_sha256', 'observed_bytes',
    'file_bytes_matched_at_observation', 'scope', 'read_only', 'journal_status_updated',
    'execution_authorized', 'reexecution_authorized', 'customer_delivery_verified',
    'semantic_quality_verified', 'reason'}


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    def invalid_constant(_):
        raise ValueError('Nonfinite JSON number')
    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid_constant)


def valid_id(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9_-]{1,128}', value) is not None


def valid_sha(value):
    return isinstance(value, str) and re.fullmatch(r'[a-f0-9]{64}', value) is not None


def valid_bytes(value):
    return type(value) is int and 0 < value <= 500000


def evidence_view(receipt, *, task_id, input_digest, expected_sha256, expected_bytes,
                  execution_state, now=None):
    """Pure projection. Only load_record supplies an authenticated receipt in the CLI.

    Expected binding comes from the requested job, never copied from the receipt.
    The supported acceptance criterion is ONLY those private draft bytes at the
    recorded observation. Semantic quality and customer delivery are outside it.
    """
    if (not valid_id(task_id) or not valid_sha(input_digest) or not valid_sha(expected_sha256)
            or not valid_bytes(expected_bytes) or execution_state not in ('proposed', 'recorded', 'unknown')):
        raise ValueError('Invalid task criterion')
    now = time.time() if now is None else now
    if type(now) not in (int, float) or not math.isfinite(now) or now <= 0:
        raise ValueError('Invalid observation clock')
    view = {'schema_version': 1, 'requested_task_id': task_id,
            'acceptance_scope': 'private_draft_bytes_at_recorded_observation',
            'execution_state': execution_state, 'new_task_outcome': 'unknown',
            'task_binding_matched': False, 'observed_outcome_verified': False,
            'current_file_outcome_verified': False, 'semantic_quality_verified': False,
            'customer_delivery_verified': False, 'execution_authorized': False,
            'reexecution_authorized': False, 'read_only': True, 'fresh_file_read': False,
            'historical_measurement': None, 'reason': 'No usable independent outcome receipt',
            'minimal_check': 'Read the existing task binding and independently observe its file; do not replay'}
    if not isinstance(receipt, dict):
        return view
    proof = receipt.get('outcome_evidence')
    if isinstance(proof, dict):
        observed_at = proof.get('observed_at')
        dated = (type(observed_at) in (int, float) and math.isfinite(observed_at)
                 and 0 < observed_at <= now)
        # Unsupported plan/GUI/process receipts cannot borrow a draft's acceptance.
        independent = (proof.get('method') == 'independent_file_read'
                       and receipt.get('request_id') == proof.get('request_id')
                       and receipt.get('task_id', receipt.get('request_id')) == receipt.get('request_id')
                       and valid_id(proof.get('request_id')) and valid_sha(proof.get('input_digest'))
                       and valid_sha(proof.get('expected_sha256')) and valid_sha(proof.get('observed_sha256'))
                       and valid_bytes(proof.get('expected_bytes')) and valid_bytes(proof.get('observed_bytes'))
                       and dated)
        matches = bool(independent and proof['expected_sha256'] == proof['observed_sha256']
                       and proof['expected_bytes'] == proof['observed_bytes'])
        if independent:
            view['historical_measurement'] = {
                'request_id': proof['request_id'], 'input_digest': proof['input_digest'],
                'method': 'independent_file_read', 'observed_at': observed_at,
                'file_bytes_matched_at_observation': matches,
                'current_file_outcome_verified': False}
        bound = bool(independent and receipt.get('request_id') == task_id == proof['request_id']
                     and proof['input_digest'] == input_digest
                     and proof['expected_sha256'] == expected_sha256
                     and proof['expected_bytes'] == expected_bytes)
        view['task_binding_matched'] = bound
    else:
        matches = bound = False
    if execution_state == 'proposed':
        view.update(new_task_outcome='not_run', reason='Proposed job has no execution acceptance; historical measurements stay dated')
    elif execution_state == 'unknown' or receipt.get('status') in ('OUTCOME_UNKNOWN', 'IN_PROGRESS'):
        view['reason'] = 'Execution outcome remains unknown; receipt inspection does not authorize replay'
    elif view['historical_measurement'] is not None and not bound:
        view.update(new_task_outcome='binding_mismatch', reason='Receipt task, input or byte criterion differs from the requested job')
    elif bound and not matches:
        view.update(new_task_outcome='mismatch', reason='Independent recorded bytes differ from the expected draft')
    elif (bound and matches and receipt.get('status') == 'SUCCESS'
          and proof.get('status') == 'matched' and receipt.get('outcome_verified') is True
          and receipt.get('completion_authority', True) is True
          and isinstance(receipt.get('result'), dict) and receipt['result'].get('delivered') is False):
        view.update(new_task_outcome='matched_at_observation', observed_outcome_verified=True,
                    reason='Exact job/input/byte criterion matched at the dated independent observation; current file and delivery remain unverified')
    return view


def current_evidence_view(observation, *, task_id, input_digest, expected_sha256,
                          expected_bytes, execution_state, now=None):
    """Validate current authenticated file evidence against an independent criterion.

    A match is only the file bytes at the stated instant. Unknown action results
    stay unknown; content quality, delivery and permission do not follow a match.
    """
    now = time.time() if now is None else now
    view = evidence_view(None, task_id=task_id, input_digest=input_digest,
                         expected_sha256=expected_sha256, expected_bytes=expected_bytes,
                         execution_state=execution_state, now=now)
    view.update(acceptance_scope='private_draft_bytes_at_this_observation',
                current_observation=None, execution_outcome_verified=False,
                reason='No usable current independent observation')
    if execution_state == 'proposed':
        view.update(new_task_outcome='not_run', reason='Proposed job has no execution result')
        return view
    if not isinstance(observation, dict) or set(observation) != CURRENT_FIELDS:
        return view
    if (type(observation['schema_version']) is not int or observation['schema_version'] != 1
            or not valid_id(observation['request_id'])
            or observation['method'] != 'independent_current_file_read'
            or observation['scope'] != 'private_draft_bytes_at_this_observation'
            or observation['read_only'] is not True
            or any(observation[k] is not False for k in (
                'journal_status_updated', 'execution_authorized', 'reexecution_authorized',
                'customer_delivery_verified', 'semantic_quality_verified'))):
        return view
    status = observation['status']
    if status not in ('matched', 'mismatch', 'unavailable', 'deferred', 'unsupported'):
        return view
    if status not in ('matched', 'mismatch'):
        view['reason'] = {'unavailable': 'Current file observation unavailable',
                          'deferred': 'Writer still active; observe later without replay',
                          'unsupported': 'Only private draft bytes can be observed'}[status]
        return view
    observed_at = observation['observed_at']
    if (type(observed_at) not in (int, float) or not math.isfinite(observed_at)
            or not 0 < observed_at <= now or now - observed_at > 60
            or not all(valid_sha(observation[k]) for k in (
                'input_digest', 'expected_sha256', 'observed_sha256'))
            or not valid_bytes(observation['expected_bytes'])
            or type(observation['observed_bytes']) is not int
            or not 0 <= observation['observed_bytes'] <= 500000):
        return view
    matched = (observation['observed_sha256'] == observation['expected_sha256']
               and observation['observed_bytes'] == observation['expected_bytes'])
    if (observation['file_bytes_matched_at_observation'] is not matched
            or (status == 'matched') != matched):
        return view
    bound = (observation['request_id'] == task_id and observation['input_digest'] == input_digest
             and observation['expected_sha256'] == expected_sha256
             and observation['expected_bytes'] == expected_bytes)
    if not bound:
        view.update(new_task_outcome='binding_mismatch', reason='Current observation belongs to a different task/input/criterion')
        return view
    view.update(task_binding_matched=True, fresh_file_read=True,
                current_observation={k: observation[k] for k in (
                    'request_id', 'input_digest', 'method', 'observed_at',
                    'expected_sha256', 'expected_bytes', 'observed_sha256', 'observed_bytes')},
                observed_outcome_verified=matched, current_file_outcome_verified=matched,
                new_task_outcome='unknown' if execution_state == 'unknown' else (
                    'matched_at_observation' if matched else 'mismatch'),
                reason='Current private file bytes matched at the observation; action result and delivery remain separate'
                       if matched else 'Current private file bytes differ from the criterion')
    return view


def _load_authenticated(record_id, suffix=''):
    if not valid_id(record_id):
        raise ValueError('Invalid record id')
    key = bridge_key()
    if not key:
        raise ValueError('Missing bridge authentication')
    host = os.environ.get('ALFRED_HOST', '100.89.26.86')
    req = Request('http://' + host + ':7788/tasks/' + record_id + suffix,
                  headers={'X-Bridge-Key': key}, method='GET')
    with urlopen(req, timeout=10) as response:
        raw = response.read(MAX_RECEIPT_BYTES + 1)
    if len(raw) > MAX_RECEIPT_BYTES:
        raise ValueError('Receipt exceeds bound')
    receipt = strict_json(raw)
    if not isinstance(receipt, dict) or receipt.get('request_id') != record_id:
        raise ValueError('Receipt identity mismatch')
    return receipt


def load_record(record_id):
    return _load_authenticated(record_id)


def load_current_observation(record_id):
    return _load_authenticated(record_id, '/observation')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task-id', required=True)
    parser.add_argument('--input-digest', required=True)
    parser.add_argument('--expected-sha256', required=True)
    parser.add_argument('--expected-bytes', required=True, type=int)
    parser.add_argument('--execution-state', choices=('proposed', 'recorded', 'unknown'), required=True)
    parser.add_argument('--record-task-id', help='Optional historical receipt; never changes the requested task binding')
    parser.add_argument('--current', action='store_true', help='Read current private file bytes through the authenticated node')
    args = parser.parse_args(argv)
    criteria = dict(task_id=args.task_id, input_digest=args.input_digest,
                    expected_sha256=args.expected_sha256, expected_bytes=args.expected_bytes,
                    execution_state=args.execution_state)
    try:
        # Validate BEFORE any transport. Unknown binding must not be invented from a receipt.
        evidence_view(None, **criteria)
        if args.current:
            observation = None if args.execution_state == 'proposed' else load_current_observation(args.record_task_id or args.task_id)
            view = current_evidence_view(observation, **criteria)
        else:
            receipt = load_record(args.record_task_id or args.task_id)
            view = evidence_view(receipt, **criteria)
    except (OSError, ValueError, TypeError, RecursionError):
        print('Göreve bağlı sonuç kanıtı okunamadı; iş tekrarlanmadı.', file=sys.stderr)
        return 1
    print(json.dumps(view, ensure_ascii=False, indent=2, allow_nan=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
