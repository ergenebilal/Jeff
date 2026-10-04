"""Restart uncertainty never replays generic work or edits its original claim."""
import ast
import contextlib
import io
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock
from pablo_task_guard import TaskGuard,fingerprint


class RuntimeInterruptionTests(unittest.TestCase):
    def test_restart_receipt_preserves_original_and_marks_only_prior_dated_generic_claims(self):
        with tempfile.TemporaryDirectory() as directory:
            guard=TaskGuard(Path(directory)/'journal.db',{},'',lambda:False,clock=lambda:1000)
            params={'fixture':True}
            with guard.connect() as db:
                for rid,action,created in [('old','screenshot',500),('legacy','shell',None),('current','screenshot',950),('draft','local_draft',500)]:
                    db.execute('INSERT INTO requests(id,digest,action,params,status,response,created_at) VALUES(?,?,?,?,?,?,?)',
                               (rid,fingerprint(action,params),action,json.dumps(params),'IN_PROGRESS',json.dumps(guard.response(rid,'IN_PROGRESS')),created))
                before=db.execute('SELECT * FROM requests ORDER BY id').fetchall()
            guard.note_restart(900)
            self.assertEqual(guard.get('old')['status'],'OUTCOME_UNKNOWN')
            self.assertEqual(guard.work_status('old')['phase'],'outcome_unknown_after_restart')
            self.assertFalse(guard.get('old')['outcome_verified'])
            with mock.patch.object(guard,'_run',side_effect=AssertionError('replay')):
                self.assertEqual(guard.execute('screenshot',params,'old')['status'],'OUTCOME_UNKNOWN')
                self.assertEqual(guard.reconcile('old')['status'],'OUTCOME_UNKNOWN')
            for rid in ('legacy','current','draft'):self.assertEqual(guard.get(rid)['status'],'IN_PROGRESS')
            with guard.connect() as db:self.assertEqual(db.execute('SELECT * FROM requests ORDER BY id').fetchall(),before)

    def test_invalid_restart_instant_cannot_forge_a_runtime_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            guard=TaskGuard(Path(directory)/'journal.db',{},'',lambda:False,clock=lambda:1000)
            for value in (True,float('nan'),-1,1001):
                with self.subTest(value=str(value)),self.assertRaises(ValueError):guard.note_restart(value)

    def test_real_node_main_binds_before_receipts_and_threads_and_duplicate_cannot_start(self):
        tree=ast.parse(Path(__file__).with_name('hermes_node.py').read_text(encoding='utf-8'))
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        events=[]
        server=mock.Mock();server.serve_forever.side_effect=lambda:events.append('serve')
        server.server_close.side_effect=lambda:events.append('close')
        def bind(*args):events.append('bind');return server
        class Thread:
            def __init__(self,**kw):pass
            def start(self):events.append('thread')
        guard=mock.Mock();guard.note_restart.side_effect=lambda _:events.append('restart_receipt')
        ns={'CONFIG':{'version':'fixture','listen_host':'127.0.0.1','listen_port':1234,'jeff_bridge_api_url':'fixture'},
            'ThreadingHTTPServer':bind,'PabloRequestHandler':object,'task_guard':lambda:guard,'PROCESS_STARTED_AT':900,
            'threading':types.SimpleNamespace(Thread=Thread),'run_bridge_worker':mock.Mock(),'run_telegram_worker':mock.Mock(),
            'run_tailscale_watchdog':mock.Mock(),'log':mock.Mock()}
        exec(compile(ast.Module(body=[fn],type_ignores=[]),'real-node-startup','exec'),ns)
        with contextlib.redirect_stdout(io.StringIO()):ns['main']()
        self.assertEqual(events[:2],['bind','restart_receipt']);self.assertEqual(events.count('thread'),3)
        events.clear();ns['ThreadingHTTPServer']=mock.Mock(side_effect=OSError('bound'))
        with contextlib.redirect_stdout(io.StringIO()),self.assertRaises(OSError):ns['main']()
        self.assertEqual(events,[])


if __name__=='__main__':unittest.main()
