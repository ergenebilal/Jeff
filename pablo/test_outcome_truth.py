import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock
from pablo_task_guard import TaskGuard
from pablo_capability_policy import admission
from pablo_brain import PabloBrain


class OutcomeTruthTests(unittest.TestCase):
    def test_live_policy_worker_success_is_not_completion_or_repeat(self):
        with tempfile.TemporaryDirectory() as root:
            action=Mock(return_value={'ok':True,'status':'SUCCESS','outcome_verified':True,'result':{'exit_code':0}})
            guard=TaskGuard(Path(root)/'journal',{'shell':action},42,lambda:True,capability_policy=admission)
            result=guard.execute('shell',{'cmd':'echo fixture'},'one')
            self.assertEqual(result['status'],'EXECUTION_SUCCEEDED');self.assertFalse(result['ok'])
            self.assertTrue(result['worker_action_succeeded']);self.assertFalse(result['outcome_verified'])
            view=guard.work_status('one')
            self.assertTrue(view['open']);self.assertEqual(view['phase'],'awaiting_outcome_evidence')
            self.assertEqual(guard.work_snapshot()['open_count'],1)
            self.assertEqual(guard.execute('shell',{'cmd':'echo fixture'},'one'),result)
            self.assertEqual(action.call_count,1)

    def test_old_worker_claim_is_derived_without_db_mutation_or_replay(self):
        with tempfile.TemporaryDirectory() as root:
            action=Mock();guard=TaskGuard(Path(root)/'journal',{'shell':action},42,lambda:True,capability_policy=admission)
            for rid,created in [('undated',None),('dated',100)]:
                raw=json.dumps(guard.response(rid,'SUCCESS',outcome_verified=True,result={'customer_text':'private'}))
                with guard.connect() as db:
                    db.execute('INSERT INTO requests(id,action,status,response,created_at) VALUES(?,?,?,?,?)',(rid,'shell','SUCCESS',raw,created))
            with guard.connect() as db:before=db.execute('SELECT * FROM requests ORDER BY id').fetchall()
            self.assertEqual(guard.work_snapshot()['open_count'],0)
            self.assertEqual(guard.work_snapshot()['history_open_count'],2)
            self.assertEqual(guard.work_snapshot(include_history=True)['open_count'],2)
            view=guard.work_status('undated');self.assertFalse(view['outcome_verified']);self.assertTrue(view['history_only'])
            self.assertEqual(view['recorded_status'],'SUCCESS');self.assertNotIn('result',view)
            with guard.connect() as db:
                response=db.execute("SELECT response FROM requests WHERE id='dated'").fetchone()[0]
                self.assertEqual(guard._recorded(db,'dated',response)['status'],'EXECUTION_SUCCEEDED')
                self.assertEqual(db.execute('SELECT * FROM requests ORDER BY id').fetchall(),before)
            action.assert_not_called()

    def test_independent_draft_still_completes(self):
        with tempfile.TemporaryDirectory() as root:
            guard=TaskGuard(Path(root)/'journal',{},42,lambda:True,capability_policy=admission)
            result=guard.execute('local_draft',{'name':'proof','format':'txt','content':'fixture'},'draft')
            self.assertTrue(result['outcome_verified']);self.assertEqual(result['status'],'SUCCESS')
            self.assertTrue(guard.work_status('draft')['outcome_verified']);self.assertFalse(guard.work_status('draft')['open'])
            self.assertEqual(guard.work_snapshot()['open_count'],0)

    def test_model_cannot_invent_completion_or_notification_after_receipt(self):
        for status in ('EXECUTION_SUCCEEDED','OUTCOME_UNKNOWN','APPROVAL_REQUIRED'):
            brain=PabloBrain();brain._call_llm=Mock(side_effect=['TOOL: {"tool":"window_list","params":{}}','Tamamlandı; Telegram mesajı gönderdim.'])
            executor=Mock(return_value={'status':status,'ok':False,'outcome_verified':False,'worker_action_succeeded':status=='EXECUTION_SUCCEEDED'})
            result=brain.think_and_respond('fixture',tool_executor=executor)
            self.assertEqual(brain._call_llm.call_count,1);self.assertEqual(executor.call_count,1)
            self.assertNotIn('Tamamlandı',result['text']);self.assertNotIn('gönderdim',result['text'])
            self.assertEqual(result['stopped'],'approval' if status=='APPROVAL_REQUIRED' else 'outcome_unverified')
