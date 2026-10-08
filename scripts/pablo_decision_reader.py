"""Authenticated read-only decision, bound to the node's original stored request.

No arbitrary expectations from model prose. Unknown criteria do not trigger file
reads. A second criterion read detects concurrent changes; unavailable transport
fails closed without retrying or replaying work. This does not prove original
request quality, owner intent, execution, delivery, or general intelligence.
"""
import argparse
import json
import time
import sys
from pathlib import Path
if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.pablo_outcome_evidence import _load_authenticated, valid_id, evidence_view
from scripts.pablo_decision_view import decision_view

FIELDS = {'schema_version', 'request_id', 'status', 'source', 'input_digest',
          'expected_sha256', 'expected_bytes', 'execution_state', 'read_only',
          'execution_authorized', 'reexecution_authorized'}


def criterion_args(value, task_id):
    if (not isinstance(value, dict) or set(value) != FIELDS
            or type(value['schema_version']) is not int or value['schema_version'] != 1
            or value['request_id'] != task_id or value['status'] != 'available'
            or value['source'] != 'stored_original_request' or value['read_only'] is not True
            or value['execution_authorized'] is not False or value['reexecution_authorized'] is not False
            or value['execution_state'] not in ('recorded', 'unknown')):
        raise ValueError('Unusable original criterion')
    args = dict(task_id=task_id, **{k: value[k] for k in (
        'input_digest', 'expected_sha256', 'expected_bytes', 'execution_state')})
    evidence_view(None, **args)
    return args


def read_decision(task_id, *, loader=None, clock=time.time):
    if not valid_id(task_id):
        raise ValueError('Invalid task identity')
    out = dict(schema_version=1, request_id=task_id, status='unavailable',
               new_task_outcome='unknown', current_file_outcome_verified=False,
               execution_outcome_verified=False, semantic_quality_verified=False,
               customer_delivery_verified=False, execution_authorized=False,
               reexecution_authorized=False, read_only=True,
               criterion_source='stored_original_request',
               goal_scope='existing_private_draft_bytes_only',
               minimal_check='Read this existing original request and its evidence later; do not replay')
    loader = _load_authenticated if loader is None else loader
    try:
        original = loader(task_id, '/criterion')
        args = criterion_args(original, task_id)
        dated = loader(task_id, '')
        current = loader(task_id, '/observation')
        if loader(task_id, '/criterion') != original:
            raise ValueError('Criterion changed during observation')
        view = decision_view(**args, dated_receipt=dated, current_observation=current, now=clock())
        out.update(view, status='observed')
        if out['current_file_outcome_verified']:
            out['minimal_check'] = 'File bytes matched only at this observation; execution, quality and delivery remain separate'
        elif out['new_task_outcome'] in ('mismatch', 'binding_mismatch'):
            out['minimal_check'] = 'Compare the original request with this mismatch; do not mark complete or replay'
    except (OSError, ValueError, TypeError, RecursionError):
        # No private response or exception text crosses this boundary.
        pass
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task-id', required=True)
    args = parser.parse_args(argv)
    try:
        result = read_decision(args.task_id)
    except ValueError:
        return 1
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))
    return 0 if result['status'] == 'observed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
