"""Real ledger binding/expiry with the production transport and callback boundary."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch,Mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'jeff2/bridge'))
from approval_ledger import ApprovalLedger,ApprovalConflict
from pablo_approval_client import ApprovalClient,ApprovalUnavailable,review_binding
import marketing_telegram_gateway as gateway

class LedgerClient(ApprovalClient):
    def call(self,method,path,body=None,owner=False):
        try:
            if path=='/decisions/request':
                return self.ledger.request(**body)
            aid=path.split('/')[2]
            if method=='GET': return self.ledger.get(aid)
            if path.endswith('/decision'):
                if not owner or body['user_id']!='42' or body['chat_id']!='42':
                    raise ApprovalUnavailable('Owner boundary')
                return self.ledger.decide(aid,body['input_digest'],'42',body['decision']=='approve')
            if path.endswith('/claim'): return self.ledger.claim(aid,body['binding'],body['worker'])
            if path.endswith('/complete'): return self.ledger.complete(aid,**body)
        except ApprovalConflict as exc: raise ApprovalUnavailable(str(exc)) from None

class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.now=[10000.0]
        self.client=LedgerClient({});self.client.ledger=ApprovalLedger(Path(self.temp.name)/'db',clock=lambda:self.now[0])
        self.client.ledger.initialize()
        self.row={'status':'PENDING_APPROVAL','channel':'email','recipient_target':'fixture@example.test','message_body':'approved text'}
        self.binding=review_binding('marketing_campaign',6,self.row)
        self.record=self.client.request('marketing_campaign',6,self.binding,self.now[0]+60,self.now[0])

    def callback(self,row=None,legacy=False):
        with patch.object(gateway,'ApprovalClient',return_value=self.client),patch.object(gateway,'get_telegram_config',return_value={'telegram_default_chat_id':'42'}),patch.object(gateway,'MarketingPipeline') as pipeline,patch.object(gateway,'MarketingPlaybooks') as playbooks,patch.object(gateway,'send_telegram_raw'):
            pipeline.get_campaign.return_value=row or self.row
            playbooks.execute_campaign_delivery.return_value={'ok':True,'status':'SIMULATED'}
            data='mkt_appr:6'+('' if legacy else ':'+self.record['approval_id'])
            result=gateway.handle_marketing_callback('cb',data,42,42)
            return result,pipeline.update_campaign_status.call_count,playbooks.execute_campaign_delivery.call_count

    def test_real_review_is_single_use_and_unsent(self):
        result,updates,runs=self.callback()
        self.assertEqual(result['status'],'SIMULATED');self.assertEqual(runs,1)
        self.assertEqual(self.client.ledger.get(self.record['approval_id'])['status'],'consumed')
        result,updates,runs=self.callback();self.assertEqual(runs,0);self.assertEqual(updates,0)

    def test_edited_recipient_or_text_never_uses_old_card(self):
        for key in ('message_body','recipient_target','channel'):
            result,updates,runs=self.callback(dict(self.row,**{key:'changed'}))
            self.assertEqual(result['status'],'APPROVAL_UNAVAILABLE');self.assertEqual(updates+runs,0)

    def test_expired_or_legacy_card_does_not_regrant(self):
        self.now[0]+=60
        result,updates,runs=self.callback();self.assertEqual(updates+runs,0)
        result,updates,runs=self.callback(legacy=True);self.assertEqual(result['status'],'NEEDS_REVALIDATION')
        self.assertEqual(len(self.client.ledger.queue()),0)

    def test_lost_decision_response_can_only_claim_once(self):
        aid=self.record['approval_id']
        self.client.decide(aid,self.binding,42,42)
        self.client.decide(aid,self.binding,42,42)
        self.client.claim(aid,self.binding,'worker')
        with self.assertRaises(ApprovalUnavailable):self.client.decide(aid,self.binding,42,42)

    def test_no_credential_is_fail_closed(self):
        with self.assertRaises(ApprovalUnavailable): ApprovalClient({}).request('journal','id',self.binding,10060)

if __name__=='__main__':unittest.main()
