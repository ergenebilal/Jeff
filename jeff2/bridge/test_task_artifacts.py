"""Durable drafts, independent outcomes, owner approval and crash recovery."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).parent))
from task_contract import ArtifactStep, TaskCreate, TaskLedger, TaskConflict
from task_artifacts import ArtifactStore, DraftWorker


def request(approval=False, task_id='draft-1'):
    return TaskCreate(task_id=task_id, source='panel', actor_id='42', goal='Company research and draft',
                      success_criteria=['artifact_sha256_matches'], risk_level='low',
                      side_effect_class='none', approval_required=approval, assigned_worker='jeff-server',
                      steps=[ArtifactStep(name='research', content='Sources and verified facts'),
                             ArtifactStep(name='message', content='Personal draft — never sent')])


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.clock = [1000.0]
        self.ledger = TaskLedger(self.root / 'ledger.db', clock=lambda: self.clock[0])
        self.ledger.initialize()
        self.artifacts = ArtifactStore(self.root / 'artifacts')
        self.worker = DraftWorker(self.ledger, self.artifacts)

    def ready(self, approval=False):
        task = self.ledger.create(request(approval))
        self.ledger.plan(task['task_id'], 'panel')
        self.ledger.queue(task['task_id'], 'panel')
        return task

    def test_actual_files_and_independent_hashes_are_required(self):
        self.ready()
        result = self.worker.run_task('draft-1')
        self.assertEqual(result['status'], 'verified')
        self.assertTrue(result['verification_result']['outcome_ok'])
        self.assertEqual([r['status'] for r in self.ledger.checkpoints('draft-1')], ['verified', 'verified'])
        for step in result['steps']:
            self.assertEqual(self.artifacts.read('draft-1', step).decode(), step['content'])
        # A finished task is not scheduled again.
        self.assertEqual(self.worker.run_once(), [])

    def test_forged_success_missing_file_cannot_verify(self):
        self.ready()
        self.ledger.claim('draft-1', 'jeff-server'); self.ledger.start('draft-1', 'jeff-server')
        self.ledger.finish('draft-1', 'jeff-server', {'request_id': 'draft-1', 'status': 'SUCCESS', 'verified': True})
        result = self.ledger.verify('draft-1', lambda: {'status_code': 200, 'status': 'ok'}, self.artifacts.observe)
        self.assertEqual(result['status'], 'escalated')
        self.assertFalse(result['verification_result']['outcome_ok'])

    def test_changed_file_fails_even_when_the_worker_said_success(self):
        self.ready()
        task = self.ledger.claim('draft-1', 'jeff-server'); self.ledger.start('draft-1', 'jeff-server')
        for step in task['steps']: self.artifacts.write('draft-1', step)
        self.ledger.finish('draft-1', 'jeff-server', {'request_id': 'draft-1', 'status': 'SUCCESS'})
        self.artifacts.path('draft-1', task['steps'][1]).write_text('changed')
        self.assertEqual(self.ledger.verify('draft-1', lambda: {}, self.artifacts.observe)['status'], 'failed')

    def test_crash_after_first_publication_resumes_without_rewrite(self):
        self.ready()
        task = self.ledger.claim('draft-1', 'jeff-server', 5); self.ledger.start('draft-1', 'jeff-server')
        self.artifacts.write('draft-1', task['steps'][0])  # Crash before checkpoint was saved.
        path = self.artifacts.path('draft-1', task['steps'][0]); before = path.stat().st_mtime_ns
        self.clock[0] += 6
        reopened = TaskLedger(self.root / 'ledger.db', clock=lambda: self.clock[0])
        result = DraftWorker(reopened, self.artifacts).run_task('draft-1')
        self.assertEqual(result['status'], 'verified')
        self.assertEqual(result['attempt'], 2)
        self.assertEqual(path.stat().st_mtime_ns, before)
        self.assertIn('reconciling', [r['to_status'] for r in reopened.events('draft-1')])

    def test_recovery_never_overwrites_a_conflicting_file(self):
        task = self.ready()
        path = self.artifacts.path('draft-1', task['steps'][0]); path.write_text('unrelated content')
        self.assertEqual(self.worker.run_task('draft-1')['status'], 'escalated')
        self.assertEqual(path.read_text(), 'unrelated content')

    def test_explicit_approval_is_bound_to_owner_chat_digest_and_lifetime(self):
        self.ready(True)
        self.assertEqual(self.worker.run_task('draft-1')['status'], 'waiting_approval')
        task = self.ledger.get('draft-1'); aid = task['approval_id']
        self.assertEqual(self.ledger.request_approval('draft-1')['approval_id'], aid)
        for owner, user, chat, digest in [('', '42', '42', task['input_digest']),
                                         ('42', '7', '42', task['input_digest']),
                                         ('42', '42', '7', task['input_digest']),
                                         ('42', '42', '42', '0' * 64)]:
            with self.assertRaises(TaskConflict): self.ledger.decide_approval(aid, owner, user, chat, digest, True)
        self.ledger.decide_approval(aid, '42', '42', '42', task['input_digest'], True)
        self.assertEqual(self.worker.run_task('draft-1')['status'], 'verified')
        with self.assertRaises(TaskConflict): self.ledger.decide_approval(aid, '42', '42', '42', task['input_digest'], True)

    def test_expired_approval_can_be_renewed_but_old_card_cannot_run(self):
        task = self.ready(True)
        approval = self.ledger.request_approval('draft-1', ttl=30)
        self.clock[0] += 31
        with self.assertRaises(TaskConflict):
            self.ledger.decide_approval(approval['approval_id'], '42', '42', '42', task['input_digest'], True)
        new = self.ledger.request_approval('draft-1')
        self.assertNotEqual(new['approval_id'], approval['approval_id'])
        self.assertEqual(self.ledger.get('draft-1')['status'], 'waiting_approval')

    def test_owner_rejection_does_not_create_any_artifact(self):
        task = self.ready(True); approval = self.ledger.request_approval('draft-1')
        result = self.ledger.decide_approval(approval['approval_id'], '42', '42', '42', task['input_digest'], False)
        self.assertEqual(result['status'], 'cancelled')
        self.assertEqual(self.worker.run_once(), [])
        self.assertEqual(list(self.artifacts.root.iterdir()), [])

    def test_cancel_revokes_pending_card_and_expiry_is_in_shared_inventory(self):
        from datetime import datetime, timezone
        from scripts.approval_inventory import collect
        self.ready(True); self.ledger.request_approval('draft-1', ttl=30)
        self.clock[0] += 31
        counts = collect(self.root / 'ledger.db', now=datetime.fromtimestamp(self.clock[0], timezone.utc))
        self.assertEqual((counts['waiting'], counts['expired']), (0, 1))
        self.ledger.cancel('draft-1', 'panel')
        self.assertEqual(self.ledger.approvals(), [])

    def test_paths_commands_and_unsupported_delivery_cannot_enter_the_plan(self):
        for data in ({'name': '../outside', 'content': 'x'}, {'name': 'x', 'kind': 'send', 'content': 'x'},
                     {'name': 'x', 'path': '/etc/passwd', 'content': 'x'}):
            with self.assertRaises(ValueError): ArtifactStep(**data)
        with self.assertRaises(ValueError): TaskCreate.model_validate(request().model_dump() | {'assigned_worker': 'pablo'})

    def test_persisted_plan_tampering_prevents_execution(self):
        self.ready()
        with self.ledger.connect() as db:
            db.execute("UPDATE task_records SET goal='Changed goal' WHERE task_id='draft-1'")
        with self.assertRaises(TaskConflict): self.worker.run_task('draft-1')
        self.assertEqual(list(self.artifacts.root.iterdir()), [])

    def test_active_lease_and_cancelled_task_are_not_replayed(self):
        self.ready()
        self.ledger.claim('draft-1', 'jeff-server', 30)
        self.assertEqual(self.worker.run_once(), [])
        self.ledger.cancel('draft-1', 'panel')
        self.clock[0] += 31
        self.assertEqual(self.worker.run_once(), [])

    def test_existing_legacy_digest_is_preserved_on_migration(self):
        from task_contract import digest
        body = TaskCreate(source='legacy', goal='Ping', success_criteria=['pablo_health_ok'], risk_level='low',
                          side_effect_class='none', approval_required=False)
        immutable = body.model_dump(exclude={'task_id', 'input_digest', 'steps'})
        self.assertEqual(self.ledger.create(body)['input_digest'], digest(immutable))

    def test_final_verification_resumes_after_restart(self):
        self.ready(); task = self.ledger.claim('draft-1', 'jeff-server'); self.ledger.start('draft-1', 'jeff-server')
        for step in task['steps']: self.artifacts.write('draft-1', step)
        self.ledger.finish('draft-1', 'jeff-server', {'request_id': 'draft-1', 'status': 'SUCCESS'})
        self.assertEqual(self.worker.run_task('draft-1')['status'], 'verified')

    def test_approval_gateway_key_is_separate_from_agent_key(self):
        import asyncio
        import jeff_bridge_api as api
        body = api.ApprovalDecisionRequest(user_id='42', chat_id='42', input_digest='0'*64, decision='approve')
        with mock.patch.object(api, 'BRIDGE_KEY', 'fixture-agent'), mock.patch.dict('os.environ', APPROVAL_DECISION_KEY='fixture-agent'):
            with self.assertRaises(api.HTTPException) as error:
                asyncio.run(api.approval_decision('a', body, 'fixture-agent'))
            self.assertEqual(error.exception.status_code, 401)


if __name__ == '__main__':
    unittest.main()
