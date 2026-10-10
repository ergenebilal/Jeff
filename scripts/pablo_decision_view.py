"""Read-only prototype: explicit criterion, dated evidence and current bytes stay separate.

Inputs must come from authenticated readers and independently known request criteria.
This pure projection does not authenticate supplied dictionaries or acquire expectations.
No model prose can promote its computed acceptance fields; no I/O or replay is present.
"""
from scripts.pablo_outcome_evidence import evidence_view, current_evidence_view


def decision_view(*, task_id, input_digest, expected_sha256, expected_bytes,
                  execution_state, dated_receipt=None, current_observation=None, now=None):
    criterion = dict(task_id=task_id, input_digest=input_digest,
                     expected_sha256=expected_sha256, expected_bytes=expected_bytes,
                     execution_state=execution_state)
    dated = evidence_view(dated_receipt, **criterion, now=now)
    current = current_evidence_view(current_observation, **criterion, now=now)
    # Never replace an explicit unknown execution with a matching current file.
    recorded_unknown = (isinstance(dated_receipt, dict)
                        and dated_receipt.get('request_id') == task_id
                        and dated_receipt.get('status') in ('OUTCOME_UNKNOWN', 'IN_PROGRESS'))
    if execution_state == 'proposed':
        task_outcome = 'not_run'
        explanation = 'Proposed work has no execution result.'
    elif execution_state == 'unknown' or recorded_unknown:
        task_outcome = 'unknown'
        explanation = 'Execution remains unknown; current file bytes are a separate observation.'
    elif current['fresh_file_read']:
        task_outcome = current['new_task_outcome']
        explanation = 'Bound current bytes take precedence for the file criterion at this observation.'
    elif current['new_task_outcome'] == 'binding_mismatch':
        task_outcome = 'binding_mismatch'
        explanation = 'Current evidence belongs to another task, input or byte criterion.'
    else:
        task_outcome = 'unknown'
        explanation = 'No acceptable current observation; retain dated evidence without claiming current success.'
    return {
        'schema_version': 1, 'requested_task_id': task_id,
        'acceptance_scope': 'private_draft_bytes_at_observation_only',
        'execution_state': execution_state,
        'recorded_execution_unknown': recorded_unknown,
        'new_task_outcome': task_outcome,
        'current_file_outcome_verified': current['current_file_outcome_verified'],
        'fresh_file_read': current['fresh_file_read'],
        'historical_measurement': dated['historical_measurement'],
        'dated_task_binding_matched': dated['task_binding_matched'],
        'current_task_binding_matched': current['task_binding_matched'],
        'current_observation': current['current_observation'],
        'current_evidence_result': current['new_task_outcome'],
        'reason': explanation,
        # A mismatch is an acceptance/binding failure, not invented factual conflict.
        'factual_source_conflict_assessed': False,
        'execution_outcome_verified': False,
        'semantic_quality_verified': False,
        'customer_delivery_verified': False,
        'execution_authorized': False,
        'reexecution_authorized': False,
        'read_only': True,
    }
