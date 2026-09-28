"""Port the PR-01 Bridge protocol to a drifted live Pablo worker.

Fails if any expected live-code anchor changed. Writes a new file; it never
overwrites the running worker or its TaskGuard implementation.
"""
import argparse
from pathlib import Path


def replace_once(source: str, old: str, new: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f'Expected exactly one live-code anchor: {old[:60]!r}')
    return source.replace(old, new, 1)


def patch(source: str) -> str:
    source = replace_once(source,
        'headers={"X-Bridge-Key": bridge_key}\n            )\n            try:',
        'headers={"X-Bridge-Key": bridge_key, "X-Worker-ID": CONFIG["node_id"]}\n            )\n            try:')
    source = replace_once(source,
        "if response.status != 200:\n            raise RuntimeError('Bridge did not acknowledge result')",
        "if response.status != 200 or json.loads(response.read().decode()).get('status') == 'quarantined':\n            raise RuntimeError('Bridge did not acknowledge result')")
    source = replace_once(source,
        'def handle_bridge_task(task: dict):',
        '''def bridge_claim_metadata(task_id):
    req = urllib.request.Request(
        f"{CONFIG['jeff_bridge_api_url']}/alfred/task/{urllib.parse.quote(task_id)}",
        headers={'X-Bridge-Key': CONFIG['auth_token']})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            claim = json.loads(response.read().decode())
    except Exception:
        return None
    if claim.get('worker_id') != CONFIG['node_id'] or claim.get('status') != 'delivered':
        return None
    return claim


def handle_bridge_task(task: dict):''')
    source = replace_once(source,
        "    result = execute_request(action, task.get('payload'), rid)\n    payload = dict(result, type=task.get('type'), result=json.dumps(result))",
        '''    params = task.get('payload')
    if isinstance(params, str):
        try:
            params = json.loads(params)
        except json.JSONDecodeError:
            params = {'raw': params}
    if not isinstance(params, dict):
        params = {'value': params}
    if task.get('reconcile_only'):
        result = task_guard().get(rid)
        if result['status'] in ('NOT_FOUND', 'IN_PROGRESS'):
            log('WARN', f'Bridge task {rid} requires manual reconciliation: {result["status"]}')
            return
    else:
        result = execute_request(action, params, rid)
    payload = dict(result, type=task.get('type'), result=json.dumps(result),
                   digest=task.get('digest'), worker_id=CONFIG['node_id'],
                   attempt=task.get('attempt'))''')
    source = replace_once(source,
        "                            task_guard().queue_result(dict(result, type='ACTION_RESULT', result=json.dumps(result)))",
        '''                            claim = bridge_claim_metadata(result['request_id'])
                            if claim:
                                task_guard().queue_result(dict(result, type=claim['type'],
                                    result=json.dumps(result), digest=claim['digest'],
                                    worker_id=claim['worker_id'], attempt=claim['attempt']))''')
    return source


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        raise SystemExit('Output must differ from source')
    original = args.source.read_bytes()
    newline = '\r\n' if b'\r\n' in original else '\n'
    staged = patch(original.decode('utf-8').replace('\r\n', '\n'))
    args.output.write_bytes(staged.replace('\n', newline).encode('utf-8'))
