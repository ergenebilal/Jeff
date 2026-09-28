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
from pablo.pablo_task_guard import TaskGuard
from pablo.pablo_bridge_auth import bridge_worker_headers, validate_bridge_result_ack
from pablo.pablo_approval_handoff import apply_approval_decision
from jeff2.bridge.jeff_approval_bot import JeffApprovalBot


class BridgeSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.old_db = bridge.DB_PATH
        self.old_key = bridge.BRIDGE_KEY
        worker_env = patch.dict(os.environ, {'TASK_WORKER_KEY': 'fixture-worker-key',
                                          'PABLO_WORKER_ID': 'fake-pablo'})
        worker_env.start()
        self.addCleanup(worker_env.stop)
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

    def test_worker_auth_fails_closed_without_distinct_key_and_identity(self):
        with patch.dict(os.environ, {'TASK_WORKER_KEY': 'fixture-bridge-key'}):
            with self.assertRaises(bridge.HTTPException) as same_key:
                bridge.require_pablo_worker('fixture-bridge-key', 'fake-pablo')
        self.assertEqual(same_key.exception.status_code, 401)
        with patch.dict(os.environ, {'PABLO_WORKER_ID': ''}):
            with self.assertRaises(bridge.HTTPException) as no_identity:
                bridge.require_pablo_worker('fixture-worker-key', 'fake-pablo')
        self.assertEqual(no_identity.exception.status_code, 403)

    def test_jeff_approval_key_cannot_reuse_bridge_or_worker_key(self):
        for key in ('fixture-bridge-key', 'fixture-worker-key', ''):
            with self.subTest(key=key), patch.dict(os.environ, {'JEFF_APPROVAL_KEY': key}):
                with self.assertRaises(bridge.HTTPException) as rejected:
                    bridge.require_jeff_approval_key(key)
                self.assertEqual(rejected.exception.status_code, 401)

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
                                     status='SUCCESS', ok=True, result='claimed',
                                     worker_id='fake-pablo', request_id='forged')
        response = asyncio.run(bridge.alfred_result(
            result, 'fixture-bridge-key', 'fixture-worker-key', 'fake-pablo'))
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

    def test_approval_handoff_is_bound_single_use_and_worker_scoped(self):
        self.submit({'url': 'https://example.test'})
        task = asyncio.run(bridge.alfred_get_tasks(
            1, 'fixture-bridge-key', 'fake-pablo', 'fixture-worker-key'))['tasks'][0]
        pending = bridge.AlfredResult(
            task_id='task-1', type='BROWSER_ACTION', status='APPROVAL_REQUIRED',
            request_id='task-1', approval_id='approval-1', digest=task['digest'],
            worker_id='fake-pablo', attempt=task['attempt'])
        self.assertEqual(asyncio.run(bridge.alfred_result(
            pending, 'fixture-bridge-key', 'fixture-worker-key', 'fake-pablo'))['status'],
            'approval_required')
        self.assertEqual(asyncio.run(bridge.alfred_result(
            pending.model_copy(update={'approval_id': 'changed'}),
            'fixture-bridge-key', 'fixture-worker-key', 'fake-pablo'))['status'],
            'quarantined')
        self.assertEqual(asyncio.run(bridge.alfred_result(
            pending.model_copy(update={'approval_id': None}),
            'fixture-bridge-key', 'fixture-worker-key', 'fake-pablo'))['status'],
            'quarantined')
        self.assertEqual(asyncio.run(bridge.alfred_result(
            pending.model_copy(update={'status': 'SUCCESS', 'ok': True}),
            'fixture-bridge-key', 'fixture-worker-key', 'fake-pablo'))['status'],
            'quarantined')
        self.submit({'url': 'https://other.test'}, task_id='task-2')
        other = asyncio.run(bridge.alfred_get_tasks(
            1, 'fixture-bridge-key', 'fake-pablo', 'fixture-worker-key'))['tasks'][0]
        reused_id = pending.model_copy(update={
            'task_id': 'task-2', 'request_id': 'task-2', 'digest': other['digest'],
            'attempt': other['attempt']})
        self.assertEqual(asyncio.run(bridge.alfred_result(
            reused_id, 'fixture-bridge-key', 'fixture-worker-key', 'fake-pablo'))['status'],
            'quarantined')
        with sqlite3.connect(bridge.DB_PATH) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM alfred_approvals').fetchone()[0], 1)
        with patch.dict(os.environ, {'APPROVAL_OWNER_ID': '42',
                                      'JEFF_APPROVAL_KEY': 'fixture-jeff-approval-key'}):
            with self.assertRaises(bridge.HTTPException) as unauthorized:
                asyncio.run(bridge.alfred_get_approvals('fixture-bridge-key', None))
            self.assertEqual(unauthorized.exception.status_code, 401)
            approvals = asyncio.run(bridge.alfred_get_approvals(
                'fixture-bridge-key', 'fixture-jeff-approval-key'))['approvals']
            self.assertEqual(len(approvals), 1)
            self.assertEqual(approvals[0]['digest'], task['digest'])
            card = asyncio.run(bridge.alfred_approval_card(
                'approval-1', 'fixture-bridge-key', 'fixture-jeff-approval-key'))
            self.assertEqual(card['task_id'], 'task-1')
            self.assertFalse(card['notified'])
            with patch.dict(os.environ, {'APPROVAL_OWNER_ID': ''}):
                with self.assertRaises(bridge.HTTPException) as unconfigured:
                    asyncio.run(bridge.alfred_claim_approval(
                        'task-1', 'fixture-bridge-key', 'fixture-jeff-approval-key'))
                self.assertEqual(unconfigured.exception.status_code, 503)
            self.assertTrue(asyncio.run(bridge.alfred_claim_approval(
                'task-1', 'fixture-bridge-key', 'fixture-jeff-approval-key'))['claimed'])
            self.assertTrue(asyncio.run(bridge.alfred_approval_card(
                'approval-1', 'fixture-bridge-key', 'fixture-jeff-approval-key'))['notified'])
            self.assertFalse(asyncio.run(bridge.alfred_claim_approval(
                'task-1', 'fixture-bridge-key', 'fixture-jeff-approval-key'))['claimed'])
            with self.assertRaises(bridge.HTTPException) as wrong_owner:
                asyncio.run(bridge.alfred_decide_approval(
                    'task-1', bridge.AlfredApprovalDecision(
                        approval_id='approval-1', digest=task['digest'], decision='approve',
                        actor_id='other', chat_id='42'), 'fixture-bridge-key',
                    'fixture-jeff-approval-key'))
            self.assertEqual(wrong_owner.exception.status_code, 403)
            decision = bridge.AlfredApprovalDecision(
                approval_id='approval-1', digest=task['digest'], decision='approve',
                actor_id='42', chat_id='42')
            self.assertEqual(asyncio.run(bridge.alfred_decide_approval(
                'task-1', decision, 'fixture-bridge-key',
                'fixture-jeff-approval-key'))['status'], 'decided')
            with self.assertRaises(bridge.HTTPException) as replay:
                asyncio.run(bridge.alfred_decide_approval(
                    'task-1', decision, 'fixture-bridge-key', 'fixture-jeff-approval-key'))
            self.assertEqual(replay.exception.status_code, 409)
            with self.assertRaises(bridge.HTTPException) as wrong_worker:
                asyncio.run(bridge.alfred_get_approval_decisions(
                    'fixture-bridge-key', 'other-pablo', 'fixture-worker-key'))
            self.assertEqual(wrong_worker.exception.status_code, 403)
            decisions = asyncio.run(bridge.alfred_get_approval_decisions(
                'fixture-bridge-key', 'fake-pablo', 'fixture-worker-key'))['decisions']
            self.assertEqual(len(decisions), 1)
            self.assertEqual(decisions[0]['approval_id'], 'approval-1')
            asyncio.run(bridge.init_db())
            self.assertEqual(len(asyncio.run(bridge.alfred_get_approval_decisions(
                'fixture-bridge-key', 'fake-pablo', 'fixture-worker-key'))['decisions']), 1)


