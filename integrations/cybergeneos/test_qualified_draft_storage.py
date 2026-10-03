"""SQLite boundary tests for the real qualified-draft modules.

The full packaged panel tests cover the research and HTTP adapters. Here those
adapters are explicit fixtures; the production persistence and review code runs.
"""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

from integrations.cybergeneos.test_marketing_storage import PanelAdapter


def load_workflow():
    package = types.ModuleType('_cgos_qualified_fixture')
    package.__path__ = []
    sys.modules[package.__name__] = package
    for name in ('analysis','contact','outreach','store','qualification'):
        module = types.ModuleType(package.__name__+'.'+name)
        sys.modules[module.__name__] = module
        setattr(package,name,module)
    package.store.now = lambda:1000
    package.outreach.new_ref = lambda:'qualified-ref'
    package.analysis._flat = lambda text:' '.join(text.lower().split())
    package.contact.opted_out = lambda store,lid:False
    package.contact.check_text = lambda text,link:(text,[])
    package.qualification.administrative_operation = lambda fact:fact['signal'] in ('manual_callback','rescheduling_waitlist')
    package.qualification.capabilities = lambda:[{'id':'appointment','capability':'Conditional admin coordination','honest_limit':'No independent need verification'}]
    def views(store):
        row = store.one('SELECT * FROM qualification_reports ORDER BY created_at DESC LIMIT 1')
        return {'lead':{**json.loads(row['report']),'job_id':row['job_id'],'current':True}}
    package.qualification.views = views
    for name in ('qualified_draft','marketing'):
        path = Path(__file__).parent/'qualification_drafts/server'/f'{name}.py'
        spec = importlib.util.spec_from_file_location(package.__name__+'.'+name,path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        setattr(package,name,module)
        spec.loader.exec_module(module)
    return package


p = load_workflow()
m = p.marketing


class QualifiedStorageTests(unittest.TestCase):
    def setUp(self):
        self.s = PanelAdapter()
        self.addCleanup(self.s.db.close)
        m.init(self.s)
        self.s.x('UPDATE leads SET gate=NULL WHERE id=?',('lead',))
        self.s.db.executescript('CREATE TABLE qualification_reports(job_id,lead_id,report,created_at);')
        self.facts = [{'id':0,'kind':'operations','signal':'manual_callback','quote':'Requests are reviewed before confirmation.','url':'https://fixture.example/','observed_at':1000,'text_sha256':'source-a','verification_scope':'quote_exists'},
                      {'id':1,'kind':'operations','signal':'rescheduling_waitlist','quote':'Cancelled appointments go to our waiting list.','url':'https://fixture.example/','observed_at':1000,'text_sha256':'source-a','verification_scope':'quote_exists'}]
        self.report = {'decision':'gorusme_adayi','argument_id':'appointment','supported_ids':[0,1],'facts':self.facts,'adversarial':{'status':'completed'},'expires_at':2000}
        self.s.x('INSERT INTO qualification_reports VALUES(?,?,?,?)',('q-one','lead',json.dumps(self.report),1000))
        self.jid,_ = m.start(self.s,'lead','source-boundary-request',source='qualification')
        self.generated = {'text':'Hello Fixture, CyberGene here. Your requests are reviewed before confirmation and cancelled appointments go to your waiting list. With your team’s agreement we can support these two administrative tasks, while your existing tools may already be sufficient. Which tools do you use to manage them?',
                          'used_fact_ids':[0,1],'scope':'Conditional administrative support for the existing team.',
                          'known_counter':'The current team and tools may already handle both tasks.',
                          'open_question':'Which tools do you use to manage them?'}
        self.audit = {'approved':True,'supported_fact_ids':[0,1],'unsupported_claims':[],
                      'claim_audit':[{'claim':'requests are reviewed before confirmation','fact_ids':[0],'supported':True},
                                     {'claim':'cancelled appointments go to your waiting list','fact_ids':[1],'supported':True}],
                      'reason':'Two distinct tasks, matching sources and a conditional proposition.',
                      'alternative_explanation':'The current team and tools may handle both tasks well.',
                      'evidence_limit':'The sources do not prove workload, need or purchase intention.',
                      'disconfirming_condition':'If existing tools already handle both tasks well, withdraw the proposition.'}
        self.drafts = {'source':'qualification','whatsapp':self.generated['text'],'notes':{'whatsapp':[]},'audit':self.audit,'used_fact_ids':[0,1]}
        self.cp = {'sources':{'state':'done','output':{'verified_at':1000}},'generation':{'state':'done','output':self.generated},
                   'critique':{'state':'done','output':self.audit},'draft':{'state':'done','output':self.drafts}}
        m._save(self.s,self.jid,copy.deepcopy(self.cp))

    def publish(self):
        m.publish(self.s,self.jid)
        self.s.update_job(self.jid,status='done')

    def test_atomic_publish_keeps_gate_and_waits_for_real_owner_feedback(self):
        self.publish();self.publish()
        self.assertIsNone(self.s.lead('lead')['gate'])
        self.assertEqual(self.s.one('SELECT count(*) n FROM events')['n'],1)
        self.assertEqual(self.s.one('SELECT count(*) n FROM marketing_reviews')['n'],0)
        self.assertTrue(m.views(self.s)['lead']['current'])
        self.assertFalse(m.views(self.s)['lead']['human_accepted'])
        self.assertFalse(m.views(self.s)['lead']['delivered'])

    def test_new_report_revokes_review_even_if_message_and_report_text_match(self):
        self.publish()
        value = m.content_digest(self.s.lead('lead'))
        m.review(self.s,'lead',value,'accepted')
        self.s.x('INSERT INTO qualification_reports VALUES(?,?,?,?)',('q-two','lead',json.dumps(self.report),1001))
        self.assertFalse(m.views(self.s)['lead']['current'])
        self.assertIsNone(m.views(self.s)['lead']['review'])
        with self.assertRaises(m.Conflict): m.review(self.s,'lead',value,'accepted')

    def test_concurrent_record_change_cannot_be_overwritten(self):
        self.s.x('UPDATE leads SET draft=? WHERE id=?',('Owner changed this text','lead'))
        with self.assertRaises(m.Conflict): self.publish()
        self.assertEqual(self.s.lead('lead')['draft'],'Owner changed this text')
        self.assertEqual(self.s.one('SELECT count(*) n FROM events')['n'],0)

    def test_critic_rejection_and_unknown_claim_reference_do_not_publish(self):
        for field,value in (('approved',False),('supported_fact_ids',[0,99])):
            cp = copy.deepcopy(self.cp);cp['critique']['output'][field] = value;cp['draft']['output']['audit'][field] = value
            m._save(self.s,self.jid,cp)
            with self.assertRaises(m.Conflict): self.publish()
        self.assertIsNone(self.s.lead('lead')['drafts'])

    def test_tampered_draft_metadata_cannot_reuse_the_owner_review(self):
        self.publish()
        value = m.content_digest(self.s.lead('lead'))
        m.review(self.s,'lead',value,'accepted')
        drafts = json.loads(self.s.lead('lead')['drafts']);drafts['used_fact_ids'] = [99]
        self.s.x('UPDATE leads SET drafts=? WHERE id=?',(json.dumps(drafts),'lead'))
        with self.assertRaises(m.Conflict): m.review(self.s,'lead',value,'accepted')
        self.assertFalse(m.views(self.s)['lead']['current'])

    def test_uncertain_response_is_not_requeued(self):
        cp = copy.deepcopy(self.cp);cp['critique'] = {'state':'calling'}
        m._save(self.s,self.jid,cp)
        self.assertEqual(m.recover(self.s),[])
        self.assertEqual(self.s.one('SELECT status FROM jobs WHERE id=?',(self.jid,))['status'],'failed')

    def test_same_key_cannot_change_workflow_or_owner_note(self):
        self.assertEqual(m.start(self.s,'lead','source-boundary-request',source='qualification'),(self.jid,False))
        for kwargs in ({'source':'research'}, {'source':'qualification','note':'A different note'}):
            with self.assertRaises(m.Conflict): m.start(self.s,'lead','source-boundary-request',**kwargs)

    def test_capability_change_invalidates_existing_draft(self):
        self.publish()
        with patch.object(p.qualification,'capabilities',return_value=[{'id':'appointment','capability':'A changed scope','honest_limit':'Changed'}]):
            self.assertFalse(m.views(self.s)['lead']['current'])
