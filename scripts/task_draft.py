"""Submit internal draft files and resume an idempotent task via Bridge HTTP."""
import argparse
import json
import os
import time
from pathlib import Path
from urllib.request import ProxyHandler, Request, build_opener


class DraftClient:
    def __init__(self, url, key):
        if not key:
            raise ValueError('BRIDGE_KEY is required')
        self.url, self.key = url.rstrip('/'), key
        self.opener = build_opener(ProxyHandler({}))

    def call(self, path, data=None):
        request = Request(self.url + path, headers={'X-Bridge-Key': self.key, 'Content-Type': 'application/json'},
                          data=json.dumps(data, ensure_ascii=False).encode() if data is not None else None)
        with self.opener.open(request, timeout=10) as response:
            return json.load(response)

    def submit(self, task_id, goal, steps, source='operator', approval=False):
        from urllib.parse import quote
        task = self.call('/tasks', {'task_id': task_id, 'source': source, 'goal': goal,
            'success_criteria': ['artifact_sha256_matches'], 'risk_level': 'low', 'side_effect_class': 'none',
            'approval_required': approval, 'assigned_worker': 'jeff-server', 'steps': steps})
        base = '/tasks/' + quote(task_id, safe='')
        if task['status'] == 'received': task = self.call(base + '/plan', {'actor': source})
        if task['status'] == 'planned': task = self.call(base + '/queue', {'actor': source})
        return task

    def wait(self, task_id, timeout=30):
        from urllib.parse import quote
        deadline = time.monotonic() + timeout
        while True:
            task = self.call('/tasks/' + quote(task_id, safe=''))
            if task['status'] in ('verified', 'failed', 'escalated', 'cancelled', 'waiting_approval'):
                return task
            if time.monotonic() >= deadline:
                return task  # A timeout is not a verified outcome or a new submission.
            time.sleep(.5)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default=os.environ.get('BRIDGE_URL', 'http://127.0.0.1:7700'))
    parser.add_argument('--task-id', required=True)
    parser.add_argument('--goal', required=True)
    parser.add_argument('--file', type=Path, action='append', required=True)
    parser.add_argument('--approval', action='store_true')
    args = parser.parse_args()
    steps = [{'name': p.stem, 'content': p.read_text(encoding='utf-8'), 'format': p.suffix.lstrip('.')} for p in args.file]
    client = DraftClient(args.url, os.environ.get('BRIDGE_KEY'))
    client.submit(args.task_id, args.goal, steps, approval=args.approval)
    result = client.wait(args.task_id)
    print(json.dumps({'task_id': result['task_id'], 'status': result['status'],
                      'verification_result': result['verification_result'], 'final_result': result['final_result']}, indent=2))
    return 0 if result['status'] == 'verified' else 2


if __name__ == '__main__':
    raise SystemExit(main())
