import json,tempfile,threading,time,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from integrations.cybergeneos.live_adapter import LiveCalls,Refused,brain_reply,brain_route,bounded_brain_lines,record_primary_failure,verified_session_reply


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
        self.assertEqual(body['model_options']['reasoning_effort'],'low')
        self.assertNotIn('en çok 3',body['messages'][0]['content'])
        self.assertFalse(self.session['native_conversation']);self.assertTrue(self.session['single_brain'])

    def test_voice_transport_selection_does_not_change_global_configuration(self):
        route=Path(self.tmp.name)/'voice-brain-route.json'
        route.write_text(json.dumps({'model':'gemini-3.8-flash','provider':'custom:jeff-voice-google','reasoning_effort':'low'}))
        selected=brain_route(self.tmp.name)
        self.assertEqual(selected['provider'],'custom:jeff-voice-google');self.assertEqual(selected['model'],'gemini-3.8-flash')
        self.assertNotIn('api_key',selected)
        route.unlink();self.assertEqual(brain_route(self.tmp.name)['model'],'jeff')

    def test_invalid_voice_route_never_silently_falls_back_or_accepts_secrets(self):
        route=Path(self.tmp.name)/'voice-brain-route.json'
        for value in ['broken',json.dumps({'model':'unknown','provider':'gemini','reasoning_effort':'low'}),
                      json.dumps({'model':'gemini-3.8-flash','provider':'gemini','reasoning_effort':'low','api_key':'secret'})]:
            with self.subTest(value=value):
                route.write_text(value)
                with self.assertRaises(Refused):brain_route(self.tmp.name)

    def capacity_fixture(self):
        primary={'model':'gpt-6-astra','provider':'openai-codex','reasoning_effort':'low'}
        standby={'model':'gemini-3.8-flash','provider':'custom:jeff-voice-google','reasoning_effort':'low'}
        Path(self.tmp.name,'voice-brain-route.json').write_text(json.dumps(dict(primary,fallback=standby)))
        value={'version':1,'observed_at':1000,'blocks':[
            dict(provider=primary['provider'],model=primary['model'],unavailable_until=3000,source='openai_usage_limit_reached'),
            dict(provider=standby['provider'],model=standby['model'],unavailable_until=2000,source='google_daily_quota_exceeded')]}
        path=Path(self.tmp.name,'voice-brain-capacity.json');path.write_text(json.dumps(value));path.chmod(0o600)
        return path,value

    def test_both_dated_capacity_limits_refuse_before_any_backend_call(self):
        self.capacity_fixture()
        app=SimpleNamespace(DATA=self.tmp.name,jeff=SimpleNamespace())
        with patch('integrations.cybergeneos.live_adapter.time.time',return_value=1001),patch('urllib.request.urlopen') as backend:
            with self.assertRaises(Refused) as refused:list(brain_reply(app,'Bir fikir düşünelim.','{}'))
        self.assertEqual(refused.exception.reason,'ses_model_hakki_dolu');backend.assert_not_called()

    def test_capacity_expiry_allows_only_a_later_human_request_on_matching_route(self):
        self.capacity_fixture()
        with patch('integrations.cybergeneos.live_adapter.time.time',return_value=2001):
            self.assertEqual(brain_route(self.tmp.name)['provider'],'custom:jeff-voice-google')
        with patch('integrations.cybergeneos.live_adapter.time.time',return_value=3001):
            self.assertEqual(brain_route(self.tmp.name)['provider'],'openai-codex')
        self.assertEqual(self.executions,0)

    def test_old_primary_failure_does_not_erase_dated_hard_capacity_limit(self):
        self.capacity_fixture()
        with patch('integrations.cybergeneos.live_adapter.time.time',return_value=1001):
            record_primary_failure(self.tmp.name,{'provider':'openai-codex'})
        with patch('integrations.cybergeneos.live_adapter.time.time',return_value=1200):
            with self.assertRaises(Refused) as refused:brain_route(self.tmp.name)
        self.assertEqual(refused.exception.reason,'ses_model_hakki_dolu')

    def test_capacity_record_rejects_wrong_model_secrets_and_unbounded_or_future_dates(self):
        path,valid=self.capacity_fixture()
        bad=[]
        for field,value in [('model','unknown'),('unavailable_until',float('inf')),('unavailable_until',True),
                            ('unavailable_until',999),('unavailable_until',1000+8*86400),('source','healthy'),('api_key','secret')]:
            candidate=json.loads(json.dumps(valid));candidate['blocks'][0][field]=value;bad.append(candidate)
        bad.extend([dict(valid,observed_at=2000),dict(valid,observed_at=True),dict(valid,version=2),{}])
        with patch('integrations.cybergeneos.live_adapter.time.time',return_value=1001):
            for value in bad:
                path.write_text(json.dumps(value))
                with self.subTest(value=value),self.assertRaises(Refused) as refused:brain_route(self.tmp.name)
                self.assertEqual(refused.exception.reason,'ses_kapasite_kaydi_gecersiz')

    def test_capacity_refusal_is_not_unknown_execution_and_keeps_record_reader_available(self):
        def blocked(text):raise Refused(503,'ses_model_hakki_dolu')
        self.service.reply=blocked
        self.service.records_reply=lambda text:iter(['Kayıttan okundu.'])
        with self.assertRaises(Refused) as refused:list(self.service._execute_stream('owner',self.body))
        self.assertEqual(refused.exception.reason,'ses_model_hakki_dolu')
        self.assertEqual(self.service.result('owner',self.body)['state'],'NOT_EXECUTED')
        self.assertIsNone(self.service.result('owner',self.body)['answer'])
        with self.assertRaises(Refused):list(self.service._execute_stream('owner',self.body))
        read=dict(self.body,call_id='records-after-capacity',operation='records',text='Pablo ne durumda?')
        events=list(self.service._execute_stream('owner',read))
        self.assertEqual(events[-1]['answer'],'Kayıttan okundu.');self.assertEqual(self.executions,0)

    def test_openai_primary_keeps_gemini_standby_without_executing_either_model(self):
        primary={'model':'gpt-6-astra','provider':'openai-codex','reasoning_effort':'low'}
        fallback={'model':'gemini-3.8-flash','provider':'custom:jeff-voice-google','reasoning_effort':'low'}
        Path(self.tmp.name,'voice-brain-route.json').write_text(json.dumps(dict(primary,fallback=fallback)))
        self.assertEqual(brain_route(self.tmp.name)['provider'],'openai-codex')
        self.assertEqual(self.executions,0)
        record_primary_failure(self.tmp.name,primary)
        self.assertEqual(brain_route(self.tmp.name)['provider'],'custom:jeff-voice-google')
        state=json.loads(Path(self.tmp.name,'voice-brain-route-state.json').read_text())
        self.assertFalse(state['failed_request_replayed']);self.assertEqual(self.executions,0)
        with patch('integrations.cybergeneos.live_adapter.time.time',return_value=state['primary_unavailable_until']+1):
            self.assertEqual(brain_route(self.tmp.name)['provider'],'openai-codex')

    def test_openai_failure_is_not_a_second_backend_request_or_a_gemini_success(self):
        primary={'model':'gpt-6-astra','provider':'openai-codex','reasoning_effort':'low'}
        fallback={'model':'gemini-3.8-flash','provider':'custom:jeff-voice-google','reasoning_effort':'low'}
        Path(self.tmp.name,'voice-brain-route.json').write_text(json.dumps(dict(primary,fallback=fallback)))
        requests=[]
        def fail(request,timeout):requests.append(json.loads(request.data));raise OSError('connection lost')
        app=SimpleNamespace(DATA=self.tmp.name,jeff=SimpleNamespace(DATA_RULES='DATA ONLY',pack_request=lambda t,c:t,hermes_url=lambda:'http://fixture'))
        with patch.dict('os.environ',{'HERMES_API_KEY':'test'}),patch('urllib.request.urlopen',side_effect=fail):
            with self.assertRaises(OSError):list(brain_reply(app,'Sadece konuş, iş başlatma.',''))
        self.assertEqual(len(requests),1);self.assertEqual(requests[0]['provider'],'openai-codex')
        self.assertTrue(requests[0]['require_model_lock'])
        self.assertEqual(brain_route(self.tmp.name)['provider'],'custom:jeff-voice-google')

    def test_corrupt_standby_state_or_credentials_are_refused_not_used_as_success(self):
        route=Path(self.tmp.name,'voice-brain-route.json')
        primary={'model':'gpt-6-astra','provider':'openai-codex','reasoning_effort':'low'}
        standby={'model':'gemini-3.8-flash','provider':'custom:jeff-voice-google','reasoning_effort':'low'}
        route.write_text(json.dumps(dict(primary,fallback=dict(standby,api_key='secret'))))
        with self.assertRaises(Refused):brain_route(self.tmp.name)
        route.write_text(json.dumps(dict(primary,fallback=standby)))
        Path(self.tmp.name,'voice-brain-route-state.json').write_text('broken')
        with self.assertRaises(Refused):brain_route(self.tmp.name)
        for status in [[],False,{'primary_unavailable_until':True},{'primary_unavailable_until':float('inf')},{'primary_unavailable_until':float('nan')}]:
            with self.subTest(status=status):
                Path(self.tmp.name,'voice-brain-route-state.json').write_text(json.dumps(status))
                with self.assertRaises(Refused):brain_route(self.tmp.name)

    def test_only_completed_locked_provider_output_is_canonical(self):
        selected={'provider':'openai-codex','model':'gpt-6-astra'}
        def frame(event,data):return [f'event: {event}', 'data: '+json.dumps(data),'']
        runtime=dict(selected,model_lock='confirmed')
        lines=frame('assistant.commentary',{'text':'Kontrol ediyorum.'})+frame('assistant.delta',{'delta':'Taslak'})
        lines+=frame('assistant.completed',{'content':'Gerçek sonuç.'})+frame('run.completed',{'runtime':runtime})+frame('done',{})
        self.assertEqual(list(verified_session_reply(lines,selected,0,clock=lambda:1)),['Gerçek sonuç.'])
        for terminal in [('run.failed',{}),('run.cancelled',{}),('error',{}),
                         ('run.completed',{'runtime':dict(runtime,provider='other')}),
                         ('run.completed',{'runtime':dict(runtime,model_lock='accepted')}),
                         ('run.completed',{'runtime':runtime,'partial':True})]:
            with self.subTest(terminal=terminal):
                failed=lines[:6]+frame('assistant.completed',{'content':'Başarı gibi görünen hata.'})+frame(*terminal)
                with self.assertRaises(Refused):list(verified_session_reply(failed,selected,0,clock=lambda:1))
        with self.assertRaises(Refused):list(verified_session_reply(lines[:6],selected,0,clock=lambda:1))

    def test_empty_or_unverified_openai_stream_enters_standby_without_replay(self):
        primary={'model':'gpt-6-astra','provider':'openai-codex','reasoning_effort':'low'}
        standby={'model':'gemini-3.8-flash','provider':'custom:jeff-voice-google','reasoning_effort':'low'}
        Path(self.tmp.name,'voice-brain-route.json').write_text(json.dumps(dict(primary,fallback=standby)))
        class Response:
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def __iter__(self):return iter([])
        app=SimpleNamespace(DATA=self.tmp.name,jeff=SimpleNamespace(DATA_RULES='DATA ONLY',pack_request=lambda t,c:t,hermes_url=lambda:'http://fixture'))
        with patch.dict('os.environ',{'HERMES_API_KEY':'test'}),patch('urllib.request.urlopen',return_value=Response()) as request:
            with self.assertRaises(Refused):list(brain_reply(app,'İş başlatma.',''))
        self.assertEqual(request.call_count,1)
        self.assertIn('/api/sessions/',request.call_args.args[0].full_url)
        self.assertEqual(brain_route(self.tmp.name)['provider'],standby['provider'])
        proof=json.loads(Path(self.tmp.name,'voice-brain-route-last.json').read_text())
        self.assertFalse(proof['completion_verified']);self.assertFalse(proof['failed_request_replayed'])

    def test_named_gemini_runtime_requires_exact_confirmed_identity(self):
        selected={'provider':'custom:jeff-voice-google','model':'gemini-3.8-flash'}
        runtime={'provider':'custom','model':selected['model'],'requested':selected,'model_lock':'confirmed'}
        def stream(r):return ['event: assistant.completed','data: '+json.dumps({'content':'Yedi.'}),
                              'event: run.completed','data: '+json.dumps({'runtime':r})]
        self.assertEqual(list(verified_session_reply(stream(runtime),selected,0,clock=lambda:1)),['Yedi.'])
        for bad in [dict(runtime,requested={'provider':'custom:other','model':selected['model']}),
                    dict(runtime,model_lock='accepted'),dict(runtime,requested={})]:
            with self.assertRaises(Refused):list(verified_session_reply(stream(bad),selected,0,clock=lambda:1))

    def test_keepalives_cannot_extend_the_initial_answer_deadline(self):
        times=iter([1,20,46])
        with self.assertRaises(Refused):list(bounded_brain_lines([b': keepalive\n']*3,0,clock=lambda:next(times)))

    def test_started_tools_are_not_cancelled_by_the_initial_reply_deadline(self):
        lines=[b'event: hermes.tool.progress\n',b'data: {"status":"running"}\n',b': keepalive\n']
        self.assertEqual(list(bounded_brain_lines(lines,0,clock=lambda:1000)),lines)

    def test_after_real_text_arrives_the_whole_answer_is_allowed_to_finish(self):
        lines=[b'data: {"choices":[{"delta":{"content":"Gercek cevap"}}]}\n',b': keepalive\n']
        self.assertEqual(list(bounded_brain_lines(lines,0,clock=lambda:1000)),lines)


if __name__=='__main__':unittest.main()
