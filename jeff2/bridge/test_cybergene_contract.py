"""No production requests, model calls, Telegram sends or real GUI actions."""
import asyncio
import contextlib
import ctypes
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import Mock, patch, AsyncMock

ROOT = Path(os.environ.get('CYBERGENE_TEST_SOURCE', Path(__file__).parent))
sys.path.insert(0, str(ROOT))
from pablo_task_guard import TaskGuard, allowed_ip
from verified_coding import run as run_coding


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.action = Mock(return_value={'ok': True, 'result': {'exit_code': 0}})
        self.clock = [100.0]
        self.ready = Mock(return_value=True)
        self.guard = TaskGuard(Path(self.tmp.name)/'state.db', {'shell': self.action, 'ping': self.action,
            'gui_click': self.action}, 42, self.ready, clock=lambda:self.clock[0], ttl=10)

    def pending(self, action='shell'):
        result = self.guard.execute(action, {'command': 'test'}, 'r1')
        self.assertEqual(result['status'], 'APPROVAL_REQUIRED')
        self.action.assert_not_called()
        return result['approval_id']

    def test_wrong_user_and_chat(self):
        aid = self.pending()
        for user, chat in [(7,42),(42,7)]:
            self.assertEqual(self.guard.approve(aid,user,chat)['status'], 'REJECTED')
        self.action.assert_not_called()

    def test_expiry_and_replay(self):
        aid = self.pending()
        self.clock[0] = 111
        self.assertEqual(self.guard.approve(aid,42,42)['status'], 'REJECTED')
        self.action.assert_not_called()

    def test_single_use_and_durable_idempotency(self):
        aid = self.pending()
        self.assertTrue(self.guard.approve(aid,42,42)['ok'])
        self.assertEqual(self.guard.approve(aid,42,42)['status'], 'REJECTED')
        reopened = TaskGuard(self.guard.path, self.guard.actions,42,self.ready)
        self.assertTrue(reopened.execute('shell',{'command':'test'},'r1')['ok'])
        self.assertEqual(self.action.call_count,1)

    def test_changed_content_rejected(self):
        self.pending()
        self.assertEqual(self.guard.execute('shell',{'command':'different'},'r1')['status'],'CONFLICT')
        self.action.assert_not_called()

    def test_tampered_pending_record_rejected(self):
        aid = self.pending()
        with self.guard.connect() as db:
            db.execute('UPDATE requests SET params=?', ('{"command":"changed"}',))
        self.assertEqual(self.guard.approve(aid,42,42)['status'],'REJECTED')
        self.action.assert_not_called()

    def test_active_desktop_blocks_even_approved_action(self):
        aid = self.pending('gui_click')
        self.ready.return_value=False
        result=self.guard.approve(aid,42,42)
        self.assertEqual(result['status'],'BLOCKED')
        self.action.assert_not_called()

    def test_read_action_also_checks_desktop(self):
        self.guard.actions['screenshot']=self.action
        self.ready.return_value=False
        self.assertEqual(self.guard.execute('screenshot',{},'r2')['status'],'BLOCKED')
        self.action.assert_not_called()

    def test_ip_exact_allowlist(self):
        self.assertTrue(allowed_ip('100.124.217.48',['100.124.217.48']))
        for ip in ('100.1.2.3','100.124.217.49','203.0.113.2'):
            self.assertFalse(allowed_ip(ip,['100.124.217.48']))

    def test_action_error_is_not_success(self):
        self.action.return_value={'ok':True,'result':{'exit_code':3}}
        self.assertEqual(self.guard.execute('ping',{},'r')['status'],'ERROR')

    def test_outbox_survives_send_failure(self):
        self.guard.queue_result({'task_id':'r','status':'ERROR'})
        self.guard.flush_results(Mock(side_effect=OSError()))
        sender=Mock()
        self.guard.flush_results(sender)
        sender.assert_called_once()
        self.guard.flush_results(sender)
        self.assertEqual(sender.call_count,1)


class CodingTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.coder=self.root/'fixture_coder.py'
        self.coder.write_text("from pathlib import Path\nPath('answer.py').write_text('def add(a,b): return a+b\\n')\nprint('fixture coder wrote answer.py')\n")
        (self.root/'test_answer.py').write_text('import unittest\nfrom answer import add\nclass Contract(unittest.TestCase):\n def test_add(self): self.assertEqual(add(2,3),5)\n')

    def test_gateway_coding_delegate_test_evidence_end_to_end(self):
        args=[sys.executable,'-m','unittest','discover','-v']
        result=run_coding(str(self.root),'coding-1','Implement addition',args,coder_argv=[sys.executable,str(self.coder)])
        self.assertEqual(result['status'],'VERIFIED')
        self.assertEqual(result['verification']['exit_code'],0)
        self.assertIn('OK',result['verification']['stderr'])
        self.assertEqual(result['workspace'],str(self.root))
        print('E2E_CODING: delegate=SUCCESS test_exit=0 status=VERIFIED; Ran 1 test / OK')
        self.coder.write_text('raise RuntimeError("must not rerun")')
        self.assertEqual(run_coding(str(self.root),'coding-1','Implement addition',args)['status'],'VERIFIED')

    def test_failed_test_never_seals(self):
        (self.root/'test_answer.py').write_text('import unittest\nclass Contract(unittest.TestCase):\n def test_failure(self): self.assertEqual(1,2)\n')
        result=run_coding(str(self.root),'coding-fail','Implement addition',[sys.executable,'-m','unittest','discover'],coder_argv=[sys.executable,str(self.coder)])
        self.assertEqual(result['status'],'ERROR')
        self.assertEqual(result['verification']['exit_code'],1)
        print('E2E_TEST_FAILURE: test_exit=1 status=ERROR; FAILED (failures=1)')

    def test_coder_timeout_retains_task(self):
        result=run_coding(str(self.root),'slow','Wait',[sys.executable,'-m','unittest'],timeout=.1,
                         coder_argv=[sys.executable,'-c','import time; time.sleep(5)'])
        self.assertEqual(result['status'],'TIMEOUT')
        self.assertEqual(result['steps']['verify'],'pending')

    def test_existing_aider_route_is_preserved(self):
        with patch('verified_coding.execute', return_value={'exit_code':0,'status':'SUCCESS','stdout':'','stderr':'OK'}) as execute:
            result=run_coding(str(self.root),'aider-route','Implement addition',[sys.executable,'-m','unittest'],engine='aider')
        args=execute.call_args_list[0]
        self.assertTrue(args.args[0][0].endswith('/.local/bin/aider'))
        self.assertIn('openai/claude-3-5-sonnet-latest',args.args[0])
        self.assertEqual(args.kwargs['env']['OPENAI_API_BASE'],'http://127.0.0.1:8999/v1')
        self.assertEqual(result['engine'],'aider')


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        constants=types.ModuleType('hermes_constants')
        constants.get_hermes_home=lambda:self.root/'home'
        self.patches=patch.dict(sys.modules,{'hermes_constants':constants})
        self.patches.start()
        self.addCleanup(self.patches.stop)
        self.client=load('alfred_tool',ROOT/'alfred_tool.py')
        # Real Pablo HTTP handler; only platform/GUI and external message boundaries are replaced.
        shutil.copy2(ROOT/'hermes_node.py',self.root/'hermes_node.py')
        modules={name:Mock() for name in ['win32gui','win32con','win32process','pyautogui','mss','mss.tools','PIL','PIL.Image','PIL.ImageGrab']}
        with patch.dict(sys.modules,modules), patch.object(ctypes,'windll',Mock(),create=True):
            self.node=load('pablo_test_node',self.root/'hermes_node.py')
        self.node.CONFIG.update(auth_token='test-only',telegram_default_chat_id=42,allowed_ips=[])
        self.node.send_telegram_approval_request=Mock()
        self.node.desktop_ready=Mock(return_value=False)
        self.node.ACTIONS['ping']=Mock(return_value={'ok':True,'result':{'message':'pong'}})
        self.server=self.node.HTTPServer(('127.0.0.1',0),self.node.PabloRequestHandler)
        self.worker=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.worker.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.client.ALFRED_BASE_URL='http://127.0.0.1:'+str(self.server.server_port)
        self.client.BRIDGE_KEY='test-only'

    def test_real_http_jeff_to_pablo_and_reconcile(self):
        result=self.client.execute('ping',{},request_id='http-1')
        self.assertTrue(result['ok'],result)
        self.assertEqual(result['request_id'],'http-1')
        self.assertTrue(self.client.execute('ping',{},request_id='http-1')['ok'])
        self.assertEqual(self.node.ACTIONS['ping'].call_count,1)
        print('E2E_BRIDGE: request_id=http-1 status=SUCCESS executions=1')

    def test_real_http_approval_required(self):
        self.node.ACTIONS['shell']=Mock()
        result=self.client.execute('shell',{'command':'test'},request_id='approval-http')
        self.assertEqual(result['status'],'APPROVAL_REQUIRED')
        self.assertFalse(result['ok'])
        self.node.ACTIONS['shell'].assert_not_called()

    def test_real_http_timeout_is_reconciled_not_replayed(self):
        import time
        def slow(params):
            time.sleep(.15)
            return {'ok':True,'result':{'message':'pong'}}
        self.node.ACTIONS['ping']=Mock(side_effect=slow)
        self.assertEqual(self.client.execute('ping',{},timeout=.03,request_id='slow-http')['status'],'TIMEOUT')
        time.sleep(.25)
        result=self.client.execute('ping',{},request_id='slow-http')
        self.assertTrue(result['ok'],result)
        self.assertEqual(self.node.ACTIONS['ping'].call_count,1)
        print('E2E_TIMEOUT: TIMEOUT -> reconciled SUCCESS; executions=1')

    def test_offline_retained(self):
        import requests
        with patch.object(self.client,'get_session') as session:
            session.return_value.post.side_effect=requests.exceptions.ConnectionError()
            result=self.client.execute('ping',{},request_id='offline')
        self.assertEqual(result['status'],'OFFLINE')
        records=list((self.root/'home'/'pablo-requests').glob('*.json'))
        self.assertEqual(len(records),1)
        self.assertEqual(json.loads(records[0].read_text())['response']['request_id'],'offline')

    def test_bridge_unknown_action_is_error_not_generic_success(self):
        self.node.send_bridge_result=Mock()
        self.node.handle_bridge_task({'task_id':'unknown','type':'unknown','payload':'{}'})
        sent=self.node.send_bridge_result.call_args.args[0]
        self.assertEqual(sent['status'],'ERROR')

    def test_cli_failure_exit_status(self):
        with patch.object(sys,'argv',['alfred','--request-id','cli','shell','test']):
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(self.client.main(),1)


class JeffTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        constants=types.ModuleType('hermes_constants')
        constants.get_hermes_home=lambda:self.root
        fake_client=types.ModuleType('alfred_tool')
        import contextvars
        fake_client.request_context=contextvars.ContextVar('request',default=None)
        fake_client.last_response=contextvars.ContextVar('response',default=None)
        modules={'hermes_constants':constants,'alfred_tool':fake_client}
        # Telegram types are inert; handle_message itself is still the real production function.
        telegram=types.ModuleType('telegram'); telegram.Update=object
        extension=types.ModuleType('telegram.ext')
        for n in ('Application','MessageHandler','CommandHandler','filters','ContextTypes'):
            setattr(extension,n,Mock())
        modules.update({'telegram':telegram,'telegram.ext':extension})
        patches=patch.dict(sys.modules,modules); patches.start(); self.addCleanup(patches.stop)
        self.bot=load('jeff_test_bot',ROOT/'telegram_claude_bot.py')
        self.bot.alfred=None
        self.task=self.bot.TaskState('jeff-1','test code',42)
        self.bot.active_tasks[42]=self.task

    def test_nonzero_shell_and_forged_evidence_block_completion(self):
        text,_,_=self.bot.execute_tool_call('run_linux_command',{'command':"python3 -c 'raise SystemExit(7)'"},has_active_task=True,task_obj=self.task)
        self.assertIn('[TOOL_RESULT: ERROR]',text)
        evidence=self.task.evidence[-1]['id']
        text,_,rejected=self.bot.execute_tool_call('complete_task',{'summary':'done','verification_evidence':'trust me','evidence_ids':[evidence]},has_active_task=True,task_obj=self.task)
        self.assertTrue(rejected)
        self.assertNotEqual(self.task.status,'SUCCESS')
        print('JEFF_FAILURE_GATE: ExitCode=7 -> completion refused')

    def test_task_reload_retains_failed_evidence(self):
        self.bot.execute_tool_call('run_linux_command',{'command':'false'},has_active_task=True,task_obj=self.task)
        self.bot.active_tasks.clear()
        loaded=self.bot.load_task_state(42)
        self.assertFalse(loaded.evidence[-1]['ok'])
        self.assertEqual(loaded.goal,'test code')

    def test_text_only_model_claim_does_not_complete(self):
        bot=self.bot
        bot.call_antigravity=AsyncMock(return_value={'choices':[{'message':{'content':'All fixed successfully'}}]})
        bot.build_system_prompt=lambda **kw:'test'
        bot.TaskStatusIndicator=Mock(return_value=types.SimpleNamespace(update=AsyncMock(),finalize=AsyncMock(return_value=True)))
        message=types.SimpleNamespace(text='test code',document=None,photo=None,audio=None,voice=None,chat=Mock(),reply_text=AsyncMock())
        update=types.SimpleNamespace(message=message,effective_user=types.SimpleNamespace(id=42,username='test'))
        asyncio.run(bot.handle_message(update,Mock()))
        self.assertEqual(bot.active_tasks[42].status,'TASK_PAUSED')

    def test_model_failure_preserves_state(self):
        bot=self.bot
        bot.call_antigravity=AsyncMock(side_effect=RuntimeError('model unavailable'))
        bot.build_system_prompt=lambda **kw:'test'
        bot.TaskStatusIndicator=Mock(return_value=types.SimpleNamespace(update=AsyncMock(),finalize=AsyncMock(return_value=True)))
        message=types.SimpleNamespace(text='test code',document=None,photo=None,audio=None,voice=None,chat=Mock(),reply_text=AsyncMock())
        update=types.SimpleNamespace(message=message,effective_user=types.SimpleNamespace(id=42,username='test'))
        asyncio.run(bot.handle_message(update,Mock()))
        self.assertEqual(bot.load_task_state(42).status,'TASK_PAUSED')


if __name__=='__main__':
    unittest.main(verbosity=2)
