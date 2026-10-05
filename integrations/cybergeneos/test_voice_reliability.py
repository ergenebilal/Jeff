import json,tempfile,threading,time,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from integrations.cybergeneos.live_adapter import LiveCalls,Refused,brain_reply


class ReliabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.tokens=[];self.now=1000;self.executions=0
        self.release=threading.Event();self.entered=threading.Event()
        self.addCleanup(self.release.set)
        def reply(text):
            self.executions+=1;self.entered.set();self.release.wait(3)
            yield 'Gerçek sonuç.'
        self.service=LiveCalls(Path(self.tmp.name)/'voice-calls.sqlite3',lambda:'test',reply,
            clock=lambda:self.now,token_request=lambda body:self.tokens.append(body) or 'auth_tokens/test',durable=True)
        self.session=self.service.session('owner','Charon')
        self.body={'session':self.session['session'],'call_id':'first','text':'Bir fikri değerlendir.'}

    def test_disconnected_consumer_does_not_lose_or_reexecute_work(self):
        stream=self.service.consult_stream('owner',self.body)
        self.assertEqual(next(stream)['t'],'accepted');self.assertTrue(self.entered.wait(1));stream.close()
        self.assertEqual(self.service.result('owner',self.body)['state'],'RUNNING')
        with self.assertRaises(Refused):self.service.consult('owner',self.body)
        self.release.set()
        for _ in range(100):
            result=self.service.result('owner',self.body)
            if result['state']=='ANSWERED':break
            time.sleep(.01)
        self.assertEqual(result['answer'],'Gerçek sonuç.');self.assertEqual(self.executions,1)
        self.assertTrue(self.service.consult('owner',self.body)['cached']);self.assertEqual(self.executions,1)

    def test_result_read_never_exposes_other_owners_work(self):
        with self.assertRaises(Refused):self.service.result('other',self.body)
        self.assertEqual(self.executions,0)

    def test_renew_uses_same_ledger_and_does_not_submit_work(self):
        self.now+=100
        renewal=self.service.renew('owner',dict(self.body,handle='test-resumption',voice='Charon'))
        self.assertEqual(renewal['setup']['sessionResumption']['handle'],'test-resumption')
        self.assertEqual(self.executions,0);self.assertEqual(len(self.tokens),2)
        with self.service.db() as db:self.assertEqual(db.execute('SELECT count(*) FROM voice_sessions').fetchone()[0],1)

    def test_wrong_owner_and_ended_session_cannot_renew(self):
        with self.assertRaises(Refused):self.service.renew('other',dict(self.body,handle='x'))
        self.service.end('owner',self.body['session'])
        with self.assertRaises(Refused):self.service.renew('owner',dict(self.body,handle='x'))
        self.assertEqual(len(self.tokens),1)

    def test_process_restart_marks_abandoned_work_unknown_without_rerun(self):
        with self.service.db() as db:
            db.execute("INSERT INTO voice_calls VALUES('old-session','old-call','binding','RUNNING',NULL)")
        self.assertEqual(self.service.recover_on_startup(),1)
        with self.service.db() as db:self.assertEqual(db.execute('SELECT state FROM voice_calls').fetchone()[0],'OUTCOME_UNKNOWN')
        self.assertEqual(self.executions,0)

    def test_end_during_token_request_cannot_resurrect_a_session(self):
        def token(body):
            self.now+=1;self.service.end('owner',self.body['session']);return 'auth_tokens/test'
        self.service.token_request=token
        with self.assertRaises(Refused):self.service.renew('owner',dict(self.body,handle='x'))

    def test_same_hermes_brain_session_survives_transport_and_cannot_become_panel_only(self):
        requests=[]
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):pass
        def request(req,timeout):requests.append(req);return Response()
        app=SimpleNamespace(DATA=self.tmp.name,jeff=SimpleNamespace(DATA_RULES='DATA ONLY',
            pack_request=lambda t,c:t+' '+c,hermes_url=lambda:'http://fixture',sse_deltas=lambda response:iter(['Yanıt.'])))
        with patch.dict('os.environ',{'HERMES_API_KEY':'test'}),patch('urllib.request.urlopen',side_effect=request):
            list(brain_reply(app,'Bir yazılım fikrini düşünelim.','context'))
            list(brain_reply(app,'Buna göre bir sonraki adım?','context'))
        self.assertEqual(requests[0].headers['X-hermes-session-id'],requests[1].headers['X-hermes-session-id'])
        body=json.loads(requests[0].data)
        self.assertEqual(body['model'],'jeff');self.assertIn('yeteneklerinin sınırı değildir',body['messages'][0]['content'])
        self.assertNotIn('en çok 3',body['messages'][0]['content'])
        self.assertFalse(self.session['native_conversation']);self.assertTrue(self.session['single_brain'])


if __name__=='__main__':unittest.main()
