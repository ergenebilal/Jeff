import copy
import hashlib
import json
import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from server import app, briefing, contact, marketing  # noqa: E402
from server import qualification as q
from server import qualified_draft as d
from server.jobs import Handle, Jobs  # noqa: E402
from server.store import Store, now  # noqa: E402


class QualifiedDraftTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)/'test.db'
        self.s = Store(self.path)
        marketing.init(self.s)
        q.init(self.s)
        self.lid = self.s.create_lead({'name':'Örnek Güzellik Merkezi','city':'Bursa'})
        self.s.update_lead(self.lid, {'website':'https://ornek.com/','category':'Güzellik merkezi','phone':'02241234567'})
        text = 'Randevu taleplerinizi formdan alıp uygun saati ekibimiz onaylar. İptal sonrası bekleme listesindeki müşterilerimize haber veriyoruz. info@ornek.com 0224 123 45 67'
        self.pages = [{'url':'https://ornek.com/','text':text,'links':[],'observed_at':now(),
                       'text_sha256':hashlib.sha256(text.encode()).hexdigest()}]
        research = {'argument_id':'randevu-dusmesin','facts':[
            {'kind':'operations','signal':'manual_callback','url':'https://ornek.com/','quote':'Randevu taleplerinizi formdan alıp uygun saati ekibimiz onaylar.'},
            {'kind':'operations','signal':'rescheduling_waitlist','url':'https://ornek.com/','quote':'İptal sonrası bekleme listesindeki müşterilerimize haber veriyoruz.'}]}
        audit = {'supported_ids':[0,1],'distinct_operations':[0,1],'explicit_need_ids':[],'trigger_ids':[],
                 'blocking_counter_ids':[],'fit':True,'unresolved':True,'hypothesis':'Talep onayı ve iptal sonrası koordinasyon için koşullu destek.',
                 'discovery_question':'Bu iki idari akışı hangi mevcut araçlarla yürütüyorsunuz?',
                 'reason':'İki farklı somut idari akış var; gerçek iş yükü ve ihtiyaç bilinmiyor.',
                 'unknowns':['Mevcut yazılım ve iş yükü bilinmiyor.'],
                 'adversarial':{'alternative_explanation':'Mevcut ekip ve yazılım iki akışı sorunsuz yürütüyor olabilir.',
                                'evidence_limit':'Alıntılar gerçek mesaj hacmi veya müşteri kaybını göstermiyor.',
                                'disconfirming_observation':'Mevcut araçların iki işi yeterli karşılaması teklifi çürütür.'}}
        self.qjob, _ = q.start(self.s,[self.lid],'source-qualified-fixture')
        with patch.object(q,'collect',return_value=(self.pages,[])), patch.object(q,'model',side_effect=[research,audit]):
            q.run(self.s,Handle(self.s,self.qjob,threading.Event()),{})
        self.s.update_job(self.qjob,status='done')
        self.assertEqual(q.views(self.s)[self.lid]['decision'],'gorusme_adayi')
        self.draft = {'text':"Merhaba, CyberGene'den yazıyorum. Örnek Güzellik Merkezi'nin sitesinde talepleri formdan alıp uygun saati ekibinizin onayladığını ve iptal sonrası bekleme listesindeki müşterilere haber verdiğinizi görüyoruz. Mevcut düzeniniz yeterli olabilir; ekibiniz isterse bu iki idari akışın takibine koşullu destek sunabiliriz. Bu talepleri ve iptal sonrası haberleşmeyi hangi araçla yürütüyorsunuz?",
                      'used_fact_ids':[0,1],'scope':'Ekibin onayıyla talep ve iptal sonrası idari koordinasyon.',
                      'known_counter':'Mevcut ekip ve sistem aynı işleri yeterli karşılıyor olabilir.',
                      'open_question':'Bu talepleri ve iptal sonrası haberleşmeyi hangi araçla yürütüyorsunuz?'}
        self.audit = {'approved':True,'supported_fact_ids':[0,1],'unsupported_claims':[],
                      'question_check':{'already_answered':False,'reason':'Kaynak iki akışı söylüyor, kullanılan iç aracı açıklamıyor.'},
                      'context_check':{'channel_scope_preserved':True,'existing_solution_respected':True,
                                       'reason':'İki akışın mevcut olduğu korunuyor, kanallar arası süre genellenmiyor.'},
                      'claim_audit':[{'claim':'talepleri formdan alıp uygun saati ekibinizin onayladığını','fact_ids':[0],'supported':True},
                                     {'claim':'iptal sonrası bekleme listesindeki müşterilere haber verdiğinizi','fact_ids':[1],'supported':True}],
                      'reason':'İki farklı somut akış ve koşullu teklif var, mevcut çözüm yok sayılmıyor.',
                      'alternative_explanation':'Mevcut personel ve araçlar iki işi sorunsuz karşılıyor olabilir.',
                      'evidence_limit':'Kaynaklar gerçek ihtiyacı, iş yükünü veya satın alma niyetini kanıtlamıyor.',
                      'disconfirming_condition':'Mevcut araçların iki işi yeterli yürüttüğü bilgisi teklifi çürütür.'}
        self.collect = patch.object(q,'collect',return_value=(self.pages,[])).start()
        self.model = patch.object(q,'model',side_effect=lambda instruction,data,session,receipt: copy.deepcopy(self.audit if 'draft' in data else self.draft)).start()
        self.send = patch.object(contact,'send_email').start()
        self.record = patch.object(contact,'record_contact').start()
        self.addCleanup(patch.stopall)

    def tearDown(self):
        self.s.db.close()
        self.tmp.cleanup()

    def start(self, key='qualified-draft-request', note=''):
        return marketing.start(self.s,self.lid,key,source='qualification',note=note)[0]

    def finish(self, jid=None):
        jid = jid or self.start()
        result = marketing.run(self.s,Handle(self.s,jid,threading.Event()),{})
        self.s.update_job(jid,status='done')
        return jid,result

    def test_native_job_uses_real_report_without_gate_or_owner_override(self):
        jid,_ = self.finish()
        lead = self.s.lead(self.lid)
        self.assertIsNone(lead['gate'])
        self.assertFalse(lead['gate_override'])
        self.assertIsNone(lead['reviewed_at'])
        self.assertIsNone(lead['analysis'])
        self.assertEqual(lead['stage'],'Taslak hazır')
        view = marketing.views(self.s)[self.lid]
        self.assertTrue(view['current'])
        self.assertEqual(view['qualification_job'],self.qjob)
        self.assertFalse(view['human_accepted'])
        self.assertIsNone(view['review'])
        self.assertFalse(view['delivered'])
        self.assertEqual(len(view['evidence']),2)
        self.assertEqual(self.model.call_count,2)
        self.assertNotEqual(self.model.call_args_list[0].args[2],self.model.call_args_list[1].args[2])
        self.assertEqual(self.s.one('SELECT count(*) n FROM marketing_reviews')['n'],0)
        self.send.assert_not_called()
        self.record.assert_not_called()
        self.assertEqual(marketing.start(self.s,self.lid,'qualified-draft-request',source='qualification'),(jid,False))

    def test_negative_or_missing_context_review_never_publishes(self):
        for change in ({'question_check':{'already_answered':True,'reason':'Soru kaynakta ortak takvim açıklamasıyla zaten yanıtlanmış.'}},
                       {'context_check':{'channel_scope_preserved':False,'existing_solution_respected':True,'reason':'Form süresi WhatsApp kanalına genişletilmiş ve kapsam bozulmuş.'}},
                       {'context_check':{'channel_scope_preserved':True,'existing_solution_respected':False,'reason':'Mevcut ortak takvim düzeni teklif tarafından yok sayılmış.'}},
                       {'question_check':None}):
            with self.subTest(change=change), self.assertRaises(marketing.Conflict):
                d.validate(self.draft,{**self.audit,**change},d.payload(self.s.lead(self.lid),d.binding(self.s,self.s.lead(self.lid)))['verified_facts'],self.s.lead(self.lid)['name'])
        self.assertIsNone(self.s.lead(self.lid)['drafts'])

    def test_older_review_protocol_revokes_ready_status_and_owner_approval(self):
        jid,_ = self.finish()
        row=self.s.one('SELECT input_json FROM marketing_runs WHERE job_id=?',(jid,))
        data=json.loads(row['input_json']);data['qualification_binding']['version']=1
        self.s.x('UPDATE marketing_runs SET input_json=? WHERE job_id=?',(json.dumps(data),jid))
        self.assertFalse(marketing.views(self.s)[self.lid]['current'])
        with self.assertRaises(marketing.Conflict):
            marketing.review(self.s,self.lid,marketing.content_digest(self.s.lead(self.lid)),'accepted')

    def test_wrong_sender_or_placeholder_purpose_cannot_publish_despite_positive_critic(self):
        for key, change in (
            ('wrong-sender-request', {'text':self.draft['text'].replace(d.INTRO, "Merhaba, Örnek Güzellik Merkezi'nden; CyberGene olarak yazıyorum.")}),
            ('placeholder-purpose', {'scope':'koşullu önerilen idari ek görev'}),
        ):
            with self.subTest(key=key):
                original = copy.deepcopy(self.draft)
                self.draft.update(change)
                jid = self.start(key)
                with self.assertRaises(marketing.Conflict): self.finish(jid)
                self.s.update_job(jid, status='failed')
                self.assertIsNone(self.s.lead(self.lid)['drafts'])
                self.assertIsNone(self.s.one('SELECT published_at FROM marketing_runs WHERE job_id=?',(jid,))['published_at'])
                self.draft = original
        self.send.assert_not_called(); self.record.assert_not_called()

    def test_message_policy_change_invalidates_previous_ready_draft_and_feedback(self):
        self.finish()
        digest = marketing.content_digest(self.s.lead(self.lid))
        with patch.object(d, 'VERSION', d.VERSION + 1):
            self.assertFalse(marketing.views(self.s)[self.lid]['current'])
            with self.assertRaises(marketing.Conflict): marketing.review(self.s,self.lid,digest,'accepted')

    def test_reconcile_exact_open_question_and_unused_known_id_without_rewriting_model(self):
        extra={'id':2,'kind':'contact','signal':'resmi_iletisim_kanali'}
        facts=d.payload(self.s.lead(self.lid),d.binding(self.s,self.s.lead(self.lid)))['verified_facts']+[extra]
        generated=copy.deepcopy(self.draft);generated['used_fact_ids'].append(2)
        audited=copy.deepcopy(self.audit)
        audited['claim_audit'].append({'claim':generated['open_question'],'fact_ids':[],'supported':False})
        drafted,audit,receipt=d.canonical_outputs(generated,audited,facts)
        d.validate(drafted,audit,facts,self.s.lead(self.lid)['name'])
        self.assertEqual(receipt['unused_declared_fact_ids'],[2])
        self.assertFalse(receipt['message_changed']);self.assertFalse(receipt['approval_changed'])
        self.assertEqual(drafted['text'],generated['text'])
        self.assertTrue(audit['approved']);self.assertEqual(audit['unsupported_claims'],[])
        self.assertEqual(generated['used_fact_ids'],[0,1,2]);self.assertEqual(len(audited['claim_audit']),3)
        for change in ({'claim':'Başka bir soru mu?','fact_ids':[],'supported':False},
                       {'claim':'talepleri formdan alıp uygun saati ekibinizin onayladığını','fact_ids':[0],'supported':False}):
            bad=copy.deepcopy(self.audit);bad['claim_audit'].append(change)
            drafted,audit,_=d.canonical_outputs(self.draft,bad,facts)
            with self.assertRaises(marketing.Conflict): d.validate(drafted,audit,facts,self.s.lead(self.lid)['name'])
        unknown=copy.deepcopy(generated);unknown['used_fact_ids'].append(99)
        drafted,audit,_=d.canonical_outputs(unknown,audited,facts)
        with self.assertRaises(marketing.Conflict): d.validate(drafted,audit,facts,self.s.lead(self.lid)['name'])

    def test_legacy_gate_stays_required_and_idempotency_cannot_switch_source_or_note(self):
        with self.assertRaises(marketing.Conflict):
            marketing.start(self.s,self.lid,'legacy-no-gate')
        jid = self.start(note='Kısa yaz')
        self.assertEqual(self.start(note='Kısa yaz'),jid)
        for params in ({'source':'research'}, {'source':'qualification','note':'Yeni not'}):
            with self.assertRaises(marketing.Conflict):
                marketing.start(self.s,self.lid,'qualified-draft-request',**params)

    def test_unselected_expired_and_opted_out_leads_cannot_start(self):
        raw = self.s.one('SELECT report FROM qualification_reports WHERE lead_id=?',(self.lid,))['report']
        for patch_data in ({'decision':'arastirma_gerekli'}, {'expires_at':now()-1}, {'adversarial':{'status':'missing'}}):
            report = json.loads(raw);report.update(patch_data)
            self.s.x('UPDATE qualification_reports SET report=? WHERE lead_id=?',(json.dumps(report),self.lid))
            with self.assertRaises(marketing.Conflict):
                self.start()
        self.s.x('UPDATE qualification_reports SET report=? WHERE lead_id=?',(raw,self.lid))
        self.s.x('INSERT INTO optout VALUES(?,?,?)',(self.lid,now(),'İstemiyor'))
        with self.assertRaises(marketing.Conflict): self.start()
        self.model.assert_not_called()

    def test_observed_source_change_invalidates_qualification_and_never_generates(self):
        jid = self.start()
        self.pages[0]['text_sha256'] = 'changed'
        with self.assertRaises(marketing.Conflict): self.finish(jid)
        self.model.assert_not_called()
        self.assertFalse(q.views(self.s)[self.lid]['current'])
        self.assertTrue(q.views(self.s)[self.lid]['source_invalidated'])
        self.assertIsNone(self.s.lead(self.lid)['drafts'])

    def test_missing_quote_during_source_read_is_not_replaced_with_inference(self):
        jid = self.start()
        self.pages[0]['text'] = 'İşletmenin yeni sayfası, önceki alıntılar bulunmuyor.'
        with self.assertRaises(marketing.Conflict): self.finish(jid)
        self.model.assert_not_called()
        self.assertIsNone(self.s.lead(self.lid)['drafts'])

    def test_stale_report_revokes_owner_review_and_delivery(self):
        self.finish()
        old = marketing.content_digest(self.s.lead(self.lid))
        marketing.review(self.s,self.lid,old,'accepted')
        self.assertTrue(marketing.views(self.s)[self.lid]['human_accepted'])
        row = self.s.one('SELECT * FROM qualification_reports WHERE lead_id=?',(self.lid,))
        self.s.x('INSERT INTO qualification_reports VALUES(?,?,?,?,?)',('new-report',self.lid,row['input_digest'],row['report'],now()+1))
        view = marketing.views(self.s)[self.lid]
        self.assertFalse(view['current'])
        self.assertIsNone(view['review'])
        with self.assertRaises(marketing.Conflict): marketing.review(self.s,self.lid,old,'accepted')
        with self.assertRaises(contact.Refused): contact.must_allow(self.s,self.s.lead(self.lid),need_finding=False)
        self.assertIn('yeniden inceleme',briefing.steps(self.s)[self.lid]['text'])

    def test_capability_or_company_changes_invalidate_saved_draft(self):
        self.finish()
        catalog = copy.deepcopy(q.capabilities())
        for arg in catalog:
            if arg['id'] == 'randevu-dusmesin': arg['honest_limit'] = 'Hizmet kapsamı değişti.'
        with patch.object(q,'capabilities',return_value=catalog):
            self.assertFalse(marketing.views(self.s)[self.lid]['current'])
        self.s.update_lead(self.lid,{'phone':'02247654321'})
        self.assertFalse(marketing.views(self.s)[self.lid]['current'])

    def test_claim_metadata_edit_cannot_reuse_critique_or_owner_acceptance(self):
        self.finish()
        digest = marketing.content_digest(self.s.lead(self.lid))
        marketing.review(self.s,self.lid,digest,'accepted')
        drafts = json.loads(self.s.lead(self.lid)['drafts'])
        drafts['claim_audit'][0]['fact_ids'] = [99]
        self.s.x('UPDATE leads SET drafts=? WHERE id=?',(json.dumps(drafts),self.lid))
        self.assertFalse(marketing.views(self.s)[self.lid]['current'])
        with self.assertRaises(marketing.Conflict): marketing.review(self.s,self.lid,digest,'accepted')

    def test_report_change_during_model_call_preserves_existing_record(self):
        jid = self.start()
        def change(instruction,data,session,receipt):
            self.s.update_lead(self.lid,{'draft':'Kullanıcının başka metni'})
            return copy.deepcopy(self.audit if 'draft' in data else self.draft)
        self.model.side_effect = change
        with self.assertRaises(marketing.Conflict): self.finish(jid)
        self.assertEqual(self.s.lead(self.lid)['draft'],'Kullanıcının başka metni')
        self.assertIsNone(self.s.lead(self.lid)['drafts'])

    def test_rejected_critique_cannot_publish_but_reason_survives(self):
        self.audit.update(approved=False,unsupported_claims=['Mevcut çözüm yeterli olabilir; ek görev kanıtlanmadı.'])
        jid = self.start()
        with self.assertRaises(marketing.Conflict): self.finish(jid)
        self.assertIsNone(self.s.lead(self.lid)['drafts'])
        view = marketing.views(self.s)[self.lid]
        self.assertFalse(view['current'])
        self.assertFalse(view['audit']['approved'])
        self.assertTrue(view['audit']['unsupported_claims'])

    def test_unknown_fact_claim_mismatch_and_missing_reason_fail_closed(self):
        facts = q.views(self.s)[self.lid]['facts']
        cases = []
        draft = copy.deepcopy(self.draft);draft['used_fact_ids'] = [0,99];cases.append((draft,self.audit))
        audit = copy.deepcopy(self.audit);audit['claim_audit'][0]['claim'] = 'Taslakta bulunmayan bir iddia';cases.append((self.draft,audit))
        audit = copy.deepcopy(self.audit);audit['claim_audit'][0]['fact_ids'] = [True];cases.append((self.draft,audit))
        audit = copy.deepcopy(self.audit);audit['evidence_limit'] = '';cases.append((self.draft,audit))
        draft = copy.deepcopy(self.draft);draft['used_fact_ids'] = [0];cases.append((draft,self.audit))
        for draft,audit in cases:
            with self.assertRaises(marketing.Conflict): d.validate(draft,audit,facts,'Örnek Güzellik Merkezi')

    def test_owner_feedback_does_not_send_and_unaudited_edit_cannot_be_accepted(self):
        self.finish()
        value = marketing.content_digest(self.s.lead(self.lid))
        with self.assertRaises(contact.Refused): contact.must_allow(self.s,self.s.lead(self.lid),need_finding=False)
        marketing.review(self.s,self.lid,value,'accepted')
        marketing.review(self.s,self.lid,value,'accepted')
        self.assertEqual(self.s.one('SELECT count(*) n FROM marketing_reviews')['n'],1)
        self.assertTrue(marketing.views(self.s)[self.lid]['human_accepted'])
        with self.assertRaises(marketing.Conflict): marketing.review(self.s,self.lid,value,'edited','Başka bir taslak metni, tekrar denetlenmeli.')
        self.s.x('UPDATE leads SET draft=? WHERE id=?',('Değişmiş taslak',self.lid))
        self.assertFalse(marketing.views(self.s)[self.lid]['current'])
        self.assertIsNone(marketing.views(self.s)[self.lid]['review'])
        self.send.assert_not_called();self.record.assert_not_called()

    def test_restart_resumes_sources_and_known_output_but_never_ambiguous_response(self):
        jid = self.start()
        row = self.s.one('SELECT input_json FROM marketing_runs WHERE job_id=?',(jid,))
        data = json.loads(row['input_json'])
        base = d.payload(self.s.lead(self.lid),data['qualification_binding'])
        sources = d.verify_sources(self.s,self.s.lead(self.lid),data['qualification_binding'],base)
        marketing._save(self.s,jid,{'sources':{'state':'done','output':sources},'generation':{'state':'done','output':self.draft}})
        self.finish(jid)
        self.assertEqual(self.model.call_count,1)
        jid = self.start('new-ambiguous-job')
        marketing._save(self.s,jid,{'generation':{'state':'calling'}})
        self.assertNotIn(jid,marketing.recover(self.s))
        self.assertEqual(self.s.one('SELECT status FROM jobs WHERE id=?',(jid,))['status'],'failed')
        self.assertEqual(self.model.call_count,1)

    def test_budget_and_native_http_route_use_source_binding(self):
        with patch.dict(os.environ,{'CGOS_MARKETING_DAILY_CAP':'1'}):
            self.finish()
            with self.assertRaises(marketing.Conflict): self.start('next-cap-request')
        old_store,old_jobs = app.store,app.jobs
        with patch('server.jobs.threading.Thread.start'):
            app.store,app.jobs = self.s,Jobs(self.s,MagicMock(),auto_gate=False)
        try:
            code,body = app.act_lead(self.lid,'prepare-qualified',{'request_key':'qualified-draft-request'})
            self.assertEqual(code,200)
            self.assertEqual(body['job'],self.s.one('SELECT job_id FROM marketing_runs')['job_id'])
            self.assertEqual(app.act_lead(self.lid,'drafts',{})[0],409)
            self.assertEqual(app.act_lead(self.lid,'draft',{})[0],409)
        finally:
            app.store,app.jobs = old_store,old_jobs


if __name__ == '__main__': unittest.main()
