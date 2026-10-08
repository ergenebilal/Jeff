"""Real HTTP on the production handler AST; no GUI, node workers or real journal."""
import ast
from contextlib import closing
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import Mock
import urllib.error
import urllib.parse
import urllib.request

from pablo_task_guard import TaskGuard, allowed_ip
from pablo_outcome_observer import observe_current
from pablo_task_criterion import read_criterion


class ObservationHTTPTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.root=Path(directory.name);self.journal=self.root/'task-journal.sqlite3'
        guard=TaskGuard(self.journal,{},'fixture',lambda:False)
        guard.execute('local_draft',{'name':'proof','content':'private bytes','format':'txt'},'fixture')
        source=ast.parse(Path(__file__).with_name('hermes_node.py').read_text(encoding='utf-8'))
        handler=next(n for n in source.body if isinstance(n,ast.ClassDef) and n.name=='PabloRequestHandler')
        self.reader=Mock(wraps=observe_current)
        self.guard_constructor=Mock(side_effect=AssertionError('GET must never initialize a guard'))
        self.ns={'BaseHTTPRequestHandler':BaseHTTPRequestHandler,'allowed_ip':allowed_ip,
                 'CONFIG':{'auth_token':'fixture-key','allowed_ips':['127.0.0.1']},
                 'NODE_DIR':self.root,'observe_current':self.reader,'task_guard':self.guard_constructor,
                 'urllib':urllib,'json':json,'re':re,'read_criterion':Mock(wraps=read_criterion)}
        exec(compile(ast.Module(body=[handler],type_ignores=[]),'<production handler>','exec'),self.ns)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),self.ns['PabloRequestHandler'])
        self.server.daemon_threads=True
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.addCleanup(self.stop)

    def stop(self):
        self.server.shutdown();self.server.server_close();self.thread.join(2)

    def get(self,path='/tasks/fixture/observation',key='fixture-key',method='GET'):
        headers={} if key is None else {'X-Bridge-Key':key}
        req=urllib.request.Request('http://127.0.0.1:'+str(self.server.server_port)+path,
                                   headers=headers,method=method)
        try:
            with urllib.request.urlopen(req,timeout=3) as response:return response.status,response.read()
        except urllib.error.HTTPError as error:return error.code,error.read()

    def journal_snapshot(self):
        with closing(sqlite3.connect(self.journal)) as db:
            return {r[0]:list(db.execute('SELECT * FROM "'+r[0]+'"')) for r in
                    db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}

    def test_real_get_observes_without_constructor_events_content_or_paths(self):
        before=self.journal_snapshot();code,raw=self.get();result=json.loads(raw)
        self.assertEqual(code,200);self.assertEqual(result['status'],'matched')
        self.assertNotIn(b'private bytes',raw);self.assertNotIn(str(self.root).encode(),raw)
        self.assertEqual(before,self.journal_snapshot());self.guard_constructor.assert_not_called()
        self.reader.assert_called_once_with(self.journal,'fixture')

    def test_missing_wrong_or_unconfigured_key_refuses_before_reader(self):
        for key in (None,'wrong'):
            self.assertEqual(self.get(key=key)[0],401)
        self.ns['CONFIG']['auth_token']=''
        self.assertEqual(self.get()[0],401);self.reader.assert_not_called()

    def test_ip_guard_refuses_before_auth_or_file_observation(self):
        self.ns['allowed_ip']=lambda *args:False
        self.assertEqual(self.get()[0],403);self.reader.assert_not_called()

    def test_query_paths_encoded_separators_and_invalid_ids_cannot_select_a_file(self):
        for path in ('/tasks/fixture/observation?path=outside',
                     '/tasks/../observation','/tasks/%2E%2E/observation',
                     '/tasks/a%2Fb/observation','/tasks//observation',
                     '/tasks/'+'a'*129+'/observation'):
            with self.subTest(path=path):self.assertEqual(self.get(path)[0],400)
        self.reader.assert_not_called();self.guard_constructor.assert_not_called()

    def test_missing_task_is_read_only_and_post_cannot_observe_or_execute(self):
        before=self.journal_snapshot()
        code,raw=self.get('/tasks/missing/observation')
        self.assertEqual(code,200);self.assertEqual(json.loads(raw)['status'],'unavailable')
        self.assertEqual(self.get(method='POST')[0],404)
        self.assertEqual(before,self.journal_snapshot());self.guard_constructor.assert_not_called()

    def test_criterion_get_reads_original_input_without_private_data_or_mutation(self):
        before=self.journal_snapshot();code,raw=self.get('/tasks/fixture/criterion')
        self.assertEqual(code,200);self.assertEqual(json.loads(raw)['status'],'available')
        self.assertNotIn(b'private bytes',raw);self.assertNotIn(str(self.root).encode(),raw)
        self.assertEqual(before,self.journal_snapshot());self.guard_constructor.assert_not_called()

    def test_criterion_missing_wrong_key_and_foreign_ip_are_rejected_before_read(self):
        for key in (None,'wrong'):self.assertEqual(self.get('/tasks/fixture/criterion',key=key)[0],401)
        self.ns['allowed_ip']=lambda *args:False
        self.assertEqual(self.get('/tasks/fixture/criterion')[0],403)
        self.ns['read_criterion'].assert_not_called()

    def test_criterion_query_and_encoded_paths_cannot_select_other_files(self):
        for path in ('/tasks/fixture/criterion?path=outside','/tasks/a%2Fb/criterion',
                     '/tasks/../criterion','/tasks/'+'x'*129+'/criterion'):
            self.assertEqual(self.get(path)[0],400)
        self.ns['read_criterion'].assert_not_called();self.guard_constructor.assert_not_called()

    def test_criterion_missing_and_post_do_not_write_or_execute(self):
        before=self.journal_snapshot();code,raw=self.get('/tasks/missing/criterion')
        self.assertEqual(code,200);self.assertEqual(json.loads(raw)['status'],'unavailable')
        self.assertEqual(self.get('/tasks/fixture/criterion',method='POST')[0],404)
        self.assertEqual(before,self.journal_snapshot());self.guard_constructor.assert_not_called()


if __name__=='__main__':unittest.main()
