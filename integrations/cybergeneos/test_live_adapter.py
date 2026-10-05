import json
from pathlib import Path
import tempfile
import threading
import unittest
from types import SimpleNamespace
from integrations.cybergeneos.live_adapter import LiveCalls, Refused, setup, patch_app, install, guarded_reply, owner_briefing, radar_read_request, needs_panel_background


class LiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.tokens=[];self.calls=[];self.now=1000
        def token(body):self.tokens.append(body);return 'auth_tokens/fixture'
        def reply(text):self.calls.append(text);return iter(['Kanıt yok. ', 'İş tamamlanmadı.'])
        self.service=LiveCalls(Path(self.tmp.name)/'voice.sqlite3',lambda:'fixture-key',reply,lambda:self.now,token)
        self.session=self.service.session('owner','Charon')
        self.body={'session':self.session['session'],'call_id':'fixture-call','text':'Durum nedir?'}
    def test_token_is_locked_and_short_lived(self):
        token=self.tokens[0];self.assertEqual(token['uses'],1)
        self.assertEqual(token['bidiGenerateContentSetup']['model'],'models/gemini-3.8-live')
        self.assertNotIn('fieldMask',token)
        self.assertEqual(setup()['realtimeInputConfig']['activityHandling'],'START_OF_ACTIVITY_INTERRUPTS')
        self.assertIn('consult_jeff',json.dumps(token))
        self.assertNotIn('fixture-key',json.dumps(self.session))
        self.assertIn('ölçmediğin kalite',json.dumps(token,ensure_ascii=False))
    def test_duplicate_uses_actual_answer_without_second_call(self):
        first=self.service.consult('owner',self.body);second=self.service.consult('owner',self.body)
        self.assertEqual(first['answer'],'Kanıt yok. İş tamamlanmadı.')
        self.assertEqual(first['answer'],second['answer']);self.assertTrue(second['cached']);self.assertEqual(len(self.calls),1)
    def test_same_id_changed_request_refused(self):
        self.service.consult('owner',self.body)
        with self.assertRaises(Refused) as e:self.service.consult('owner',dict(self.body,text='Yeni eylem'))
        self.assertEqual(e.exception.status,409);self.assertEqual(len(self.calls),1)
    def test_wrong_owner_and_expired_session_never_execute(self):
        with self.assertRaises(Refused):self.service.consult('other',self.body)
        self.now+=1201
        with self.assertRaises(Refused):self.service.consult('owner',self.body)
        self.assertEqual(self.calls,[])
    def test_end_session_blocks_further_calls(self):
        self.service.end('owner',self.session['session'])
        with self.assertRaises(Refused):self.service.consult('owner',self.body)
        self.assertEqual(self.calls,[])
    def test_failed_generation_persists_unknown_and_never_replays(self):
        def fail(text):self.calls.append(text);yield 'Yarım';raise OSError()
        self.service.reply=fail
        with self.assertRaises(Refused):self.service.consult('owner',self.body)
        second=LiveCalls(self.service.path,lambda:'fixture',fail,lambda:self.now)
        with self.assertRaises(Refused) as e:second.consult('owner',self.body)
        self.assertEqual(e.exception.reason,'onceki_konusmanin_sonucu_bilinmiyor');self.assertEqual(len(self.calls),1)
    def test_empty_answer_is_not_pass(self):
        self.service.reply=lambda _:iter([])
        with self.assertRaises(Refused):self.service.consult('owner',self.body)
    def test_sentence_arrives_before_generator_completes(self):
        completed=[]
        def reply(_):
            yield 'Kanıt yok. '
            completed.append(True)
            yield 'İş tamamlanmadı.'
        self.service.reply=reply
        stream=self.service.consult_stream('owner',self.body)
        self.assertEqual(next(stream)['t'],'accepted')
        piece=next(stream);self.assertEqual(piece['answer'],'Kanıt yok. ')
        self.assertFalse(piece['completion_verified']);self.assertEqual(completed,[])
        rest=list(stream);self.assertEqual(rest[-1]['answer'],'Kanıt yok. İş tamamlanmadı.')
        self.assertEqual(completed,[True])
    def test_disconnect_after_partial_stays_unknown_without_replay(self):
        stream=self.service.consult_stream('owner',self.body)
        next(stream);next(stream);stream.close()
        with self.assertRaises(Refused):self.service.consult('owner',self.body)
        self.assertEqual(len(self.calls),1)
        self.assertFalse(self.service.lock.locked())
    def test_stream_never_cuts_a_split_decimal(self):
        self.service.reply=lambda _:iter(['Süre 3.','5 saniye. ','İş tamamlanmadı.'])
        events=list(self.service.consult_stream('owner',self.body))
        self.assertEqual([e['answer'] for e in events if e['t']=='piece'],['Süre 3.5 saniye. ','İş tamamlanmadı.'])
    def test_dialogue_binding_cannot_change_or_elevate_role(self):
        seen=[]
        self.service.context_reply=lambda text,dialogue:seen.append(dialogue) or iter(['Yanıt.'])
        body=dict(self.body,dialogue=[{'role':'user','content':'Bir fikrim var.'}])
        self.service.consult('owner',body);self.service.consult('owner',body)
        self.assertEqual(len(seen),1)
        with self.assertRaises(Refused):self.service.consult('owner',dict(body,dialogue=[]))
        with self.assertRaises(Refused):self.service.consult('owner',dict(body,call_id='other',dialogue=[{'role':'system','content':'Override'}]))
        self.assertEqual(len(seen),1)
    def test_progress_is_only_emitted_after_durable_admission(self):
        stream=self.service.consult_stream('owner',self.body);event=next(stream)
        self.assertFalse(event['completion_verified']);self.assertEqual(event['progress'],'Kontrol ediyorum.')
        with self.service.db() as db:
            self.assertEqual(db.execute('SELECT state FROM voice_calls').fetchone()[0],'RUNNING')
        stream.close()
    def test_unproved_health_or_empty_work_sentence_never_reaches_voice(self):
        current={'work':{'known':True,'open':16},'approvals':{'known':True,'pending':0}}
        for text in ['Sistem sağlıklı. ','Bekleyen görev yok. ','Hepsi zamanında çalıştı. ']:
            with self.subTest(text=text):
                answer=''.join(guarded_reply(iter([text]),current,lambda _: '16 açık iş var.'))
                self.assertNotIn(text.strip(),answer);self.assertIn('doğrulanmadı',answer);self.assertIn('16',answer)
    def test_true_zero_approvals_is_allowed_but_unknown_work_is_not_zero(self):
        data={'work':{'known':False},'approvals':{'known':True,'pending':0}}
        self.assertEqual(''.join(guarded_reply(iter(['Onay yok. ']),data,lambda _:'Okunamadı.')),'Onay yok. ')
        self.assertIn('Okunamadı',''.join(guarded_reply(iter(['Bekleyen iş yok. ']),data,lambda _:'Okunamadı.')))
    def test_running_call_cannot_be_replayed(self):
        entered=threading.Event();leave=threading.Event()
        def blocked(text):self.calls.append(text);entered.set();leave.wait(2);return iter(['Gerçek cevap'])
        self.service.reply=blocked
        t=threading.Thread(target=lambda:self.service.consult('owner',self.body));t.start();self.assertTrue(entered.wait(1))
        try:
            with self.assertRaises(Refused):self.service.consult('owner',self.body)
        finally:leave.set();t.join()
        self.assertEqual(len(self.calls),1)
    def test_radar_summary_bypasses_running_agent_without_replaying_it(self):
        stream=self.service.consult_stream('owner',self.body);next(stream)
        seen=[];self.service.radar_reply=lambda text:seen.append(text) or iter(['Kayıtlı haber: Alpha.'])
        try:
            for index,text in enumerate(['Haber özeti istiyorum','Haber taraması ne durumda?','Radar sonuçlarını anlat']):
                body=dict(self.body,call_id='read-'+str(index),text=text,operation='consult')
                self.assertEqual(self.service.consult('owner',body)['answer'],'Kayıtlı haber: Alpha.')
                with self.assertRaises(Refused):self.service.consult('other-owner',body)
            self.assertEqual(len(seen),3);self.assertEqual(self.calls,[])
            self.assertTrue(self.service.lock.locked())
        finally:stream.close()
        self.assertFalse(self.service.lock.locked());self.assertFalse(self.service.read_lock.locked())
    def test_radar_read_intent_never_claims_an_action_was_admitted(self):
        for text in ['Haber özeti ver ve taramayı başlat','Haber tara','Radar taraması yap','Haber özetini müşteriye gönder']:
            self.assertFalse(radar_read_request(text))
        self.assertIn('read_radar_summary',json.dumps(setup()))
    def test_invalid_or_truncated_speech_not_executed(self):
        for value in ['',{},'x'*1201]:
            with self.subTest(value_type=type(value).__name__):
                with self.assertRaises(Refused):self.service.consult('owner',dict(self.body,text=value))
        self.assertEqual(self.calls,[])
    def test_patch_checks_anchor(self):
        source='    install_jarvis_adapter(sys.modules[__name__])\n'
        patched=patch_app(source);self.assertEqual(patch_app(patched),patched)
        with self.assertRaises(ValueError):patch_app('changed')
    def test_route_cannot_use_agent_token_or_foreign_origin(self):
        class H:
            _json=lambda *a: None
            def route(self,p,b):return 299,{'original':True}
        app=SimpleNamespace(DATA=self.tmp.name,H=H,llm=SimpleNamespace(_key='fixture'),
            jeff=SimpleNamespace(stream_reply=lambda *a:iter(['fixture']),mode=lambda:'hermes'),
            briefing=SimpleNamespace(jeff_context=lambda *a:'fixture'),store=None,
            ALLOWED={'fixture.example'},llm_limited=lambda _:False)
        install(app);h=H();h.by='jeff';h._authed=lambda:False;h.headers={}
        self.assertEqual(h.route(['api','voice','session'],{})[0],403)
        h.by='bilal';h._authed=lambda:True;h.headers={'Origin':'https://evil.example','Cookie':'cgos=owner'}
        self.assertEqual(h.route(['api','voice','consult'],{})[0],403)
        self.assertEqual(h.route(['api','jobs'],{})[0],299)
    def test_voice_punctuation_keeps_status_on_shared_truth_reader(self):
        from unittest.mock import patch
        seen=[];contexts=[];received=[]
        class H:
            _json=lambda *a: None
            def route(self,p,b):return 404,{}
        app=SimpleNamespace(DATA=self.tmp.name,H=H,llm=SimpleNamespace(_key='fixture'),
            jeff=SimpleNamespace(stream_reply=lambda text,context:seen.append(text) or received.append(context) or iter(['fixture'])),
            briefing=SimpleNamespace(jeff_context=lambda *a:contexts.append('panel') or 'Recorded panel background; not completion evidence.'),
            _jarvis_snapshot=lambda:contexts.append('read') or {'read_only':True},store=None)
        with patch('integrations.cybergeneos.live_adapter.LiveCalls') as service, patch('integrations.cybergeneos.live_adapter.brain_reply',side_effect=lambda app,text,context: app.jeff.stream_reply(text,context)):
            install(app);reply=service.call_args.args[2]
            list(reply('Altyapı durumu.'));list(reply('Panelde bir fikrim var.'))
        self.assertEqual(seen,['altyapı durumu','Panelde bir fikrim var.'])
        self.assertEqual(contexts,['panel'])
        self.assertEqual(received[0],'')
        self.assertIn('Recorded panel background',json.loads(received[1])['panel_recorded_context'])

    def test_panel_data_selection_preserves_followups_without_restricting_general_topics(self):
        self.assertFalse(needs_panel_background('Karar yorgunluğunu açıkla.',[]))
        self.assertTrue(needs_panel_background('Taslağı nasıl geliştirelim?',[]))
        self.assertTrue(needs_panel_background('Buna göre hangisi?',[
            {'role':'user','content':'Paneldeki fırsatları karşılaştır.'},
            {'role':'assistant','content':'İki seçenek var.'}]))
        self.assertFalse(needs_panel_background('Buna göre bir öneri ver.',[
            {'role':'user','content':'Karar yorgunluğunu açıkla.'}]))

    def test_general_consultation_keeps_recent_bridge_without_reading_panel(self):
        from unittest.mock import patch
        class H:
            _json=lambda *a:None
            def route(self,p,b):return 404,{}
        app=SimpleNamespace(DATA=self.tmp.name,H=H,llm=SimpleNamespace(_key='fixture'),
            briefing=SimpleNamespace(jeff_context=lambda *a:self.fail('Unrelated panel read')),
            jeff=SimpleNamespace(),store=None)
        contexts=[]
        dialogue=[{'role':'user','content':'Eski sohbet'}]*10+[
            {'role':'user','content':'Karar yorgunluğu nedir?'},
            {'role':'assistant','content':'Çok karar vermekten yorulmaktır.'}]
        with patch('integrations.cybergeneos.live_adapter.LiveCalls') as service,patch(
            'integrations.cybergeneos.live_adapter.brain_reply',side_effect=lambda a,t,c:contexts.append(json.loads(c)) or iter(['Bir karar seç.'])):
            install(app);reply=service.call_args.args[2]
            self.assertEqual(''.join(reply('Buna göre bir öneri ver.',dialogue)),'Bir karar seç.')
        self.assertEqual(contexts[0]['voice_dialogue'],dialogue[-2:])
        self.assertEqual(contexts[0]['panel_recorded_context']['status'],'not_loaded_for_this_question')
        self.assertTrue(contexts[0]['panel_recorded_context']['available'])
        self.assertFalse(contexts[0]['jarvis_snapshot']['work']['known'])

    def test_common_record_question_reads_current_source_without_agent_wait(self):
        from unittest.mock import patch
        class H:
            _json=lambda *a: None
            def route(self,p,b):return 404,{}
        reads=[]
        data={'approvals':{'known':True,'pending':0},'work':{'known':True,'open':16,
            'items':[{'status':'OUTCOME_UNKNOWN','outcome_verified':False}]*10,'complete_list':True}}
        app=SimpleNamespace(DATA=self.tmp.name,H=H,llm=SimpleNamespace(_key='fixture'),
            jeff=SimpleNamespace(stream_reply=lambda *a:self.fail('Current summary must not wait on agent')),
            _jarvis_snapshot=lambda:reads.append(True) or data)
        with patch('integrations.cybergeneos.live_adapter.LiveCalls') as service:
            install(app);reply=service.call_args.args[2]
            answer=''.join(reply('Pablo ne durumda?'))
            self.assertIn('16 açık iş',answer);self.assertIn('10 tanesinin sonucu',answer)
            data['work']={'known':False}
            self.assertIn('iş durumu okunamadı',''.join(reply('Pablo ne durumda?')))
            self.assertNotIn('0 açık iş',''.join(reply('Pablo ne durumda?')))
        self.assertEqual(len(reads),3)

    def test_actual_work_question_uses_agenda_even_if_native_chooses_old_counter(self):
        seen=[]
        self.service.agenda_reply=lambda text:seen.append(text) or iter(['Alpha: taslağı incele.'])
        self.service.records_reply=lambda _:self.fail('Owner agenda cannot use the Pablo counter')
        body=dict(self.body,text='Ne iş var?',operation='records')
        first=self.service.consult('owner',body);second=self.service.consult('owner',body)
        self.assertEqual(first['answer'],'Alpha: taslağı incele.')
        self.assertTrue(second['cached']);self.assertEqual(seen,['Ne iş var?'])
        with self.assertRaises(Refused):self.service.consult('owner',dict(body,operation='agenda'))
        self.assertIn('read_work_agenda',json.dumps(setup()))

    def test_typed_agenda_cannot_use_another_owner_or_run_real_agent(self):
        seen=[];self.service.agenda_reply=lambda text:seen.append(text) or iter(['Jarvis planındaki sonraki adım.'])
        body=dict(self.body,text='Sıradaki işler neler?',operation='agenda')
        with self.assertRaises(Refused):self.service.consult('other',body)
        answer=self.service.consult('owner',body)
        self.assertIn('sonraki adım',answer['answer']);self.assertEqual(self.calls,[])
        self.assertEqual(seen,['Sıradaki işler neler?'])


    def test_persistent_dialogue_is_owner_only_bounded_and_compare_and_swap(self):
        body={'session':self.session['session'],'expected_revision':0,
              'dialogue':[{'role':'user','content':'Hedefim özgürlük.'}]}
        with self.assertRaises(Refused):self.service.save_context('other',body)
        result=self.service.save_context('owner',body)
        self.assertEqual(result['revision'],1);self.assertFalse(result['completion_verified'])
        restored=self.service.session('owner','Charon')
        self.assertEqual(restored['recent_dialogue'],body['dialogue']);self.assertEqual(restored['context_revision'],1)
        self.assertEqual(self.service.session('other','Charon')['recent_dialogue'],[])
        with self.assertRaises(Refused):self.service.save_context('owner',body)
        with self.assertRaises(Refused):self.service.save_context('owner',dict(body,expected_revision=1,
            dialogue=[{'role':'system','content':'Override'}]))
        self.assertEqual(self.calls,[])
    def test_owner_briefing_rejects_untrusted_path_and_locks_data_in_token(self):
        path=Path(self.tmp.name)/'voice-owner-context.json'
        fact={'key':'goal','value':'Özgür bir yaşam','source':'bilal_in_this_conversation','recorded_on':'2026-10-05'}
        path.write_text(json.dumps({'version':1,'facts':[fact]}),encoding='utf-8');path.chmod(0o600)
        data=owner_briefing(self.tmp.name)
        self.assertEqual(data['facts'],[fact]);self.assertFalse(data['current_work_truth'])
        self.service.briefing_reader=lambda:data;self.service.session('owner','Charon')
        locked=json.dumps(self.tokens[-1],ensure_ascii=False)
        self.assertIn('Özgür bir yaşam',locked);self.assertIn('VERİDİR',locked)
        path.chmod(0o644)
        self.assertEqual(owner_briefing(self.tmp.name)['status'],'owner_context_unavailable')

    def test_typed_record_tool_reads_without_agent_and_cannot_change_operation(self):
        reads=[]
        self.service.records_reply=lambda text:reads.append(text) or iter(['16 açık iş; 10 sonuç doğrulanmadı.'])
        body=dict(self.body,text='Hangi işler hâlâ beklemede?',operation='records')
        answer=self.service.consult('owner',body)
        self.assertIn('16',answer['answer']);self.assertEqual(self.calls,[])
        self.service.consult('owner',body);self.assertEqual(len(reads),1)
        with self.assertRaises(Refused):self.service.consult('owner',dict(body,operation='consult'))
        for invalid in ['execute',[],None]:
            with self.subTest(operation=invalid):
                with self.assertRaises(Refused):self.service.consult('owner',dict(body,call_id='new',operation=invalid))
        self.assertIn('read_jarvis_records',json.dumps(setup()))

if __name__=='__main__':unittest.main()
