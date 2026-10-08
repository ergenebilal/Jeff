"""Evidence boundaries, authenticated GET-only transport, and the real journal producer."""
import contextlib
from copy import deepcopy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

from scripts import pablo_outcome_evidence as reader

SHA = 'a' * 64
DIGEST = 'b' * 64


def receipt():
    return {'request_id': 'new', 'status': 'SUCCESS', 'outcome_verified': True,
            'result': {'delivered': False, 'path': 'private/never-output', 'content': 'never-output'},
            'outcome_evidence': {'method': 'independent_file_read', 'request_id': 'new',
                'input_digest': DIGEST, 'expected_sha256': SHA, 'observed_sha256': SHA,
                'expected_bytes': 8, 'observed_bytes': 8, 'observed_at': 1000, 'status': 'matched'}}


def project(value, **changes):
    criteria = dict(task_id='new', input_digest=DIGEST, expected_sha256=SHA,
                    expected_bytes=8, execution_state='recorded', now=1200)
    criteria.update(changes)
    return reader.evidence_view(value, **criteria)


class EvidenceTests(unittest.TestCase):
    def test_positive_is_only_dated_bytes_never_delivery_current_truth_or_authority(self):
        result = project(receipt())
        self.assertEqual(result['new_task_outcome'], 'matched_at_observation')
        self.assertTrue(result['observed_outcome_verified'])
        for field in ('current_file_outcome_verified', 'customer_delivery_verified',
                      'semantic_quality_verified', 'execution_authorized', 'reexecution_authorized', 'fresh_file_read'):
            self.assertIs(result[field], False)
        self.assertNotIn('never-output', json.dumps(result))

    def test_same_bytes_or_method_cannot_transfer_success_to_new_job(self):
        for changes in ({'task_id': 'other'}, {'input_digest': 'c' * 64},
                        {'expected_sha256': 'd' * 64}, {'expected_bytes': 9}):
            with self.subTest(changes=changes):
                result = project(receipt(), **changes)
                self.assertEqual(result['new_task_outcome'], 'binding_mismatch')
                self.assertFalse(result['observed_outcome_verified'])
                self.assertIsNotNone(result['historical_measurement'])

    def test_proposal_history_and_interruption_never_become_completed(self):
        self.assertEqual(project(receipt(), execution_state='proposed')['new_task_outcome'], 'not_run')
        for state in ('OUTCOME_UNKNOWN', 'IN_PROGRESS'):
            value = receipt(); value['status'] = state
            self.assertEqual(project(value)['new_task_outcome'], 'unknown')
        self.assertEqual(project(receipt(), execution_state='unknown')['new_task_outcome'], 'unknown')

    def test_wrong_file_despite_success_process_has_mismatch(self):
        value = receipt(); value['outcome_evidence']['observed_sha256'] = 'c' * 64
        value['result']['exit_code'] = 0
        self.assertEqual(project(value)['new_task_outcome'], 'mismatch')
        self.assertFalse(project(value)['observed_outcome_verified'])

    def test_process_label_and_unsupported_plan_are_insufficient(self):
        for value in ({'request_id': 'new', 'status': 'SUCCESS', 'outcome_verified': True,
                       'result': {'exit_code': 0}}, receipt()):
            if 'outcome_evidence' in value:
                value['outcome_evidence']['method'] = 'independent_plan_file_reads'
            self.assertEqual(project(value)['new_task_outcome'], 'unknown')

    def test_receipt_lies_wrong_types_dates_and_identity_cannot_verify(self):
        mutations = [('outcome_verified', 1), ('completion_authority', False), ('status', 'CANCELLED')]
        for key, value in mutations:
            row = receipt(); row[key] = value
            self.assertFalse(project(row)['observed_outcome_verified'])
        for key, value in [('observed_bytes', True), ('observed_at', True), ('observed_at', 1201),
                           ('observed_at', float('inf')), ('observed_at', None), ('observed_sha256', 'x'),
                           ('status', 'mismatch'), ('request_id', 'another')]:
            row = receipt(); row['outcome_evidence'][key] = value
            self.assertFalse(project(row)['observed_outcome_verified'])

    def test_invalid_criteria_rejected_before_transport(self):
        argv = ['--task-id', '../other', '--input-digest', DIGEST, '--expected-sha256', SHA,
                '--expected-bytes', '8', '--execution-state', 'recorded']
        with mock.patch.object(reader, 'load_record') as load, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(reader.main(argv), 1)
            load.assert_not_called()
        for changes in ({'expected_bytes': True}, {'input_digest': 'unknown'}, {'execution_state': 'done'}):
            with self.assertRaises(ValueError):
                project(receipt(), **changes)

    def test_authenticated_get_one_receipt_no_retry_or_private_output(self):
        response = mock.MagicMock(); response.__enter__.return_value = io.BytesIO(json.dumps(receipt()).encode())
        with mock.patch.object(reader, 'bridge_key', return_value='fixture-secret'), mock.patch.object(reader, 'urlopen', return_value=response) as call:
            self.assertEqual(reader.load_record('new'), receipt())
            req = call.call_args.args[0]
            self.assertEqual(req.get_method(), 'GET'); self.assertTrue(req.full_url.endswith('/tasks/new'))
            self.assertIsNone(req.data); self.assertEqual(call.call_count, 1)
            self.assertEqual(req.get_header('X-bridge-key'), 'fixture-secret')
        with mock.patch.object(reader, 'bridge_key', return_value='fixture'), mock.patch.object(reader, 'urlopen', side_effect=TimeoutError()) as call:
            with self.assertRaises(TimeoutError): reader.load_record('new')
            self.assertEqual(call.call_count, 1)

    def test_duplicate_keys_nonfinite_oversized_and_wrong_receipt_rejected(self):
        for raw in ('{"request_id":"new","request_id":"other"}', '{"nested":{"x":1,"x":2}}', '{"x":NaN}'):
            with self.assertRaises(ValueError): reader.strict_json(raw)
        for raw in (b'x' * (reader.MAX_RECEIPT_BYTES + 1), b'{"request_id":"other"}', b'[]'):
            response = mock.MagicMock(); response.__enter__.return_value = io.BytesIO(raw)
            with mock.patch.object(reader, 'bridge_key', return_value='fixture'), mock.patch.object(reader, 'urlopen', return_value=response):
                with self.assertRaises(ValueError): reader.load_record('new')

    def test_real_journal_receipt_and_later_file_change_remain_dated(self):
        # Temporary isolated producer; no production task or journal is written.
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pablo'))
        from pablo_task_guard import TaskGuard, fingerprint
        from pablo_local_drafts import expectation
        with tempfile.TemporaryDirectory() as directory:
            guard = TaskGuard(Path(directory) / 'journal.db', {}, 'fixture', lambda: False, clock=lambda: 1000)
            params = {'name': 'proof', 'format': 'txt', 'content': 'fixture!'}
            result = guard.execute('local_draft', params, 'new')
            self.assertEqual(result['status'], 'SUCCESS')
            expected = expectation('new', params)
            criteria = dict(task_id='new', input_digest=fingerprint('local_draft', params),
                            expected_sha256=expected.sha256, expected_bytes=len(expected.data),
                            execution_state='recorded', now=1200)
            before = reader.evidence_view(guard.get('new'), **criteria)
            self.assertTrue(before['observed_outcome_verified'])
            guard.local_drafts.path('new', expected).write_bytes(b'changed!')
            after = reader.evidence_view(guard.get('new'), **criteria)
            self.assertEqual(before, after)
            self.assertFalse(after['current_file_outcome_verified'])
            self.assertNotEqual(guard.local_drafts.observe('new', expected)['observed_sha256'], expected.sha256)


if __name__ == '__main__':
    unittest.main()
