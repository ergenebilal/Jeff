"""Actual interrupted processes, persisted SQLite/files and real HTTP handlers."""
import ast
from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.parse
from unittest import mock
from pablo_local_drafts import LocalDraftStore, expectation
from pablo_task_guard import TaskGuard, allowed_ip

CHILD = '''
import os, sys
from pathlib import Path
from pablo_task_guard import TaskGuard
guard = TaskGuard(Path(sys.argv[1]) / 'journal.db', {}, 'fixture', lambda: False, clock=lambda: 1000)
mode = sys.argv[2]
original = guard.local_drafts.write
def write(rid, expected):
    if mode == 'before_write': os._exit(91)
    value = original(rid, expected)
    if mode == 'after_write': os._exit(91)
    return value
guard.local_drafts.write = write
observe = guard.local_drafts.observe
def interrupted_observe(rid, expected):
    value = observe(rid, expected)
    os._exit(91)
guard.local_drafts.observe = interrupted_observe if mode == 'after_observe' else observe
guard.execute('local_draft', {'name':'proof','format':'txt','content':'restart fixture','deadline_at':900}, 'interrupted')
'''


class WorkTrackingTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root, self.now = Path(temp.name), 1200
        self.params = {'name': 'proof', 'format': 'txt', 'content': 'restart fixture', 'deadline_at': 900}

    def guard(self):
        return TaskGuard(self.root / 'journal.db', {}, 'fixture', lambda: False, clock=lambda: self.now)

    def crash(self, mode):
        env = os.environ | {'PYTHONPATH': str(Path(__file__).parent) + os.pathsep + os.environ.get('PYTHONPATH', '')}
        child = subprocess.run([sys.executable, '-c', CHILD, str(self.root), mode], env=env, capture_output=True, timeout=10)
        self.assertEqual(child.returncode, 91, child.stderr.decode())

    def test_real_crash_after_publication_recovers_without_rewriting(self):
        self.crash('after_write')
        guard = self.guard()
        path = guard.local_drafts.path('interrupted', expectation('interrupted', self.params))
        before = path.stat().st_mtime_ns
        with mock.patch.object(LocalDraftStore, 'write', side_effect=AssertionError('replayed')):
            result = guard.recover_pending()[0]
            self.assertEqual(result['status'], 'SUCCESS')
            self.assertTrue(result['recovered_by_observation'])
            self.assertFalse(result['action_verified'])
            self.assertFalse(result['result']['replayed'])
            self.assertEqual(guard.execute('local_draft', self.params, 'interrupted'), result)
            self.assertEqual(guard.reconcile('interrupted'), result)
        self.assertEqual(path.stat().st_mtime_ns, before)
        view = self.guard().work_status('interrupted')
        self.assertEqual([e['phase'] for e in view['events']], ['claimed', 'publishing', 'completed'])
        self.assertEqual(view['next_step'], 'none')
        self.assertFalse(view['open'])
        self.assertFalse(view['overdue'])

    def test_real_crash_after_observation_recovers_lost_result(self):
        self.crash('after_observe')
        guard = self.guard()
        self.assertEqual(guard.work_status('interrupted')['phase'], 'observing')
        with mock.patch.object(LocalDraftStore, 'write', side_effect=AssertionError('replayed')):
            self.assertTrue(guard.reconcile('interrupted')['outcome_verified'])
        self.assertEqual(guard.work_snapshot()['open_count'], 0)

    def test_crash_before_publication_waits_then_stays_open_without_replay(self):
        self.crash('before_write')
        guard = self.guard()
        with mock.patch.object(LocalDraftStore, 'write', side_effect=AssertionError('replayed')):
            self.assertEqual(guard.reconcile('interrupted')['status'], 'IN_PROGRESS')
            self.now = 1600
            self.assertEqual(guard.recover_pending()[0]['status'], 'VERIFICATION_UNAVAILABLE')
            self.assertEqual(guard.execute('local_draft', self.params, 'interrupted')['status'], 'VERIFICATION_UNAVAILABLE')
        view = self.guard().work_status('interrupted')
        self.assertTrue(view['open'])
        self.assertTrue(view['overdue'])
        self.assertEqual(view['deadline_at'], 900)
        self.assertEqual(view['waiting_for'], 'file_evidence')
        self.assertEqual(view['next_step'], 'observe_file_without_writing')
        self.assertFalse((self.root / 'verified-drafts').exists())

    def test_wrong_or_unreadable_file_never_closes_interrupted_work(self):
        self.crash('after_write')
        guard = self.guard()
        path = guard.local_drafts.path('interrupted', expectation('interrupted', self.params))
        path.write_bytes(b'wrong')
        self.now = 1600
        self.assertEqual(guard.reconcile('interrupted')['status'], 'OUTCOME_MISMATCH')
        with mock.patch.object(LocalDraftStore, 'observe', side_effect=PermissionError('fixture')):
            self.assertEqual(guard.reconcile('interrupted')['status'], 'VERIFICATION_UNAVAILABLE')
        self.assertTrue(guard.work_status('interrupted')['open'])
        self.assertEqual(path.read_bytes(), b'wrong')

    def test_changed_stored_binding_blocks_recovery_before_observation(self):
        self.crash('after_write')
        guard = self.guard()
        with guard.connect() as db:
            db.execute('UPDATE requests SET params=?', (json.dumps(self.params | {'content': 'tampered'}),))
        with mock.patch.object(LocalDraftStore, 'observe') as reader:
            self.assertEqual(guard.reconcile('interrupted')['status'], 'RECOVERY_BLOCKED')
            reader.assert_not_called()

    def test_legacy_unknown_is_visible_with_unknown_dates_and_never_executed(self):
        guard = self.guard()
        with guard.connect() as db:
            response = guard.response('legacy', 'IN_PROGRESS')
            db.execute('INSERT INTO requests(id,action,params,status,response) VALUES(?,?,?,?,?)',
                       ('legacy', 'shell', '{}', 'IN_PROGRESS', json.dumps(response)))
        reopened = self.guard()
        with mock.patch.object(reopened, '_run', side_effect=AssertionError('legacy replay')):
            self.assertEqual(reopened.reconcile('legacy'), response)
            self.assertEqual(reopened.recover_pending(), [])
        view = reopened.work_snapshot()['items'][0]
        self.assertEqual(view['phase'], 'legacy_unknown')
        self.assertIsNone(view['created_at'])
        self.assertIsNone(view['deadline_at'])
        self.assertFalse(view['deadline_known'])
        self.assertTrue(view['open'])
        self.assertNotIn('params', view)

    def test_second_guard_cannot_replay_or_fail_an_active_writer(self):
        guard = self.guard()
        entered, release = threading.Event(), threading.Event()
        original = guard.local_drafts.write
        def delayed(rid, expected):
            entered.set()
            if not release.wait(5):
                raise TimeoutError('fixture')
            return original(rid, expected)
        with mock.patch.object(guard.local_drafts, 'write', delayed), ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(guard.execute, 'local_draft', self.params, 'active')
            self.assertTrue(entered.wait(3))
            other = self.guard()
            try:
                self.assertEqual(other.reconcile('active')['status'], 'IN_PROGRESS')
                self.assertEqual(other.execute('local_draft', self.params, 'active')['status'], 'IN_PROGRESS')
            finally:
                release.set()
            self.assertEqual(future.result(5)['status'], 'SUCCESS')

    def test_deadline_validation_precedes_any_write(self):
        guard = self.guard()
        for index, deadline in enumerate([True, '900', float('nan'), float('inf'), -1, 253402300800]):
            with self.subTest(deadline=index), mock.patch.object(LocalDraftStore, 'write') as writer:
                self.assertEqual(guard.execute('local_draft', self.params | {'deadline_at': deadline}, 'bad-' + str(index))['status'], 'ERROR')
                writer.assert_not_called()

    def test_paging_and_closed_rejections_do_not_hide_open_work(self):
        guard = self.guard()
        for rid in ('one', 'two', 'three', 'expired', 'revalidation'):
            guard.execute('missing', {}, rid)
        with guard.connect() as db:
            guard.store(db, 'two', guard.response('two', 'REJECTED'))
            # Decay operates outside store(); its archived status still wins.
            db.execute("UPDATE requests SET status='EXPIRED' WHERE id='expired'")
            db.execute("UPDATE requests SET status='NEEDS_REVALIDATION' WHERE id='revalidation'")
        first = guard.work_snapshot(limit=1)
        second = guard.work_snapshot(limit=1, offset=first['next_offset'])
        self.assertEqual(first['open_count'], 2)
        self.assertNotEqual(first['items'][0]['request_id'], second['items'][0]['request_id'])
        self.assertIsNone(second['next_offset'])
        self.assertFalse(guard.work_status('two')['open'])
        self.assertFalse(guard.work_status('expired')['open'])

    def handler(self, path, token='fixture'):
        tree = ast.parse(Path(__file__).with_name('hermes_node.py').read_text(encoding='utf-8'))
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'PabloRequestHandler')
        guard = self.guard()
        ns = {'BaseHTTPRequestHandler': BaseHTTPRequestHandler, 'json': json, 'urllib': __import__('urllib'),
              'allowed_ip': allowed_ip, 'CONFIG': {'auth_token': 'fixture'}, 'task_guard': lambda: guard}
        exec(compile(ast.Module(body=[cls], type_ignores=[]), 'real-work-http', 'exec'), ns)
        handler = ns['PabloRequestHandler'].__new__(ns['PabloRequestHandler'])
        handler.path, handler.client_address = path, ('127.0.0.1', 1234)
        handler.headers = {'X-Bridge-Key': token, 'Content-Length': '2'}
        handler.rfile, handler.wfile = io.BytesIO(b'{}'), io.BytesIO()
        handler.send_response, handler.send_header, handler.end_headers = mock.Mock(), mock.Mock(), mock.Mock()
        return handler

    def test_actual_http_tracking_and_reconciliation_require_authentication(self):
        self.crash('after_write')
        for path in ('/work', '/work/interrupted', '/work/interrupted/reconcile'):
            with self.subTest(path=path):
                handler = self.handler(path, token='wrong')
                (handler.do_POST if path.endswith('/reconcile') else handler.do_GET)()
                handler.send_response.assert_called_with(401)
        handler = self.handler('/work/interrupted/reconcile')
        with mock.patch.object(LocalDraftStore, 'write', side_effect=AssertionError('replayed')):
            handler.do_POST()
        self.assertEqual(json.loads(handler.wfile.getvalue())['phase'], 'completed')
        handler = self.handler('/work')
        handler.do_GET()
        self.assertEqual(json.loads(handler.wfile.getvalue())['open_count'], 0)

    def test_bridge_reconciliation_observes_without_execute(self):
        self.crash('after_write')
        guard = self.guard()
        tree = ast.parse(Path(__file__).with_name('hermes_node.py').read_text(encoding='utf-8'))
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'handle_bridge_task')
        execute, sender = mock.Mock(side_effect=AssertionError('replayed')), mock.Mock()
        ns = {'json': json, 'task_guard': lambda: guard, 'execute_request': execute,
              'send_bridge_result': sender, 'CONFIG': {'node_id': 'fixture'}, 'log': mock.Mock()}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), 'real-bridge-reconcile', 'exec'), ns)
        ns['handle_bridge_task']({'task_id': 'interrupted', 'type': 'local_draft', 'payload': self.params,
                                 'digest': 'fixture-digest', 'attempt': 1, 'reconcile_only': True})
        execute.assert_not_called()
        self.assertEqual(sender.call_args.args[0]['status'], 'SUCCESS')
        self.assertEqual(guard.work_status('interrupted')['phase'], 'completed')


if __name__ == '__main__':
    unittest.main()
