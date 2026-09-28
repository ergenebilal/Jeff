"""Task evidence is captured by execution code, never accepted from model prose."""
import hashlib
import json
import os
import tempfile
from pathlib import Path


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def record(task, tool, args, output, rejected=False):
    signature = hashlib.sha256(json.dumps([tool, args], sort_keys=True).encode()).hexdigest()
    eid = f'{task.task_id}:e{len(task.evidence) + 1}'
    success = '[TOOL_RESULT: SUCCESS]' in output and not rejected
    item = dict(id=eid, tool=tool, signature=signature, ok=success, raw=output[:6000])
    task.evidence.append(item)
    task.obligations[signature] = item
    if success:
        task.completed_steps.append(tool)
    return eid


def seal(task, evidence_ids):
    if task is None:
        return False, 'No active task'
    if not isinstance(evidence_ids, list) or not evidence_ids:
        return False, 'Execution evidence IDs required; prose is not proof'
    lookup = {e['id']: e for e in task.evidence}
    if any(i not in lookup or not lookup[i]['ok'] for i in evidence_ids):
        return False, 'Missing or failed evidence'
    if any(not e['ok'] for e in task.obligations.values()):
        return False, 'Unresolved failed or pending steps'
    if task.coding_jobs and any(j.get('status') != 'verified' for j in task.coding_jobs.values()):
        return False, 'Coding jobs have not passed their declared tests'
    return True, '\n'.join(lookup[i]['raw'] for i in evidence_ids)
