import ast
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch, Mock

import pablo_antigravity as ag
from pablo_task_guard import TaskGuard, is_approval_required

class AntigravityBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.script=self.root/'fixture.py'; self.script.write_text('print(1)')

    def test_every_alias_needs_approval(self):
        for alias in ag.ALIASES:
            self.assertTrue(is_approval_required(alias,{'prompt':'fixture'})[0])

    def test_code_change_blocks_execution(self):
        with patch.object(ag,'DESIGNER',self.script),patch.object(ag.subprocess,'run') as run:
            params=ag.prepare({'prompt':'post fixture'})
            self.script.write_text('print(2)')
            self.assertEqual(ag.execute(params)['status'],'BLOCKED')
        run.assert_not_called()

    def test_zero_exit_is_execution_only_and_timeout_needs_reconciliation(self):
        with patch.object(ag,'DESIGNER',self.script):
            params=ag.prepare({'prompt':'post fixture'})
            with patch.object(ag.subprocess,'run',return_value=Mock(returncode=0,stdout='fixture',stderr='')):
                result=ag.execute(params)
                self.assertEqual(result['status'],'EXECUTION_SUCCEEDED'); self.assertFalse(result['verified']); self.assertFalse(result['delivered'])
            with patch.object(ag.subprocess,'run',side_effect=ag.subprocess.TimeoutExpired('fixture',180)):
                self.assertEqual(ag.execute(params)['status'],'PENDING_VERIFICATION')

    def test_aliases_share_request_identity_and_execute_once(self):
        action=Mock(return_value={'ok':True,'status':'EXECUTION_SUCCEEDED','result':{'exit_code':0}})
        guard=TaskGuard(self.root/'guard.db',{'antigravity':action},42,lambda:True)
        with patch.object(ag,'DESIGNER',self.script):
            first=guard.execute('antigravity_post',{'prompt':'post fixture'},'one')
            second=guard.execute('run_antigravity',{'prompt':'post fixture'},'one')
            self.assertEqual(first['approval_id'],second['approval_id'])
            guard.approve(first['approval_id'],42,42); guard.approve(first['approval_id'],42,42)
        self.assertEqual(action.call_count,1)

    def test_concurrent_desktop_actions_are_serialized(self):
        active=[0]; peak=[0]; lock=threading.Lock()
        def action(params):
            with lock: active[0]+=1; peak[0]=max(peak[0],active[0])
            time.sleep(.03)
            with lock: active[0]-=1
            return {'ok':True}
        guard=TaskGuard(self.root/'serial.db',{'window_focus':action},42,lambda:True)
        threads=[threading.Thread(target=guard.execute,args=('window_focus',{},str(i))) for i in range(4)]
        [t.start() for t in threads]; [t.join() for t in threads]
        self.assertEqual(peak[0],1)

    def test_real_node_antigravity_handler_calls_bound_executor(self):
        tree=ast.parse(Path(__file__).with_name('hermes_node.py').read_text(encoding='utf-8'))
        fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='action_antigravity')
        scope={}; exec(compile(ast.Module(body=[fn],type_ignores=[]),'node-fixture','exec'),scope)
        with patch.object(ag,'execute',return_value={'status':'fixture'}) as run:
            self.assertEqual(scope['action_antigravity']({'fixture':True})['status'],'fixture')
        run.assert_called_once_with({'fixture':True})
