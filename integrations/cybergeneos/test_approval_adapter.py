from pathlib import Path
import sys
import tempfile
import types
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'pablo'))
sys.path.insert(0,'/home/hermes/cybergeneos/docs')
from cybergeneos.server.store import Store
from test_approval_adapters import LedgerClient
from approval_ledger import ApprovalLedger
from approval_adapter import install
from install_approval_adapter import patch

class PanelTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.store=Store(Path(self.temp.name)/'panel.db')
        self.client=LedgerClient({});self.client.ledger=ApprovalLedger(Path(self.temp.name)/'ledger.db');self.client.ledger.initialize()
        def act(aid,action,body):
            if action=='edit':self.store.x('UPDATE approvals SET text=? WHERE id=?',(body['text'],aid))
            else:self.store.decide(aid,{'approve':'Onaylandı','reject':'Reddedildi','sent':'Gönderildi'}[action])
            return 200,{'ok':True}
        self.app=types.SimpleNamespace(store=self.store,act_approval=act)
        self.adapter=install(self.app,self.client,'42')
        self.aid=self.store.create_approval({'channel':'email','target':'fixture@example.test','text':'fixture draft'})

    def test_only_authenticated_owner_reviews_and_manual_send_remains_manual(self):
        self.assertEqual(self.app.act_approval(self.aid,'approve',{},actor='jeff')[0],409)
        self.assertEqual(self.app.act_approval(self.aid,'sent',{},actor='bilal')[0],409)
        self.assertEqual(self.app.act_approval(self.aid,'approve',{},actor='bilal')[0],200)
        self.assertEqual(self.app.act_approval(self.aid,'approve',{},actor='bilal')[0],409)
        self.assertEqual(self.app.act_approval(self.aid,'sent',{},actor='bilal')[0],200)

    def test_edit_revokes_old_and_direct_database_edit_blocks_review(self):
        old=self.store.one('SELECT canonical_id FROM canonical_approval_links WHERE local_id=?',(self.aid,))['canonical_id']
        self.assertEqual(self.app.act_approval(self.aid,'edit',{'text':'new reviewed draft'},actor='bilal')[0],200)
        self.assertEqual(self.client.ledger.get(old)['status'],'revoked')
        self.store.x('UPDATE approvals SET text=? WHERE id=?',('silent edit',self.aid))
        self.assertEqual(self.app.act_approval(self.aid,'approve',{},actor='bilal')[0],409)

    def test_expiry_and_legacy_are_not_local_authority(self):
        self.adapter.clock=lambda:1e12
        self.adapter.decay()
        self.assertEqual(self.app.act_approval(self.aid,'approve',{},actor='bilal')[0],409)
        self.assertEqual(self.store.approval(self.aid)['status'],'Süresi doldu')

    def test_live_source_patch_is_guarded_and_idempotent(self):
        source=Path('/home/hermes/cybergeneos/docs/cybergeneos/server/app.py').read_text()
        modified=patch(source);compile(modified,'app.py','exec')
        self.assertEqual(patch(modified),modified)
        with self.assertRaises(RuntimeError):patch('changed source')

if __name__=='__main__':unittest.main()
