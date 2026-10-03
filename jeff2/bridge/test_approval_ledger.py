from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import tempfile
import unittest

from approval_ledger import ApprovalLedger, ApprovalConflict, digest

class UnifiedDecisionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.clock=[1000.]; self.path=Path(self.tmp.name)/'ledger.db'
        self.ledger=ApprovalLedger(self.path,clock=lambda:self.clock[0]); self.ledger.initialize()
        self.binding={'task_id':'one','action':'send','recipient':'fixture.invalid','channel':'fixture','input_digest':digest({'text':'fixture'})}

    def request(self): return self.ledger.request('node','request-1',self.binding,1100)

    def approved(self):
        row=self.request(); return self.ledger.decide(row['approval_id'],row['input_digest'],'42',True)

    def test_same_explicit_binding_shares_decision_across_sources(self):
        one=self.request(); two=self.ledger.request('panel','approval-2',self.binding,1100)
        self.assertEqual(one['approval_id'],two['approval_id']); self.assertEqual(len(self.ledger.queue()),1)
        changed=dict(self.binding,recipient='different.invalid')
        third=self.ledger.request('panel','approval-3',changed,1100)
        self.assertNotEqual(one['approval_id'],third['approval_id'])

    def test_changed_context_revokes_old_card(self):
        one=self.approved(); changed=dict(self.binding,input_digest=digest('changed'))
        self.ledger.request('node','request-1',changed,1100)
        self.assertEqual(self.ledger.get(one['approval_id'])['status'],'revoked')
        with self.assertRaises(ApprovalConflict): self.ledger.claim(one['approval_id'],self.binding,'worker')

    def test_racing_consumers_only_one_claim_and_restart_cannot_retry(self):
        row=self.approved()
        def claim(i):
            try: return self.ledger.claim(row['approval_id'],self.binding,'worker-'+str(i))
            except ApprovalConflict: return None
        with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(claim,range(2)))
        winner=next(r for r in results if r); self.assertEqual(sum(r is not None for r in results),1)
        reopened=ApprovalLedger(self.path,clock=lambda:self.clock[0])
        with self.assertRaises(ApprovalConflict): reopened.claim(row['approval_id'],self.binding,'new-worker')
        reopened.complete(row['approval_id'],winner['claim_id'],winner['claimed_by'],'execution_only')
        with self.assertRaises(ApprovalConflict): reopened.complete(row['approval_id'],winner['claim_id'],winner['claimed_by'],'again')

    def test_expiry_at_boundary_is_durable_and_not_renewed_by_read(self):
        row=self.request(); self.clock[0]=1100
        with self.assertRaises(ApprovalConflict): self.ledger.decide(row['approval_id'],row['input_digest'],'42',True)
        self.assertEqual(self.ledger.get(row['approval_id'])['status'],'expired'); self.assertEqual(self.ledger.queue(),[])
        self.assertEqual(self.request()['status'],'expired')

    def test_wrong_digest_and_incomplete_context_refused(self):
        row=self.request()
        with self.assertRaises(ApprovalConflict): self.ledger.decide(row['approval_id'],'0'*64,'42',True)
        with self.assertRaises(ApprovalConflict): self.ledger.request('node','missing',{},1100)

    def test_binding_and_audit_cannot_be_rewritten(self):
        row=self.request()
        with sqlite3.connect(self.path) as db:
            with self.assertRaises(sqlite3.IntegrityError): db.execute("UPDATE approval_records SET recipient='other'")
            with self.assertRaises(sqlite3.IntegrityError): db.execute('DELETE FROM approval_audit')
