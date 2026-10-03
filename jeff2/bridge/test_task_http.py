"""Real localhost HTTP, SQLite and TaskGuard smoke for the task contract."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from pablo.pablo_task_guard import TaskGuard


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        data = json.dumps({'status': 'ok'}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_):
        pass


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


class TaskHttpSmoke(unittest.TestCase):
    def test_real_http_sqlite_guard_and_verifier(self):
        bridge_dir = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as temporary:
            health = ThreadingHTTPServer(('127.0.0.1', 0), HealthHandler)
            thread = threading.Thread(target=health.serve_forever, daemon=True)
            thread.start()
            port = free_port()
            env = os.environ.copy()
            env.update(BRIDGE_KEY='fixture-bridge-key-long-enough',
                       TASK_WORKER_KEY='fixture-worker-key-long-enough',
                       TASK_WORKER_HEALTH_URL=f'http://127.0.0.1:{health.server_port}/health',
                       BRIDGE_DB_PATH=str(Path(temporary) / 'bridge.db'),
                       BRIDGE_HOST='127.0.0.1', BRIDGE_PORT=str(port))
            env.update(TASK_ARTIFACT_ROOT=str(Path(temporary) / 'artifacts'),
                       APPROVAL_DECISION_KEY='fixture-owner-key-long-enough', TASK_APPROVAL_OWNER='42')
            process = subprocess.Popen(
                [sys.executable, '-m', 'uvicorn', 'jeff_bridge_api:app',
                 '--host', '127.0.0.1', '--port', str(port), '--log-level', 'error'],
                cwd=bridge_dir, env=env, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
            base = f'http://127.0.0.1:{port}'

            def call(method, path, data=None, worker=False, decision=False):
                headers = {'Content-Type': 'application/json',
                           ('X-Task-Worker-Key' if worker else 'X-Bridge-Key'):
                           env['TASK_WORKER_KEY' if worker else 'BRIDGE_KEY']}
                if decision:
                    headers = {'Content-Type': 'application/json', 'X-Approval-Key': env['APPROVAL_DECISION_KEY']}
                req = Request(base + path,
                              data=json.dumps(data).encode() if data is not None else None,
                              headers=headers, method=method)
                with urlopen(req, timeout=5) as response:
                    return json.load(response)

            try:
                for _ in range(100):
                    if process.poll() is not None:
                        self.fail('Bridge stopped during startup')
                    try:
                        call('GET', '/health')
                        break
                    except URLError:
                        time.sleep(.05)
                else:
                    self.fail('Bridge did not become ready')
                health_data = call('GET', '/health')
                self.assertTrue(health_data['draft_worker_ready'])
                binding={'task_id':'canonical-smoke','action':'fixture','recipient':'local-fixture','channel':'fixture','input_digest':'1'*64}
                decision=call('POST','/decisions/request',{'source':'panel','source_id':'fixture-approval',
                              'binding':binding,'expires_at':time.time()+60})
                aid=decision['approval_id']
                owner_body={'user_id':'42','chat_id':'42','input_digest':'1'*64,'decision':'approve'}
                with self.assertRaises(HTTPError) as untrusted:
                    call('POST','/decisions/'+aid+'/decision',owner_body)
                self.assertEqual(untrusted.exception.code,401)
                call('POST','/decisions/'+aid+'/decision',owner_body,decision=True)
                claim=call('POST','/decisions/'+aid+'/claim',{'binding':binding,'worker':'fixture-worker'})
                with self.assertRaises(HTTPError) as duplicate_claim:
                    call('POST','/decisions/'+aid+'/claim',{'binding':binding,'worker':'other-worker'})
                self.assertEqual(duplicate_claim.exception.code,409)
                call('POST','/decisions/'+aid+'/complete',{'claim_id':claim['claim_id'],'worker':'fixture-worker','outcome':'fixture_only'})
                self.assertEqual(call('GET','/decisions/'+aid)['status'],'consumed')
                from pablo_approval_client import ApprovalClient
                client=ApprovalClient({'auth_token':env['BRIDGE_KEY'],
                    'approval_decision_key':env['APPROVAL_DECISION_KEY'],'jeff_bridge_api_url':base})
                executions=[]
                owner_guard=TaskGuard(Path(temporary)/'canonical-node.db',
                    {'fixture':lambda p: executions.append(p) or {'ok':True}},
                    owner='42',desktop_ready=lambda:True,approvals=client)
                pending=owner_guard.execute('fixture',{'require_approval':True,'text':'immutable fixture'},'guard-http')
                self.assertEqual(pending['status'],'APPROVAL_REQUIRED')
                self.assertEqual(owner_guard.approve(pending['approval_id'],'7','42')['status'],'REJECTED')
                self.assertFalse(executions)
                self.assertEqual(owner_guard.approve(pending['approval_id'],'42','42')['status'],'SUCCESS')
                self.assertEqual(len(executions),1)
                owner_guard.approve(pending['approval_id'],'42','42')
                restarted=TaskGuard(Path(temporary)/'canonical-node.db',{},owner='42',desktop_ready=lambda:True,approvals=client)
                self.assertEqual(restarted.execute('fixture',{'require_approval':True,'text':'immutable fixture'},'guard-http')['status'],'SUCCESS')
                self.assertEqual(len(executions),1)
                self.assertEqual(call('GET','/decisions/'+pending['approval_id'])['status'],'consumed')
                import hashlib
                self.assertEqual(health_data['loaded_source_sha256']['task_artifacts.py'],
                                 hashlib.sha256((bridge_dir / 'task_artifacts.py').read_bytes()).hexdigest())

                task_id = 'http-ping-001'
                body = {'task_id': task_id, 'source': 'smoke', 'goal': 'Check Pablo health',
                        'success_criteria': ['pablo_health_ok'], 'risk_level': 'low',
                        'side_effect_class': 'none', 'approval_required': False,
                        'assigned_worker': 'fixture-pablo'}
                self.assertEqual(call('POST', '/tasks', body)['status'], 'received')
                self.assertEqual(call('POST', '/tasks', body)['task_id'], task_id)
                with self.assertRaises(HTTPError) as conflict:
                    call('POST', '/tasks', dict(body, goal='Different goal'))
                self.assertEqual(conflict.exception.code, 409)

                for route, actor in [('plan', 'jeff'), ('queue', 'jeff')]:
                    call('POST', f'/tasks/{task_id}/{route}', {'actor': actor})
                with self.assertRaises(HTTPError) as missing_worker_key:
                    call('POST', f'/tasks/{task_id}/claim', {'worker': 'fixture-pablo'})
                self.assertEqual(missing_worker_key.exception.code, 401)
                self.assertEqual(call('POST', f'/tasks/{task_id}/claim',
                                      {'worker': 'fixture-pablo'}, worker=True)['attempt'], 1)
                with self.assertRaises(HTTPError) as duplicate:
                    call('POST', f'/tasks/{task_id}/claim',
                         {'worker': 'another-worker'}, worker=True)
                self.assertEqual(duplicate.exception.code, 409)
                call('POST', f'/tasks/{task_id}/start', {'worker': 'fixture-pablo'}, worker=True)

                guard = TaskGuard(Path(temporary) / 'guard.db',
                                  {'ping': lambda _: {'ok': True, 'result': {'message': 'pong'}}},
                                  owner='fixture-owner', desktop_ready=lambda: True)
                execution = guard.execute('ping', {}, request_id=task_id)
                self.assertEqual(execution['status'], 'SUCCESS')
                call('POST', f'/tasks/{task_id}/finish',
                     {'worker': 'fixture-pablo', 'execution': execution}, worker=True)
                result = call('POST', f'/tasks/{task_id}/verify', {})
                self.assertEqual(result['status'], 'verified')
                self.assertTrue(result['verification_result']['execution_ok'])
                self.assertTrue(result['verification_result']['outcome_ok'])
                self.assertEqual([e['to_status'] for e in call('GET', f'/tasks/{task_id}/events')],
                                 ['received', 'planned', 'queued', 'claimed', 'running',
                                  'verifying', 'verified'])
                self.assertEqual([e['kind'] for e in call('GET', f'/tasks/{task_id}/evidence')],
                                 ['execution', 'outcome'])
                self.assertEqual(len(call('GET', f'/tasks/{task_id}/rejections')), 1)
                self.assertEqual(call('GET', f'/tasks/{task_id}')['status'], 'verified')

                legacy = call('POST', '/alfred/task',
                              {'task_id': 'legacy-ping-001', 'type': 'PING', 'payload': {}})
                self.assertEqual(legacy['status'], 'queued')
                self.assertFalse(call('GET', '/alfred/task/legacy-ping-001')['ok'])
                with self.assertRaises(HTTPError) as new_against_legacy:
                    call('POST', '/tasks', dict(body, task_id='legacy-ping-001'))
                self.assertEqual(new_against_legacy.exception.code, 409)
                with self.assertRaises(HTTPError) as legacy_against_new:
                    call('POST', '/alfred/task',
                         {'task_id': task_id, 'type': 'PING', 'payload': {}})
                self.assertEqual(legacy_against_new.exception.code, 409)

                draft = dict(body, task_id='http-draft', source='panel', assigned_worker='jeff-server',
                             goal='Save researched draft', approval_required=True,
                             success_criteria=['artifact_sha256_matches'],
                             steps=[{'name': 'message', 'content': 'Personal draft — never sent', 'format': 'md'}])
                call('POST', '/tasks', draft)
                call('POST', '/tasks/http-draft/plan', {'actor': 'panel'})
                call('POST', '/tasks/http-draft/queue', {'actor': 'panel'})
                approval = call('POST', '/tasks/http-draft/approval')
                self.assertEqual(call('GET', '/approvals/queue')[0]['approval_id'], approval['approval_id'])
                decision_body = {'user_id': '42', 'chat_id': '42', 'input_digest': approval['input_digest'], 'decision': 'approve'}
                path = '/approvals/' + approval['approval_id'] + '/decision'
                with self.assertRaises(HTTPError) as agent_decision:
                    call('POST', path, decision_body)
                self.assertEqual(agent_decision.exception.code, 401)
                with self.assertRaises(HTTPError) as wrong_owner:
                    call('POST', path, dict(decision_body, user_id='7'), decision=True)
                self.assertEqual(wrong_owner.exception.code, 409)
                call('POST', path, decision_body, decision=True)
                for _ in range(100):
                    saved = call('GET', '/tasks/http-draft')
                    if saved['status'] == 'verified': break
                    time.sleep(.05)
                self.assertEqual(saved['status'], 'verified')
                self.assertFalse(saved['final_result']['delivered'])
                self.assertEqual(call('GET', '/tasks/http-draft/steps')[0]['status'], 'verified')
                artifact_url = base + '/tasks/http-draft/artifacts/message'
                with urlopen(Request(artifact_url, headers={'X-Bridge-Key': env['BRIDGE_KEY']}), timeout=5) as response:
                    self.assertEqual(response.read().decode(), draft['steps'][0]['content'])
                    self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
                with self.assertRaises(HTTPError) as unauthenticated:
                    urlopen(artifact_url, timeout=5)
                self.assertEqual(unauthenticated.exception.code, 401)
                next(Path(env['TASK_ARTIFACT_ROOT']).rglob('message.md')).write_text('altered')
                with self.assertRaises(HTTPError) as changed:
                    urlopen(Request(artifact_url, headers={'X-Bridge-Key': env['BRIDGE_KEY']}), timeout=5)
                self.assertEqual(changed.exception.code, 409)
            finally:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
                health.shutdown()
                health.server_close()


if __name__ == '__main__':
    unittest.main()
