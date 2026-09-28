"""PR-02 contract regressions against the real task ledger module."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parent))
from task_contract import TaskCreate, TaskLedger, TaskConflict, InvalidTransition


def request(task_id='task-1', side_effect='none'):
    return TaskCreate(
        task_id=task_id, source='test', actor_id='42', session_id='session-1',
        goal='Check Pablo availability', success_criteria=['pablo_health_ok'],
        risk_level='low', side_effect_class=side_effect,
        approval_required=side_effect != 'none', max_attempts=2,
    )


class TaskContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.addCleanup(self.temp.cleanup)
        self.path = str(Path(self.temp.name) / 'tasks.sqlite3')
        self.now = [1000.0]
        self.ledger = TaskLedger(self.path, clock=lambda: self.now[0])
        self.ledger.initialize()

    def ready(self, task_id='task-1', side_effect='none'):
        self.ledger.create(request(task_id, side_effect))
        self.ledger.plan(task_id, 'jeff')
        self.ledger.queue(task_id, 'jeff')

    def test_full_read_only_chain_requires_independent_outcome(self):
        self.ready()
        self.ledger.claim('task-1', 'pablo', lease_seconds=30)
        self.ledger.start('task-1', 'pablo')
        self.ledger.finish('task-1', 'pablo', {'request_id': 'task-1', 'status': 'SUCCESS'})
        final = self.ledger.verify('task-1', health_probe=lambda: {'status_code': 200, 'status': 'ok'})
        self.assertEqual(final['status'], 'verified')
        self.assertEqual([e['to_status'] for e in self.ledger.events('task-1')],
                         ['received', 'planned', 'queued', 'claimed', 'running', 'verifying', 'verified'])
        self.assertEqual(len(self.ledger.evidence('task-1')), 2)

    def test_tool_success_with_outcome_failure_is_not_verified(self):
        self.ready()
        self.ledger.claim('task-1', 'pablo', lease_seconds=30)
        self.ledger.start('task-1', 'pablo')
        self.ledger.finish('task-1', 'pablo', {'request_id': 'task-1', 'status': 'SUCCESS'})
        final = self.ledger.verify('task-1', health_probe=lambda: {'status_code': 503, 'status': 'down'})
        self.assertEqual(final['status'], 'failed')
        self.assertNotEqual(final['verification_result']['outcome_ok'], True)

    def test_model_completion_text_is_not_execution_evidence(self):
        self.ready()
        self.ledger.claim('task-1', 'pablo', lease_seconds=30)
        self.ledger.start('task-1', 'pablo')
        self.ledger.finish('task-1', 'pablo',
                           {'request_id': 'task-1', 'status': 'MODEL_SAYS_DONE',
                            'message': 'Task completed successfully'})
        final = self.ledger.verify('task-1',
                                   health_probe=lambda: {'status_code': 200, 'status': 'ok'})
        self.assertEqual(final['status'], 'failed')
        self.assertFalse(final['verification_result']['execution_ok'])

    def test_invalid_transition_is_audited_without_state_change(self):
        self.ledger.create(request())
        with self.assertRaises(InvalidTransition):
            self.ledger.queue('task-1', 'jeff')
        self.assertEqual(self.ledger.get('task-1')['status'], 'received')
        self.assertEqual(len(self.ledger.events('task-1')), 1)
        self.assertEqual(len(self.ledger.rejections('task-1')), 1)

    def test_duplicate_claim_has_one_lease_owner(self):
        self.ready()
        def claim(worker):
            try:
                self.ledger.claim('task-1', worker, lease_seconds=30)
                return worker
            except TaskConflict:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            winners = list(pool.map(claim, ('pablo-a', 'pablo-b')))
        self.assertEqual(sum(x is not None for x in winners), 1)
        self.assertEqual(self.ledger.get('task-1')['lease_owner'], next(x for x in winners if x))

    def test_expired_side_effect_lease_reconciles_without_reclaim(self):
        self.ready(side_effect='external')
        self.ledger.claim('task-1', 'pablo', lease_seconds=10)
        self.ledger.start('task-1', 'pablo')
        self.now[0] += 11
        with self.assertRaises(TaskConflict):
            self.ledger.claim('task-1', 'pablo', lease_seconds=10)
        self.assertEqual(self.ledger.get('task-1')['status'], 'reconciling')
        self.assertEqual(self.ledger.get('task-1')['attempt'], 1)

    def test_approval_required_waits_then_escalates_after_reconciliation(self):
        self.ready(side_effect='external')
        self.ledger.claim('task-1', 'pablo', lease_seconds=10)
        self.ledger.start('task-1', 'pablo')
        waiting = self.ledger.finish('task-1', 'pablo',
                                     {'request_id': 'task-1', 'status': 'APPROVAL_REQUIRED',
                                      'approval_id': 'fixture-approval'})
        self.assertEqual(waiting['status'], 'waiting_approval')
        self.assertEqual(waiting['approval_id'], 'fixture-approval')
        with self.assertRaises(InvalidTransition):
            self.ledger.verify('task-1', lambda: {'status_code': 200, 'status': 'ok'})
        self.now[0] += 11
        self.assertEqual(self.ledger.reconcile('task-1', 'jeff')['status'], 'reconciling')
        with self.assertRaises(InvalidTransition):
            self.ledger.cancel('task-1', 'jeff')
        self.assertEqual(self.ledger.escalate('task-1', 'jeff', 'Approval recovery needed')['status'],
                         'escalated')

    def test_expired_read_only_lease_recovers_with_new_attempt(self):
        self.ready()
        self.ledger.claim('task-1', 'pablo-a', lease_seconds=10)
        self.now[0] += 11
        recovered = self.ledger.claim('task-1', 'pablo-b', lease_seconds=10)
        self.assertEqual(recovered['lease_owner'], 'pablo-b')
        self.assertEqual(recovered['attempt'], 2)
        self.assertIn('reconciling', [e['to_status'] for e in self.ledger.events('task-1')])

    def test_restart_preserves_evidence_and_events_are_append_only(self):
        self.ready()
        self.ledger.claim('task-1', 'pablo', lease_seconds=30)
        self.ledger.start('task-1', 'pablo')
        self.ledger.finish('task-1', 'pablo', {'request_id': 'task-1', 'status': 'SUCCESS'})
        reopened = TaskLedger(self.path, clock=lambda: self.now[0])
        self.assertEqual(reopened.get('task-1')['status'], 'verifying')
        self.assertEqual(len(reopened.evidence('task-1')), 1)
        with sqlite3.connect(self.path) as db, self.assertRaises(sqlite3.DatabaseError):
            db.execute('DELETE FROM task_events WHERE task_id=?', ('task-1',))


if __name__ == '__main__':
    unittest.main(verbosity=2)
