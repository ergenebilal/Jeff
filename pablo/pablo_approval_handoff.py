"""Apply a Jeff decision through the local, single-use Pablo TaskGuard."""

import json


def apply_approval_decision(guard, decision, worker_id, sender):
    rid = decision.get('task_id')
    approval_id = decision.get('approval_id')
    if (not rid or not approval_id or decision.get('worker_id') != worker_id
            or decision.get('decision') not in ('approve', 'reject')
            or not decision.get('digest') or not decision.get('type')
            or not isinstance(decision.get('attempt'), int)
            or decision['attempt'] < 1
            or not guard.approval_matches(rid, approval_id)):
        return False
    current = guard.get(rid)
    if current['status'] == 'APPROVAL_REQUIRED':
        result = guard.approve(approval_id, decision.get('actor_id'), decision.get('chat_id'),
                               reject=decision['decision'] == 'reject')
        if result['status'] == 'REJECTED' and guard.get(rid)['status'] == 'APPROVAL_REQUIRED':
            return False
    elif current['status'] in ('SUCCESS', 'ERROR', 'BLOCKED', 'REJECTED'):
        result = current
    else:
        return False
    payload = dict(result, type=decision['type'], result=json.dumps(result),
                   digest=decision['digest'], worker_id=worker_id,
                   attempt=decision['attempt'])
    guard.queue_result(payload)
    guard.flush_results(sender)
    return True
