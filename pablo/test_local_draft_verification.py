"""Real temporary files and durable guard results; no desktop or external sender."""
import ast
import hashlib
import io
import json
from http.server import BaseHTTPRequestHandler
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from pablo_local_drafts import LocalDraftStore, expectation
from pablo_task_guard import TaskGuard, allowed_ip


class LocalDraftTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.guard = TaskGuard(self.root / 'journal.db', {}, 'fixture-owner', lambda: False)
        self.params = {'name': 'note', 'format': 'txt', 'content': 'İstenen taslak\n'}

    def run_draft(self, params=None, rid='draft-fixture'):
        return self.guard.execute('local_draft', params or self.params, rid)

    def test_actual_read_matches_expected_utf8_bytes(self):
        result = self.run_draft()
        self.assertEqual(result['status'], 'SUCCESS')
        self.assertTrue(result['outcome_verified'])
        proof = result['outcome_evidence']
        self.assertEqual(proof['observed_sha256'], hashlib.sha256(self.params['content'].encode()).hexdigest())
        self.assertEqual(proof['expected_bytes'], proof['observed_bytes'])
        self.assertEqual(proof['method'], 'independent_file_read')
        self.assertNotIn('content', proof)
        self.assertEqual(Path(result['result']['path']).read_bytes(), self.params['content'].encode())

    def test_worker_success_without_file_is_not_success(self):
        with mock.patch.object(LocalDraftStore, 'write', return_value={'ok': True, 'exit_code': 0, 'verified': True}):
            result = self.run_draft()
        self.assertFalse(result['ok'])
        self.assertFalse(result['outcome_verified'])
        self.assertEqual(result['status'], 'VERIFICATION_UNAVAILABLE')

    def test_wrong_file_and_forged_digest_are_rejected(self):
        actual_write = LocalDraftStore.write
        def dishonest(store, rid, expected):
            actual_write(store, rid, expected)
            store.path(rid, expected).write_bytes(b'wrong')
            return {'ok': True, 'exit_code': 0, 'sha256': expected.sha256, 'verified': True}
        with mock.patch.object(LocalDraftStore, 'write', dishonest):
            result = self.run_draft()
        self.assertEqual(result['status'], 'OUTCOME_MISMATCH')
        self.assertFalse(result['outcome_verified'])
        self.assertFalse(result['ok'])

    def test_same_size_wrong_content_does_not_pass(self):
        self.params['content'] = 'wanted'
        actual_write = LocalDraftStore.write
        def wrong(store, rid, expected):
            actual_write(store, rid, expected)
            store.path(rid, expected).write_bytes(b'forged')
            return {'ok': True}
        with mock.patch.object(LocalDraftStore, 'write', wrong):
            self.assertEqual(self.run_draft()['status'], 'OUTCOME_MISMATCH')

    def test_invalid_contract_never_starts_writer(self):
        cases = [self.params | {'name': '../escape'}, self.params | {'format': 'exe'},
                 self.params | {'path': str(self.root / 'outside')}, self.params | {'content': ''},
                 self.params | {'request_id': 'other-task'}, self.params | {'format': 'json', 'content': '{'},
                 self.params | {'name': 'CON'}, self.params | {'content': 'x' * 500001}]
        for index, params in enumerate(cases):
            with self.subTest(index=index), mock.patch.object(LocalDraftStore, 'write') as writer:
                result = self.run_draft(params, 'invalid-' + str(index))
                self.assertFalse(result['ok'])
                self.assertFalse(result.get('outcome_verified', False))
                writer.assert_not_called()

    def test_duplicate_restart_and_changed_input_do_not_rewrite(self):
        first = self.run_draft()
        path = Path(first['result']['path'])
        mtime = path.stat().st_mtime_ns
        reopened = TaskGuard(self.root / 'journal.db', {}, 'fixture-owner', lambda: False)
        with mock.patch.object(LocalDraftStore, 'write') as writer:
            self.assertEqual(reopened.execute('local_draft', self.params, 'draft-fixture'), first)
            self.assertEqual(reopened.execute('local_draft', self.params | {'content': 'changed'}, 'draft-fixture')['status'], 'CONFLICT')
            writer.assert_not_called()
        self.assertEqual(path.stat().st_mtime_ns, mtime)

    def test_multibyte_content_limit_and_invalid_request_encoding(self):
        self.assertEqual(self.run_draft(self.params | {'content': 'ç' * 250001})['status'], 'ERROR')
        with self.assertRaises(ValueError):
            expectation('\ud800', self.params)

    def test_financial_words_in_private_draft_are_not_a_payment_action(self):
        result = self.run_draft(self.params | {'content': 'payment purchase are just words in this private draft'})
        self.assertEqual(result['status'], 'SUCCESS')
        self.assertFalse(result['result']['delivered'])

    def test_mutating_executor_metadata_cannot_change_expected_output(self):
        actual_write = LocalDraftStore.write
        def dishonest(store, rid, expected):
            altered = expectation(rid, self.params | {'content': 'different'})
            actual_write(store, rid, altered)
            return {'sha256': expected.sha256, 'bytes': len(expected.data), 'ok': True}
        with mock.patch.object(LocalDraftStore, 'write', dishonest):
            result = self.run_draft()
        self.assertEqual(result['status'], 'OUTCOME_MISMATCH')
        self.assertEqual(result['outcome_evidence']['expected_sha256'], hashlib.sha256(self.params['content'].encode()).hexdigest())

    def test_conflicting_existing_file_is_preserved(self):
        store = LocalDraftStore(self.root / 'verified-drafts')
        expected = expectation('draft-fixture', self.params)
        path = store.path('draft-fixture', expected)
        path.parent.mkdir(parents=True)
        path.write_bytes(b'unrelated')
        result = self.run_draft()
        self.assertEqual(result['status'], 'OUTCOME_MISMATCH')
        self.assertEqual(path.read_bytes(), b'unrelated')

    def test_read_failure_is_unknown_and_not_replayed(self):
        with mock.patch.object(LocalDraftStore, 'observe', side_effect=PermissionError('fixture')):
            result = self.run_draft()
        self.assertEqual(result['status'], 'VERIFICATION_UNAVAILABLE')
        with mock.patch.object(LocalDraftStore, 'write') as writer:
            self.assertEqual(self.run_draft(), result)
            writer.assert_not_called()

    def test_symlink_and_directory_cannot_supply_evidence(self):
        store = LocalDraftStore(self.root / 'verified-drafts')
        expected = expectation('draft-fixture', self.params)
        path = store.path('draft-fixture', expected)
        path.parent.mkdir(parents=True)
        path.mkdir()
        self.assertEqual(self.run_draft()['status'], 'VERIFICATION_UNAVAILABLE')
        # Symbolic link tests run on Linux; Windows may lack link privileges.
        if __import__('os').name == 'posix':
            other = self.root / 'outside'
            other.write_bytes(self.params['content'].encode())
            expected2 = expectation('symlink-task', self.params)
            link = store.path('symlink-task', expected2)
            link.parent.mkdir()
            link.symlink_to(other)
            self.assertEqual(self.run_draft(rid='symlink-task')['status'], 'VERIFICATION_UNAVAILABLE')

    def test_root_redirect_is_refused(self):
        if __import__('os').name != 'posix':
            # Windows reparse detection is exercised using actual lstat metadata in production.
            self.assertTrue(LocalDraftStore.is_redirect(mock.Mock(st_mode=0, st_file_attributes=0x400)))
            return
        outside = self.root / 'outside'
        outside.mkdir()
        (self.root / 'verified-drafts').symlink_to(outside, target_is_directory=True)
        self.assertEqual(self.run_draft()['status'], 'VERIFICATION_UNAVAILABLE')
        self.assertEqual(list(outside.iterdir()), [])

    def test_real_workcopy_override_uses_the_same_independent_guard(self):
        source = Path(__file__).with_name('hermes_node.py').read_text(encoding='utf-8')
        cls = next(n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name == 'PabloWorkcopyTaskGuard')
        namespace = {'TaskGuard': TaskGuard, 'get_intent_guard': lambda: None, 'GUI_ACTIONS': set()}
        exec(compile(ast.Module(body=[cls], type_ignores=[]), 'real-workcopy-fixture', 'exec'), namespace)
        live_guard = namespace['PabloWorkcopyTaskGuard'](self.root / 'live.db', {}, 'fixture', lambda: False)
        with mock.patch.object(LocalDraftStore, 'write', return_value={'ok': True, 'verified': True}):
            result = live_guard.execute('local_draft', self.params.copy(), 'live-fixture')
        self.assertFalse(result['ok'])
        self.assertFalse(result['outcome_verified'])
        self.assertEqual(result['status'], 'VERIFICATION_UNAVAILABLE')

    def test_actual_rest_entry_preserves_the_strict_draft_contract(self):
        source = Path(__file__).with_name('hermes_node.py').read_text(encoding='utf-8')
        tree = ast.parse(source)
        selected = [n for n in tree.body if
                    isinstance(n, ast.FunctionDef) and n.name in ('normalize_tool_params', 'execute_request')
                    or isinstance(n, ast.ClassDef) and n.name == 'PabloRequestHandler']
        telegram = mock.Mock()
        namespace = {'json': json, 'ast': ast, 'BaseHTTPRequestHandler': BaseHTTPRequestHandler,
                     'allowed_ip': allowed_ip, 'CONFIG': {'auth_token': 'fixture', 'allowed_ips': ['127.0.0.1']},
                     'task_guard': lambda: self.guard, 'send_telegram_approval_request': telegram}
        exec(compile(ast.Module(body=selected, type_ignores=[]), 'actual-http-entry', 'exec'), namespace)
        handler = namespace['PabloRequestHandler'].__new__(namespace['PabloRequestHandler'])
        handler.path = '/execute'
        handler.client_address = ('127.0.0.1', 12345)
        body = json.dumps({'action': 'local_draft', 'params': self.params, 'request_id': 'rest-fixture'}).encode()
        handler.headers = {'X-Pablo-Token': 'fixture', 'Content-Length': str(len(body))}
        handler.rfile, handler.wfile = io.BytesIO(body), io.BytesIO()
        handler.send_response, handler.send_header, handler.end_headers = mock.Mock(), mock.Mock(), mock.Mock()
        handler.do_POST()
        result = json.loads(handler.wfile.getvalue())
        self.assertEqual(result['status'], 'SUCCESS')
        self.assertTrue(result['outcome_verified'])
        self.assertEqual(Path(result['result']['path']).read_bytes(), self.params['content'].encode())
        telegram.assert_not_called()


if __name__ == '__main__':
    unittest.main()
