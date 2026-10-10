import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from pablo_task_guard import TaskGuard
from pablo_approval_maintenance import marketing_decay,review_link,connect

class DecayTests(unittest.TestCase):
    def test_eighteen_expired_records_archive_once_and_never_execute(self):
        with tempfile.TemporaryDirectory() as temp:
            executions=[];clock=[100.0]
            guard=TaskGuard(Path(temp)/'db',{'fixture':lambda p:executions.append(p) or {'ok':True}},'42',lambda:True,clock=lambda:clock[0],ttl=10)
            ids=[guard.execute('fixture',{'require_approval':True},str(i))['approval_id'] for i in range(18)]
            clock[0]=110
            self.assertEqual(guard.approval_snapshot()['journal_waiting'],0)
            self.assertEqual(guard.approval_snapshot()['journal_expired'],18)
            for aid in ids:self.assertEqual(guard.approve(aid,42,42)['status'],'REJECTED')
            self.assertFalse(executions)
            with guard.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM approval_archives').fetchone()[0],18)
            self.assertEqual(guard.approval_snapshot()['journal_expired'],18)

    def test_four_old_pending_records_leave_active_queue_preserving_content(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'marketing.db'
            with connect(path) as db:
                db.execute('CREATE TABLE outreach_campaigns(id INTEGER,status TEXT,approval_requested_at TEXT,message_body TEXT)')
                db.executemany('INSERT INTO outreach_campaigns VALUES(?,?,?,?)',[(i,'PENDING_APPROVAL','2020-01-01 00:00:00','original') for i in range(4)])
                db.execute("INSERT INTO outreach_campaigns VALUES(5,'PENDING_APPROVAL',NULL,'new')")
            review_link(path,'marketing_campaign',5,'canonical-new',1e12)
            marketing_decay(path,1e9);marketing_decay(path,1e9)
            with connect(path) as db:
                self.assertEqual(db.execute("SELECT count(*) FROM outreach_campaigns WHERE status='PENDING_APPROVAL'").fetchone()[0],1)
                self.assertEqual(db.execute('SELECT count(*) FROM approval_archives').fetchone()[0],4)
                self.assertEqual(db.execute("SELECT count(*) FROM outreach_campaigns WHERE message_body='original'").fetchone()[0],4)

if __name__=='__main__':unittest.main()
