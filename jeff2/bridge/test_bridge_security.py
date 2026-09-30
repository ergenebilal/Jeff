"""PR-01 regressions against the production bridge module."""
import asyncio
import os
from pathlib import Path
import sqlite3
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import requests

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
import jeff_bridge_api as bridge


class BridgeSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.old_db = bridge.DB_PATH
        self.old_key = bridge.BRIDGE_KEY
        bridge.DB_PATH = str(Path(self.temp.name) / 'bridge.sqlite3')
        bridge.BRIDGE_KEY = 'fixture-bridge-key'
        self.addCleanup(setattr, bridge, 'DB_PATH', self.old_db)
        self.addCleanup(setattr, bridge, 'BRIDGE_KEY', self.old_key)
        asyncio.run(bridge.init_db())

    def submit(self, payload, task_id='task-1'):
        body = bridge.AlfredTaskRequest(task_id=task_id, type='BROWSER_ACTION', payload=payload)
        return asyncio.run(bridge.create_alfred_task(body, 'fixture-bridge-key'))

    def test_missing_and_placeholder_secret_rejected(self):
        for key in (None, '', 'cybergene-bridge-2026'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                bridge.validate_bridge_key(key)

    def test_default_host_is_loopback(self):
        self.assertEqual(bridge.host_from_environment({}), '127.0.0.1')

    def test_same_id_same_content_is_one_event(self):
        first = self.submit({'url': 'https://example.test'})
        second = self.submit({'url': 'https://example.test'})
        self.assertEqual(first['task_id'], second['task_id'])
        with sqlite3.connect(bridge.DB_PATH) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM alfred_events').fetchone()[0], 1)

    def test_same_id_changed_content_conflicts(self):
        self.submit({'url': 'https://example.test'})
        with self.assertRaises(bridge.HTTPException) as raised:
            self.submit({'url': 'https://changed.test'})
        self.assertEqual(raised.exception.status_code, 409)

    def test_same_id_changed_policy_conflicts(self):
        self.submit({'url': 'https://example.test'})
        changed = bridge.AlfredTaskRequest(task_id='task-1', type='BROWSER_ACTION',
                                           payload={'url': 'https://example.test'},
                                           policy={'approval': 'skip'})
        with self.assertRaises(bridge.HTTPException) as raised:
            asyncio.run(bridge.create_alfred_task(changed, 'fixture-bridge-key'))
        self.assertEqual(raised.exception.status_code, 409)

    def test_unknown_result_cannot_create_success(self):
        result = bridge.AlfredResult(task_id='forged', type='BROWSER_ACTION',
                                     status='SUCCESS', ok=True, result='claimed')
        response = asyncio.run(bridge.alfred_result(result, 'fixture-bridge-key'))
        self.assertNotEqual(response.get('status'), 'verified')
        with sqlite3.connect(bridge.DB_PATH) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM alfred_events WHERE task_id='forged' AND status='result'").fetchone()[0], 0)

    def test_migration_keeps_legacy_events(self):
        legacy = str(Path(self.temp.name) / 'legacy.sqlite3')
        with sqlite3.connect(legacy) as db:
            db.execute('CREATE TABLE alfred_events (id INTEGER PRIMARY KEY, task_id TEXT, type TEXT, payload TEXT, status TEXT, created_at TEXT)')
            db.execute("INSERT INTO alfred_events(task_id,type,payload,status) VALUES('old','ping','{}','pending')")
        bridge.DB_PATH = legacy
        asyncio.run(bridge.init_db())
        with sqlite3.connect(legacy) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM alfred_events WHERE task_id='old'").fetchone()[0], 1)
            self.assertIn('digest', {row[1] for row in db.execute('PRAGMA table_info(alfred_events)')})
        status = asyncio.run(bridge.alfred_task_status('old', 'fixture-bridge-key'))
        self.assertEqual(status['status'], 'legacy_unverified')
        self.assertFalse(status['ok'])


class RealHttpSmokeTests(unittest.TestCase):
    def test_process_rejects_missing_secret(self):
        env = os.environ.copy()
        env.pop('BRIDGE_KEY', None)
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        completed = subprocess.run(
            [sys.executable, '-m', 'uvicorn', 'jeff_bridge_api:app',
             '--host', '127.0.0.1', '--port', str(port), '--log-level', 'error'],
            cwd=ROOT, env=env, capture_output=True, text=True, timeout=10)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn('BRIDGE_KEY', completed.stderr)
        self.assertNotIn('fixture-bridge-key', completed.stderr)

    def test_local_http_sqlite_guard_approval_and_single_execution(self):
        sys.path.insert(0, str(ROOT.parent.parent / 'pablo'))
        from pablo_task_guard import TaskGuard
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
            with socket.socket() as sock:
                sock.bind(('127.0.0.1', 0))
                port = sock.getsockname()[1]
            db_path = str(Path(temp) / 'bridge.sqlite3')
            env = os.environ.copy()
            env.update(BRIDGE_KEY='fixture-bridge-key', BRIDGE_DB_PATH=db_path,
                       BRIDGE_HOST='127.0.0.1', BRIDGE_PORT=str(port))
            proc = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'jeff_bridge_api:app',
                                     '--host', '127.0.0.1', '--port', str(port), '--log-level', 'error'],
                                    cwd=ROOT, env=env, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
            base = f'http://127.0.0.1:{port}'
            headers = {'X-Bridge-Key': 'fixture-bridge-key'}
            for _ in range(100):
                try:
                    if requests.get(base + '/health', timeout=.2).status_code == 200:
                        break
                except requests.ConnectionError:
                    pass
                import time
                time.sleep(.05)
            else:
                self.fail('Bridge did not start')
            try:
                self.assertEqual(requests.get(base + '/alfred_client', timeout=2).status_code, 401)
                self.assertEqual(requests.get(base + '/alfred_client', headers=headers, timeout=2).status_code, 404)
                body = {'task_id': 'smoke-1', 'type': 'BROWSER_ACTION',
                        'payload': {'url': 'https://example.test'}}
                first = requests.post(base + '/alfred/task', json=body, headers=headers, timeout=2)
                self.assertEqual(first.status_code, 200, first.text)
                self.assertEqual(requests.post(base + '/alfred/task', json=body, headers=headers, timeout=2).status_code, 200)
                changed = dict(body, payload={'url': 'https://changed.test'})
                self.assertEqual(requests.post(base + '/alfred/task', json=changed, headers=headers, timeout=2).status_code, 409)
                polled = requests.get(base + '/alfred/tasks?timeout=1',
                                      headers={**headers, 'X-Worker-ID': 'fake-pablo'}, timeout=3).json()['tasks']
                self.assertEqual(len(polled), 1)
                task = polled[0]
                forged = {'task_id': 'smoke-1', 'type': 'BROWSER_ACTION', 'status': 'SUCCESS',
                          'ok': True, 'request_id': 'smoke-1', 'digest': 'wrong',
                          'worker_id': 'fake-pablo', 'attempt': task['attempt']}
                self.assertEqual(requests.post(base + '/alfred/result', json=forged,
                                               headers=headers, timeout=2).json()['status'], 'quarantined')
                count = []
                guard = TaskGuard(Path(temp) / 'guard.sqlite3',
                                  {'social_post': lambda params: count.append(params) or {'ok': True}},
                                  owner='42', desktop_ready=lambda: True)
                pending = guard.execute('social_post', body['payload'], 'smoke-1')
                self.assertEqual(pending['status'], 'APPROVAL_REQUIRED')
                self.assertEqual(len(count), 0)
                pending_result = {**pending, 'type': 'BROWSER_ACTION', 'digest': task['digest'],
                                  'worker_id': 'fake-pablo', 'attempt': task['attempt']}
                self.assertEqual(requests.post(base + '/alfred/result', json=pending_result,
                                               headers=headers, timeout=2).json()['status'], 'approval_required')
                with sqlite3.connect(db_path) as db:
                    db.execute("UPDATE alfred_events SET delivered_at=0 WHERE task_id='smoke-1'")
                reconciliation = requests.get(base + '/alfred/tasks?timeout=1',
                                              headers={**headers, 'X-Worker-ID': 'fake-pablo'}, timeout=3).json()['tasks']
                self.assertEqual(len(reconciliation), 1)
                self.assertTrue(reconciliation[0]['reconcile_only'])
                self.assertEqual(guard.get('smoke-1')['status'], 'APPROVAL_REQUIRED')
                self.assertEqual(len(count), 0)
                approved = guard.approve(pending['approval_id'], '42', '42')
                self.assertEqual(approved['status'], 'SUCCESS')
                self.assertEqual(guard.execute('social_post', body['payload'], 'smoke-1')['status'], 'SUCCESS')
                self.assertEqual(len(count), 1)
                result = {**approved, 'type': 'BROWSER_ACTION', 'digest': task['digest'],
                          'worker_id': 'fake-pablo', 'attempt': task['attempt']}
                response = requests.post(base + '/alfred/result', json=result, headers=headers, timeout=2)
                self.assertEqual(response.json()['status'], 'unverified')
                self.assertEqual(requests.post(base + '/alfred/result', json=result, headers=headers, timeout=2).json()['status'], 'quarantined')
                with sqlite3.connect(db_path) as db:
                    self.assertEqual(db.execute("SELECT count(*) FROM alfred_events WHERE task_id='smoke-1'").fetchone()[0], 1)
                    self.assertEqual(db.execute("SELECT count(*) FROM alfred_results WHERE task_id='smoke-1'").fetchone()[0], 1)
                print('HTTP_SQLITE_SMOKE: events=1 executions=1 results=1 duplicate=quarantined')
            finally:
                proc.terminate()
                proc.wait(timeout=5)


if __name__ == '__main__':
    unittest.main()
