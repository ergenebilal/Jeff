from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
from scripts.attention_policy import AttentionOutbox,financial_decisions,irreversible_disk_decision
from scripts import system_watchdog as wd

class AttentionTests(unittest.TestCase):
    def test_routine_failures_recovery_and_reminders_do_not_send(self):
        with tempfile.TemporaryDirectory() as temp:
            sender=Mock(return_value=True)
            checks=[wd.Check('http:pablo','PC','sleep',lambda:(False,'sleep')),wd.Check('model','model','fallback',lambda:(False,'degraded'))]
            with patch.object(wd,'default_checks',return_value=checks),patch.object(wd,'telegram_sender',return_value=sender),patch.dict('os.environ',{'ALERT_BOT_TOKEN':'fixture','ALERT_CHAT_ID':'fixture'}):
                for _ in range(2):self.assertEqual(wd.main(['--state',str(Path(temp)/'state.json'),'--bridge-db',str(Path(temp)/'missing.db')]),0)
            sender.assert_not_called()
            self.assertFalse((Path(temp)/'missing.db').exists())

    def test_concurrent_runs_and_restart_send_one_money_decision(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'out.db';sender=Mock(return_value=True)
            item={'id':'one','kind':'money_decision','evidence_ref':'approval:one','deadline':200,'message':'decision'}
            def run(_):return AttentionOutbox(path,lambda:100).dispatch([item],sender)
            run(0)
            with ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(run,range(4)))
            sender.assert_called_once()

    def test_ambiguous_delivery_is_not_fake_success_or_replayed(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'out.db';sender=Mock(side_effect=TimeoutError)
            item={'id':'one','kind':'critical_decision','evidence_ref':'disk:one','deadline':200,'message':'decision'}
            self.assertEqual(AttentionOutbox(path,lambda:100).dispatch([item],sender),0)
            AttentionOutbox(path,lambda:100).dispatch([item],sender);sender.assert_called_once()
            with sqlite3.connect(path) as db:self.assertEqual(db.execute('SELECT status FROM attention_outbox').fetchone()[0],'delivery_unknown')

    def test_financial_evidence_is_action_bound_not_keyword_guess(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'ledger'
            with sqlite3.connect(path) as db:
                db.execute('CREATE TABLE approval_records(approval_id TEXT,action TEXT,recipient TEXT,expires_at REAL,status TEXT)')
                db.executemany('INSERT INTO approval_records VALUES(?,?,?,?,?)',[('one','payment','fixture',200,'pending'),('two','draft_review','payment words',200,'pending'),('three','payment','fixture',99,'pending')])
            self.assertEqual([i['id'] for i in financial_decisions(path,100)],['approval:one'])

    def test_disk_requires_measured_imminent_loss_and_persistence(self):
        state={'disk':{'ok':False,'since':1}}
        usage=lambda p:SimpleNamespace(free=100,used=9999,total=10000)
        self.assertFalse(irreversible_disk_decision(state,100,usage))
        self.assertTrue(irreversible_disk_decision(state,400,usage))
        self.assertFalse(irreversible_disk_decision(state,400,lambda p:SimpleNamespace(free=2**31,used=98,total=100)))

if __name__=='__main__':unittest.main()
