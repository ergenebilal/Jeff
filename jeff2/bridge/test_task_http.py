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
            process = subprocess.Popen(
                [sys.executable, '-m', 'uvicorn', 'jeff_bridge_api:app',
                 '--host', '127.0.0.1', '--port', str(port), '--log-level', 'error'],
                cwd=bridge_dir, env=env, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL)
            base = f'http://127.0.0.1:{port}'

            def call(method, path, data=None, worker=False):
                headers = {'Content-Type': 'application/json',
                           ('X-Task-Worker-Key' if worker else 'X-Bridge-Key'):
                           env['TASK_WORKER_KEY' if worker else 'BRIDGE_KEY']}
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
