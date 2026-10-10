from pathlib import Path
import tempfile
import unittest
from pablo_task_guard import TaskGuard
from pablo_notification_policy import reserve,finish
from pablo_approval_maintenance import connect

class NotificationTests(unittest.TestCase):
    def test_routine_approvals_are_quiet_and_money_card_is_not_replayed(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'journal'
            guard=TaskGuard(path,{'payment':lambda p:{'ok':True}},'42',lambda:True,clock=lambda:100,ttl=60)
            aid=guard.execute('payment',{},'money')['approval_id']
            self.assertFalse(reserve(path,aid,'antigravity',now=100))
            self.assertTrue(reserve(path,aid,'payment',now=100))
            finish(path,aid,False)
            self.assertFalse(reserve(path,aid,'payment',now=100))
            with connect(path) as db:self.assertEqual(db.execute('SELECT status FROM approval_notifications').fetchone()[0],'delivery_unknown')
            self.assertFalse(reserve(path,'invented','payment',now=100))

if __name__=='__main__':unittest.main()
