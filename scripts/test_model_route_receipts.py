import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

PLUGIN=Path(__file__).resolve().parents[1]/'integrations/model-route-receipts/__init__.py'
spec=importlib.util.spec_from_file_location('route_receipts',PLUGIN)
receipts=importlib.util.module_from_spec(spec); spec.loader.exec_module(receipts)

class RouteReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)/'state.db'
        self.store=receipts.ReceiptStore(self.path,clock=lambda:1234)
        self.data={'session_id':'a','turn_id':'turn','api_request_id':'call','provider':'opencode-go',
                   'model':'fixture','base_url':'https://SECRET@host.example/v1?key=SECRET'}

    def rows(self):
        with sqlite3.connect(self.path) as db:
            db.row_factory=sqlite3.Row
            return [dict(r) for r in db.execute('SELECT * FROM model_route_receipts ORDER BY rowid')]

    def test_actual_attempt_primary_then_fallback_and_secret_redaction(self):
        self.store.pre(self.data); self.store.finish(dict(self.data,error={'type':'URLError','message':'SECRET'}),'failed')
        fallback=dict(self.data,provider='proxy',model='spare')
        self.store.pre(fallback); self.store.finish(fallback,'succeeded')
        rows=self.rows(); self.assertEqual(len(rows),2)
        self.assertEqual(rows[1]['requested_route'],'opencode-go')
        self.assertEqual(rows[1]['actual_route'],'proxy')
        self.assertEqual(rows[1]['fallback_reason'],'URLError')
        self.assertEqual(rows[1]['fallback_used'],1)
        self.assertNotIn('SECRET',json.dumps(rows))

    def test_no_inferred_fallback_without_a_failed_attempt(self):
        self.store.pre(dict(self.data,provider='proxy'))
        self.assertEqual(self.rows()[0]['fallback_used'],0)

    def test_sessions_do_not_cross_and_restart_preserves_receipt(self):
        self.store.pre(self.data)
        other=dict(self.data,session_id='b',provider='proxy')
        self.store.pre(other); self.store.finish(other,'failed')
        restarted=receipts.ReceiptStore(self.path); restarted.finish(self.data,'succeeded')
        self.assertEqual([r['status'] for r in self.rows()],['succeeded','failed'])

    def test_unknown_empty_response_and_late_error_do_not_pass(self):
        with patch.object(receipts,'_store',return_value=self.store):
            receipts.pre(**self.data); receipts.post(**self.data,assistant_content_chars=0)
            self.assertEqual(self.rows()[0]['status'],'unknown')
            receipts.error(**self.data,error={'type':'InvalidResponse'})
        self.assertEqual(self.rows()[0]['status'],'failed')

    def test_write_failure_never_raises_into_model_path(self):
        with patch.object(receipts,'_store',side_effect=OSError('SECRET')):
            receipts.pre(**self.data); receipts.post(**self.data); receipts.error(**self.data)

    def test_observed_hooks_register_without_tools_or_prompt_changes(self):
        class Context:
            hooks={}
            def register_hook(self,name,fn): self.hooks[name]=fn
        ctx=Context(); receipts.register(ctx)
        with patch.object(receipts,'_store',return_value=self.store):
            ctx.hooks['pre_api_request'](**self.data)
            ctx.hooks['post_api_request'](**self.data,assistant_content_chars=2,finish_reason='stop')
        self.assertEqual(self.rows()[0]['status'],'succeeded')
