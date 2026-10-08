import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'pablo'))
from pablo_task_guard import TaskGuard
from pablo_task_criterion import read_criterion
from pablo_outcome_observer import observe_current
from scripts.pablo_decision_reader import read_decision


class ReaderTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name); self.journal = self.root/'task-journal.sqlite3'
        self.guard = TaskGuard(self.journal, {}, 'anonymous', lambda: False, clock=lambda: 1000)
        self.guard.execute('local_draft', {'name':'proof', 'format':'txt', 'content':'private anonymous fixture'}, 'fixture')
        def load(rid, suffix):
            return {'/criterion': lambda: read_criterion(self.journal, rid),
                    '': lambda: self.guard.get(rid),
                    '/observation': lambda: observe_current(self.journal, rid, clock=lambda: 1200)}[suffix]()
        self.loader = Mock(side_effect=load)

    def read(self):
        return read_decision('fixture', loader=self.loader, clock=lambda:1201)

    def test_positive_uses_original_input_and_current_evidence_without_mutation(self):
        before = self.journal.read_bytes(); view = self.read()
        self.assertTrue(view['current_file_outcome_verified']); self.assertEqual(view['new_task_outcome'], 'matched_at_observation')
        self.assertEqual(before, self.journal.read_bytes()); self.assertEqual(self.loader.call_count, 4)
        self.assertNotIn('private anonymous fixture', json.dumps(view)); self.assertNotIn(str(self.root), json.dumps(view))
        for k in ('execution_outcome_verified','semantic_quality_verified','customer_delivery_verified','execution_authorized','reexecution_authorized'):
            self.assertIs(view[k], False)

    def test_changed_file_preserves_history_but_rejects_current_success(self):
        from pablo_local_drafts import expectation
        expected = expectation('fixture', {'name':'proof','format':'txt','content':'private anonymous fixture'})
        self.guard.local_drafts.path('fixture', expected).write_bytes(b'changed')
        view = self.read(); self.assertEqual(view['new_task_outcome'], 'mismatch')
        self.assertTrue(view['historical_measurement']['file_bytes_matched_at_observation'])

    def test_unknown_receipt_with_matching_file_stays_unknown(self):
        with self.guard.connect() as db:
            db.execute("UPDATE requests SET status='OUTCOME_UNKNOWN',response=?", (json.dumps(self.guard.response('fixture','OUTCOME_UNKNOWN')),))
        view=self.read(); self.assertTrue(view['current_file_outcome_verified']); self.assertEqual(view['new_task_outcome'], 'unknown')

    def test_unavailable_criterion_stops_before_file_read(self):
        self.loader.side_effect=None; self.loader.return_value={'status':'unavailable'}
        self.assertEqual(self.read()['status'],'unavailable'); self.assertEqual(self.loader.call_count,1)

    def test_criterion_change_during_read_fails_closed(self):
        original=read_criterion(self.journal,'fixture')
        self.loader.side_effect=[original,self.guard.get('fixture'),observe_current(self.journal,'fixture',clock=lambda:1200),original|{'execution_state':'unknown'}]
        self.assertEqual(self.read()['status'],'unavailable'); self.assertFalse(self.read_if_unavailable()['current_file_outcome_verified'])

    def read_if_unavailable(self):
        return read_decision('fixture', loader=Mock(side_effect=OSError('private secret')), clock=lambda:1201)

    def test_transport_errors_have_no_retry_or_exception_text(self):
        self.loader.side_effect=OSError('secret path and key')
        view=self.read(); self.assertEqual(self.loader.call_count,1); self.assertNotIn('secret',json.dumps(view))

    def test_foreign_observation_is_binding_mismatch(self):
        original=read_criterion(self.journal,'fixture'); observation=observe_current(self.journal,'fixture',clock=lambda:1200)
        self.loader.side_effect=[original,self.guard.get('fixture'),observation|{'request_id':'other'},original]
        self.assertEqual(self.read()['new_task_outcome'],'binding_mismatch')

    def test_no_caller_supplied_criterion_or_path(self):
        with self.assertRaises(TypeError): read_decision('fixture', expected_sha256='0'*64)
        with self.assertRaises(ValueError): read_decision('../outside', loader=self.loader)
        self.loader.assert_not_called()


if __name__ == '__main__': unittest.main()
