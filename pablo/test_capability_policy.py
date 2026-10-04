import ast
from pathlib import Path
import tempfile
import json
import unittest
from unittest.mock import Mock
from pablo_task_guard import TaskGuard,fingerprint
from pablo_capability_policy import admission,LEGACY_ACTIONS,ACCEPTED_CONTRACTS
from pablo_brain import PabloBrain


class AdmissionTests(unittest.TestCase):
    def test_existing_node_actions_are_explicitly_declared(self):
        tree=ast.parse(Path(__file__).with_name('hermes_node.py').read_text(encoding='utf-8'))
        table=next(n.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='ACTIONS' for t in n.targets))
        self.assertEqual({key.value for key in table.keys},set(LEGACY_ACTIONS))

    def test_unaccepted_action_cannot_execute_or_create_approval(self):
        with tempfile.TemporaryDirectory() as root:
            action=Mock(return_value={'ok':True});approvals=Mock()
            guard=TaskGuard(Path(root)/'journal',{'future_tool':action},42,lambda:True,approvals=approvals,capability_policy=admission)
            result=guard.execute('future_tool',{'admitted':True,'contract':{'accepted':True}},'new')
            self.assertEqual(result['status'],'CAPABILITY_NOT_ADMITTED')
            action.assert_not_called();approvals.request.assert_not_called()
            with guard.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM requests').fetchone()[0],0)

    def test_legacy_success_does_not_gain_outcome_authority(self):
        with tempfile.TemporaryDirectory() as root:
            action=Mock(return_value={'ok':True,'outcome_verified':True,'result':{'ok':True,'outcome_verified':True}})
            guard=TaskGuard(Path(root)/'journal',{'shell':action},42,lambda:True,capability_policy=admission)
            result=guard.execute('shell',{'cmd':'echo fixture'},'one')
            self.assertTrue(result['worker_action_succeeded']);self.assertFalse(result['outcome_verified']);self.assertFalse(result['completion_authority'])
            self.assertEqual(guard.execute('shell',{'cmd':'echo fixture'},'one'),result);self.assertEqual(action.call_count,1)

    def test_policy_exception_closed_and_draft_contract_complete(self):
        with tempfile.TemporaryDirectory() as root:
            action=Mock();guard=TaskGuard(Path(root)/'journal',{'shell':action},42,lambda:True,capability_policy=lambda action:(_ for _ in ()).throw(ValueError()))
            self.assertEqual(guard.execute('shell',{},'one')['status'],'CAPABILITY_NOT_ADMITTED');action.assert_not_called()
        for name,contract in ACCEPTED_CONTRACTS.items():
            self.assertTrue(admission(name)['admitted'])
            self.assertTrue(all(contract[k] for k in ('approval_boundary','outcome_contract','recovery','acceptance_tests')))

    def test_model_feedback_cannot_promote_nested_or_string_outcome_flags(self):
        for result in ({'outcome_verified':'false'}, {'outcome_verified':False,'result':{'outcome_verified':True}},
                       {'outcome_verified':True,'completion_authority':False}):
            seen=[];brain=PabloBrain()
            def reply(messages):
                if not seen:seen.append('first');return 'TOOL: {"tool":"window_list","params":{}}'
                seen.append(str(messages));return 'Görünen kayıt okundu.'
            brain._call_llm=reply
            brain.think_and_respond('fixture',tool_executor=lambda n,p:{'ok':True,'status':'SUCCESS',**result})
            self.assertNotIn('AYRI KANITLA doğrulandı',seen[-1])

    def test_old_approval_cannot_enable_a_future_unaccepted_action(self):
        with tempfile.TemporaryDirectory() as root:
            action=Mock();guard=TaskGuard(Path(root)/'journal',{'future_tool':action},42,lambda:True,clock=lambda:100,capability_policy=admission)
            response=guard.response('old','APPROVAL_REQUIRED',approval_id='approval')
            with guard.connect() as db:
                db.execute('INSERT INTO requests(id,digest,action,params,status,response,approval,expires) VALUES(?,?,?,?,?,?,?,?)',
                           ('old',fingerprint('future_tool',{}),'future_tool','{}','APPROVAL_REQUIRED',json.dumps(response),'approval',200))
            self.assertEqual(guard.approve('approval',42,42)['status'],'CAPABILITY_NOT_ADMITTED')
            action.assert_not_called()
            with guard.connect() as db:self.assertEqual(db.execute('SELECT consumed,status FROM requests').fetchone(),(0,'APPROVAL_REQUIRED'))
            self.assertEqual(guard.approve('approval',42,42,reject=True)['status'],'REJECTED')
            action.assert_not_called()
