"""Recorded evidence must remain bound to input; no live HTTP requests."""
import hashlib
import json
import unittest
from scripts.pablo_local_draft import recorded_outcome


class RecordedDraftTests(unittest.TestCase):
    def fixture(self):
        params = {'name': 'note', 'format': 'txt', 'content': 'fixture'}
        digest = hashlib.sha256(json.dumps(['local_draft', params | {'request_id': 'fixture'}], sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        sha = hashlib.sha256(b'fixture').hexdigest()
        result = {'request_id': 'fixture', 'status': 'SUCCESS', 'outcome_verified': True,
                  'outcome_evidence': {'request_id': 'fixture', 'input_digest': digest,
                    'method': 'independent_file_read', 'status': 'matched',
                    'expected_sha256': sha, 'observed_sha256': sha, 'expected_bytes': 7, 'observed_bytes': 7}}
        record = {'task_id': 'fixture', 'worker_id': 'pablo-windows-node-01', 'recorded_status': 'unverified', 'result': json.dumps(result)}
        return params, result, record

    def test_matching_file_does_not_promote_bridge_status(self):
        params, result, record = self.fixture()
        proof = recorded_outcome('fixture', params, record)
        self.assertTrue(proof['outcome_verified'])
        self.assertEqual(proof['bridge_recorded_status'], 'unverified')
        self.assertFalse(proof['delivered'])

    def test_changed_input_and_forged_proof_never_pass(self):
        params, result, record = self.fixture()
        self.assertFalse(recorded_outcome('fixture', params | {'content': 'edited'}, record)['outcome_verified'])
        for field, bad in [('input_digest', 'wrong'), ('method', 'worker_claim'), ('expected_bytes', '7'), ('request_id', 'other')]:
            with self.subTest(field=field):
                changed = result | {'outcome_evidence': result['outcome_evidence'] | {field: bad}}
                self.assertFalse(recorded_outcome('fixture', params, record | {'result': json.dumps(changed)})['outcome_verified'])

    def test_missing_broken_result_and_wrong_worker_fail_closed(self):
        params, result, record = self.fixture()
        for bad in [None, '{', '[]', '{}']:
            self.assertFalse(recorded_outcome('fixture', params, record | {'result': bad})['outcome_verified'])
        self.assertFalse(recorded_outcome('fixture', params, record | {'worker_id': 'other'})['outcome_verified'])


if __name__ == '__main__':
    unittest.main()