class TaskGuardNotificationTests(unittest.TestCase):
    def test_replayed_approval_claims_one_notification_across_restart(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
            path = Path(temp) / 'guard.sqlite3'
            actions = {'browser_open': lambda _: {'ok': True}}
            guard = TaskGuard(path, actions, owner='42', desktop_ready=lambda: True)
            request = guard.execute('browser_open', {'url': 'https://example.test'}, 'repeat-1')
            self.assertEqual(request['status'], 'APPROVAL_REQUIRED')
            self.assertTrue(guard.claim_approval_notification('repeat-1'))
            self.assertFalse(guard.claim_approval_notification('repeat-1'))
            reopened = TaskGuard(path, actions, owner='42', desktop_ready=lambda: True)
            self.assertEqual(reopened.execute('browser_open', {'url': 'https://example.test'},
                                              'repeat-1')['status'], 'APPROVAL_REQUIRED')
            self.assertFalse(reopened.claim_approval_notification('repeat-1'))

    def test_existing_taskguard_database_migrates_without_losing_requests(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
            path = Path(temp) / 'legacy-guard.sqlite3'
            with sqlite3.connect(path) as db:
                db.execute('CREATE TABLE requests (id TEXT PRIMARY KEY, digest TEXT, action TEXT, '
                           'params TEXT, status TEXT, response TEXT, approval TEXT, expires REAL, '
                           'consumed INTEGER DEFAULT 0)')
                db.execute("INSERT INTO requests(id,status,response) VALUES('old','SUCCESS',?)",
                           ('{"request_id":"old","status":"SUCCESS","ok":true}',))
            guard = TaskGuard(path, {}, owner='42', desktop_ready=lambda: True)
            self.assertEqual(guard.get('old')['status'], 'SUCCESS')
            with sqlite3.connect(path) as db:
                self.assertIn('approval_notified',
                              {row[1] for row in db.execute('PRAGMA table_info(requests)')})


class PabloWorkerHeaderTests(unittest.TestCase):
    def test_missing_or_reused_worker_secret_fails_closed(self):
        config = {'auth_token': 'fixture-bridge-key', 'node_id': 'fake-pablo'}
        for worker_key in (None, '', 'fixture-bridge-key'):
            with self.subTest(worker_key=worker_key), self.assertRaises(RuntimeError):
                bridge_worker_headers({**config, 'task_worker_key': worker_key})

    def test_approval_result_requires_durable_handoff_ack(self):
        pending = {'status': 'APPROVAL_REQUIRED'}
        with self.assertRaises(RuntimeError):
            validate_bridge_result_ack(pending, {'status': 'approval_required'})
        self.assertTrue(validate_bridge_result_ack(
            pending, {'status': 'approval_required', 'handoff': 'stored'}))


class PabloApprovalHandoffTests(unittest.TestCase):
    def test_decision_checks_local_approval_and_executes_once(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
            effects, sent = [], []
            guard = TaskGuard(Path(temp) / 'guard.sqlite3',
                              {'browser_open': lambda params: effects.append(params) or {'ok': True}},
                              owner='42', desktop_ready=lambda: True)
            pending = guard.execute('browser_open', {'url': 'https://example.test'}, 'task-1')
            decision = {'task_id': 'task-1', 'approval_id': pending['approval_id'],
                        'digest': 'fixture-digest', 'worker_id': 'fake-pablo', 'attempt': 1,
                        'type': 'BROWSER_ACTION', 'decision': 'approve',
                        'actor_id': '42', 'chat_id': '42'}
            self.assertFalse(apply_approval_decision(
                guard, {**decision, 'approval_id': 'forged'}, 'fake-pablo', sent.append))
            self.assertFalse(apply_approval_decision(
                guard, {**decision, 'worker_id': 'other-pablo'}, 'fake-pablo', sent.append))
            self.assertEqual(len(effects), 0)
            self.assertTrue(apply_approval_decision(guard, decision, 'fake-pablo', sent.append))
            self.assertTrue(apply_approval_decision(guard, decision, 'fake-pablo', sent.append))
            self.assertEqual(len(effects), 1)
            self.assertEqual(sent[0]['request_id'], 'task-1')
            self.assertEqual(sent[0]['digest'], 'fixture-digest')

    def test_rejection_never_executes(self):
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
            effects, sent = [], []
            guard = TaskGuard(Path(temp) / 'guard.sqlite3',
                              {'browser_open': lambda params: effects.append(params) or {'ok': True}},
                              owner='42', desktop_ready=lambda: True)
            pending = guard.execute('browser_open', {'url': 'https://example.test'}, 'reject-1')
            decision = {'task_id': 'reject-1', 'approval_id': pending['approval_id'],
                        'digest': 'fixture-digest', 'worker_id': 'fake-pablo', 'attempt': 1,
                        'type': 'BROWSER_ACTION', 'decision': 'reject',
                        'actor_id': '42', 'chat_id': '42'}
            self.assertTrue(apply_approval_decision(guard, decision, 'fake-pablo', sent.append))
            self.assertEqual(guard.get('reject-1')['status'], 'REJECTED')
            self.assertEqual(sent[0]['status'], 'REJECTED')
            self.assertEqual(effects, [])


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
                       BRIDGE_HOST='127.0.0.1', BRIDGE_PORT=str(port),
                       TASK_WORKER_KEY='fixture-worker-key', PABLO_WORKER_ID='fake-pablo',
                       APPROVAL_OWNER_ID='42', JEFF_APPROVAL_KEY='fixture-jeff-approval-key')
            proc = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'jeff_bridge_api:app',
                                     '--host', '127.0.0.1', '--port', str(port), '--log-level', 'error'],
                                    cwd=ROOT, env=env, stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL)
            base = f'http://127.0.0.1:{port}'
            headers = {'X-Bridge-Key': 'fixture-bridge-key'}
            jeff_headers = {**headers, 'X-Jeff-Approval-Key': 'fixture-jeff-approval-key'}
            worker_headers = bridge_worker_headers({
                'auth_token': 'fixture-bridge-key',
                'task_worker_key': 'fixture-worker-key',
                'node_id': 'fake-pablo',
            })
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
                self.assertEqual(requests.get(base + '/alfred/tasks?timeout=1',
                                              headers={**headers, 'X-Worker-ID': 'fake-pablo'},
                                              timeout=3).status_code, 401)
                self.assertEqual(requests.get(base + '/alfred/tasks?timeout=1',
                                              headers={**worker_headers, 'X-Worker-ID': 'other-pablo'},
                                              timeout=3).status_code, 403)
                self.assertEqual(requests.post(base + '/alfred/heartbeat', json={'agent': 'pablo'},
                                               headers=headers, timeout=2).status_code, 401)
                self.assertEqual(requests.post(base + '/alfred/heartbeat', json={'agent': 'pablo'},
                                               headers=worker_headers, timeout=2).status_code, 200)
                self.assertTrue(requests.get(base + '/health', timeout=2).json()['alfred_online'])
                body = {'task_id': 'smoke-1', 'type': 'BROWSER_ACTION',
                        'payload': {'url': 'https://example.test'}}
                first = requests.post(base + '/alfred/task', json=body, headers=headers, timeout=2)
                self.assertEqual(first.status_code, 200, first.text)
                self.assertEqual(requests.get(base + '/alfred/tasks?timeout=1',
                                              headers={**worker_headers, 'X-Worker-ID': 'other-pablo'},
                                              timeout=3).status_code, 403)
                with sqlite3.connect(db_path) as db:
                    self.assertEqual(db.execute(
                        "SELECT status FROM alfred_events WHERE task_id='smoke-1'"
                    ).fetchone()[0], 'pending')
                self.assertEqual(requests.post(base + '/alfred/task', json=body, headers=headers, timeout=2).status_code, 200)
                changed = dict(body, payload={'url': 'https://changed.test'})
                self.assertEqual(requests.post(base + '/alfred/task', json=changed, headers=headers, timeout=2).status_code, 409)
                polled = requests.get(base + '/alfred/tasks?timeout=1',
                                      headers=worker_headers, timeout=3).json()['tasks']
                self.assertEqual(len(polled), 1)
                task = polled[0]
                spoofed = {'task_id': 'smoke-1', 'type': 'BROWSER_ACTION',
                           'status': 'SUCCESS', 'request_id': 'smoke-1',
                           'digest': task['digest'], 'worker_id': 'other-pablo',
                           'attempt': task['attempt']}
                self.assertEqual(requests.post(base + '/alfred/result', json=spoofed,
                                               headers=worker_headers, timeout=2).status_code, 403)
                forged = {'task_id': 'smoke-1', 'type': 'BROWSER_ACTION', 'status': 'SUCCESS',
                          'ok': True, 'request_id': 'smoke-1', 'digest': 'wrong',
                          'worker_id': 'fake-pablo', 'attempt': task['attempt']}
                self.assertEqual(requests.post(base + '/alfred/result', json=forged,
                                               headers=worker_headers, timeout=2).json()['status'], 'quarantined')
                count = []
                guard = TaskGuard(Path(temp) / 'guard.sqlite3',
                                  {'browser_open': lambda params: count.append(params) or {'ok': True}},
                                  owner='42', desktop_ready=lambda: True)
                pending = guard.execute('browser_open', body['payload'], 'smoke-1')
                self.assertEqual(pending['status'], 'APPROVAL_REQUIRED')
                self.assertEqual(len(count), 0)
                pending_result = {**pending, 'type': 'BROWSER_ACTION', 'digest': task['digest'],
                                  'worker_id': 'fake-pablo', 'attempt': task['attempt']}
                approval_response = requests.post(base + '/alfred/result', json=pending_result,
                                                  headers=worker_headers, timeout=2).json()
                self.assertTrue(validate_bridge_result_ack(pending_result, approval_response))
                self.assertEqual(requests.get(base + '/alfred/approvals', timeout=2).status_code, 401)
                self.assertEqual(requests.get(base + '/alfred/approvals', headers=headers,
                                              timeout=2).status_code, 401)
                approval_cards = requests.get(base + '/alfred/approvals', headers=jeff_headers,
                                              timeout=2).json()['approvals']
                self.assertEqual(len(approval_cards), 1)
                self.assertEqual(approval_cards[0]['approval_id'], pending['approval_id'])

                def jeff_bridge_call(method, path, payload=None):
                    response = requests.request(method, base + path, json=payload,
                                                headers=jeff_headers, timeout=2)
                    response.raise_for_status()
                    return response.json()

                telegram_calls = []
                bot = JeffApprovalBot('42', jeff_bridge_call,
                                      lambda method, payload: telegram_calls.append((method, payload)))
                bot.send_pending()
                bot.send_pending()
                self.assertEqual(len([call for call in telegram_calls if call[0] == 'sendMessage']), 1)
                self.assertFalse(requests.post(base + '/alfred/approvals/smoke-1/claim',
                                               headers=jeff_headers, timeout=2).json()['claimed'])
                decision = {'approval_id': pending['approval_id'], 'digest': task['digest'],
                            'decision': 'approve', 'actor_id': '42', 'chat_id': '42'}
                self.assertEqual(requests.post(base + '/alfred/approvals/smoke-1/decision',
                                               json={**decision, 'actor_id': 'other'},
                                               headers=jeff_headers, timeout=2).status_code, 403)
                self.assertEqual(requests.post(base + '/alfred/approvals/smoke-1/decision',
                                               json={**decision, 'digest': 'changed'},
                                               headers=jeff_headers, timeout=2).status_code, 409)
                update = {'callback_query': {'id': 'fixture-callback',
                    'data': 'a:' + pending['approval_id'], 'from': {'id': 42},
                    'message': {'chat': {'id': 42}}}}
                bot.handle_update(update)
                bot.handle_update(update)
                self.assertEqual(len([call for call in telegram_calls
                                      if call[0] == 'answerCallbackQuery']), 2)
                self.assertEqual(requests.post(base + '/alfred/approvals/smoke-1/decision',
                                               json=decision, headers=jeff_headers, timeout=2).status_code, 409)
                self.assertEqual(requests.get(base + '/alfred/approval-decisions',
                                              headers=headers, timeout=2).status_code, 401)
                decisions = requests.get(base + '/alfred/approval-decisions',
                                         headers=worker_headers, timeout=2).json()['decisions']
                self.assertEqual(len(decisions), 1)
                with sqlite3.connect(db_path) as db:
                    db.execute("UPDATE alfred_events SET delivered_at=0 WHERE task_id='smoke-1'")
                reconciliation = requests.get(base + '/alfred/tasks?timeout=1',
                                              headers=worker_headers, timeout=3).json()['tasks']
                self.assertEqual(len(reconciliation), 1)
                self.assertTrue(reconciliation[0]['reconcile_only'])
                self.assertEqual(guard.get('smoke-1')['status'], 'APPROVAL_REQUIRED')
                self.assertEqual(len(count), 0)
                sent = []
                self.assertTrue(apply_approval_decision(guard, decisions[0], 'fake-pablo', sent.append))
                self.assertEqual(sent[0]['status'], 'SUCCESS')
                self.assertEqual(guard.execute('browser_open', body['payload'], 'smoke-1')['status'], 'SUCCESS')
                self.assertEqual(len(count), 1)
                result = sent[0]
                self.assertEqual(requests.post(base + '/alfred/result', json=result,
                                               headers=headers, timeout=2).status_code, 401)
                with sqlite3.connect(db_path) as db:
                    self.assertEqual(db.execute(
                        "SELECT count(*) FROM alfred_results WHERE task_id='smoke-1'"
                    ).fetchone()[0], 0)
                response = requests.post(base + '/alfred/result', json=result, headers=worker_headers, timeout=2)
                self.assertEqual(response.json()['status'], 'unverified')
                self.assertEqual(requests.post(base + '/alfred/result', json=result, headers=worker_headers, timeout=2).json()['status'], 'quarantined')
                with sqlite3.connect(db_path) as db:
                    self.assertEqual(db.execute("SELECT count(*) FROM alfred_events WHERE task_id='smoke-1'").fetchone()[0], 1)
                    self.assertEqual(db.execute("SELECT count(*) FROM alfred_results WHERE task_id='smoke-1'").fetchone()[0], 1)
                print('HTTP_SQLITE_SMOKE: heartbeat=online approval_cards=1 decisions=1 '
                      'events=1 executions=1 results=1 duplicate=quarantined')
            finally:
                proc.terminate()
                proc.wait(timeout=5)


if __name__ == '__main__':
    unittest.main()
