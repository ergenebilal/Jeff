import asyncio
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock

ROOT=Path(__file__).parent
sys.path.insert(0,str(ROOT))

def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/(name+'.py'))
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(ignore_cleanup_errors=True);self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        # Bridge import logging must remain inside the isolated directory.
        import logging
        with patch.object(logging,'FileHandler',return_value=logging.NullHandler()):
            self.api=load('jeff_bridge_api')
        self.runner=load('aider_runner')
        self.api.DB_PATH=self.runner.DB_PATH=str(self.root/'bridge.db')
        self.api.BRIDGE_KEY='test-key'
        asyncio.run(self.api.init_db())
        self.coder=self.root/'coder'
        self.coder.write_text('#!/usr/bin/python3\nfrom pathlib import Path\nPath("answer.py").write_text("def add(a,b): return a+b\\n")\nprint("coder fixture")\n')
        self.coder.chmod(0o700)
        self.runner.AIDER_BIN=str(self.coder)
        (self.root/'test_answer.py').write_text('import unittest\nfrom answer import add\nclass Addition(unittest.TestCase):\n def test_add(self): self.assertEqual(add(2,3),5)\n')

    def submit(self,tid='code-1'):
        body=self.api.TaskRequest(task_id=tid,prompt='addition',workspace=str(self.root),files=['answer.py'],
                                  test_argv=[sys.executable,'-m','unittest','discover'])
        return asyncio.run(self.api.create_aider_task(body,'test-key'))

    def run_job(self,tid='code-1'):
        row=asyncio.run(self.api.get_aider_task(tid,'test-key'))
        asyncio.run(self.runner.run_aider_task(row))
        return asyncio.run(self.api.get_aider_task(tid,'test-key'))

    def test_actual_queue_runner_and_verifier(self):
        self.assertEqual(self.submit()['status'],'queued')
        self.assertEqual(self.submit()['task_id'],'code-1')
        result=self.run_job()
        self.assertEqual(result['status'],'verified',result)
        evidence=json.loads(result['result'])
        self.assertEqual(evidence['workspace'],str(self.root))
        self.assertEqual(evidence['test_exit_code'],0)
        self.assertIn('OK',evidence['test_stderr'])
        print('AIDER_QUEUE_E2E: queued -> running -> verified; coder_exit=0 test_exit=0; Ran 1 test / OK')

    def test_failed_verifier_marks_error(self):
        (self.root/'test_answer.py').write_text('import unittest\nclass Failure(unittest.TestCase):\n def test_bad(self): self.fail("expected negative test")\n')
        self.submit()
        result=self.run_job()
        self.assertEqual(result['status'],'error')
        self.assertEqual(json.loads(result['result'])['test_exit_code'],1)
        print('AIDER_QUEUE_NEGATIVE: test_exit=1 status=error')

    def test_same_id_changed_contract_rejected(self):
        self.submit()
        body=self.api.TaskRequest(task_id='code-1',prompt='changed',workspace=str(self.root),files=[],test_argv=['true'])
        with self.assertRaises(self.api.HTTPException) as exc:
            asyncio.run(self.api.create_aider_task(body,'test-key'))
        self.assertEqual(exc.exception.status_code,409)

    def test_missing_workspace_never_launches_coder(self):
        with sqlite3.connect(self.api.DB_PATH) as db:
            db.execute("INSERT INTO tasks(task_id,prompt,files,status) VALUES('legacy','old','x','queued')")
        result=self.run_job('legacy')
        self.assertEqual(result['status'],'error')
        self.assertFalse((self.root/'answer.py').exists())

    def test_result_is_not_redelivered_as_task(self):
        body=self.api.AlfredTaskRequest(task_id='win1',type='ping',payload={})
        asyncio.run(self.api.create_alfred_task(body,'test-key'))
        claimed=asyncio.run(self.api.alfred_get_tasks(1,'test-key','fixture-worker'))['tasks'][0]
        result=self.api.AlfredResult(task_id='win1',type='ping',status='ERROR',ok=False,
                                     request_id='win1',result='test error',digest=claimed['digest'],
                                     worker_id='fixture-worker',attempt=claimed['attempt'])
        asyncio.run(self.api.alfred_result(result,'test-key'))
        latest=asyncio.run(self.api.alfred_task_status('win1','test-key'))
        self.assertEqual(latest['status'],'unverified')
        with sqlite3.connect(self.api.DB_PATH) as db:
            self.assertEqual(db.execute("SELECT count(*) FROM alfred_events WHERE status='pending'").fetchone()[0],0)

    def test_path_escape_rejected(self):
        body=self.api.TaskRequest(task_id='escape',prompt='edit',workspace=str(self.root),files=['../escape.py'],test_argv=['true'])
        with self.assertRaises(self.api.HTTPException) as exc:
            asyncio.run(self.api.create_aider_task(body,'test-key'))
        self.assertEqual(exc.exception.status_code,422)


if __name__=='__main__':
    unittest.main(verbosity=2)
