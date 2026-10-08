from contextlib import closing
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from pablo_task_guard import TaskGuard, fingerprint
from pablo_local_drafts import expectation
from pablo_task_criterion import read_criterion


class CriterionTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name); self.journal = self.root/'task-journal.sqlite3'
        self.params = {'name': 'proof', 'format': 'txt', 'content': 'anonymous synthetic bytes'}
        self.guard = TaskGuard(self.journal, {}, 'anonymous', lambda: False)
        self.guard.execute('local_draft', self.params, 'fixture')

    def test_original_input_not_result_and_read_only(self):
        with self.guard.connect() as db:
            db.execute("UPDATE requests SET response=? WHERE id='fixture'", (json.dumps({'outcome_evidence': {'expected_sha256': '0'*64}}),))
        before = self.journal.read_bytes(); expected = expectation('fixture', self.params)
        view = read_criterion(self.journal, 'fixture')
        self.assertEqual(view['expected_sha256'], expected.sha256)
        self.assertEqual(view['input_digest'], fingerprint('local_draft', self.params))
        self.assertEqual(before, self.journal.read_bytes())
        self.assertNotIn(self.params['content'], json.dumps(view)); self.assertNotIn(str(self.root), json.dumps(view))

    def test_unknown_and_failed_execution_cannot_be_upgraded_by_correct_input(self):
        for status in ('IN_PROGRESS', 'OUTCOME_UNKNOWN', 'ERROR', 'BLOCKED', 'FAILED'):
            with self.subTest(status=status):
                with self.guard.connect() as db: db.execute('UPDATE requests SET status=?', (status,))
                self.assertEqual(read_criterion(self.journal, 'fixture')['execution_state'], 'unknown')

    def test_corrupted_digest_or_duplicate_input_refused(self):
        with self.guard.connect() as db: db.execute("UPDATE requests SET digest=?", ('0'*64,))
        self.assertEqual(read_criterion(self.journal, 'fixture')['status'], 'unavailable')
        with self.guard.connect() as db: db.execute('UPDATE requests SET params=?', ('{"content":"a","content":"b"}',))
        self.assertEqual(read_criterion(self.journal, 'fixture')['status'], 'unavailable')

    def test_unsupported_and_missing_records_or_database_never_create_data(self):
        self.assertEqual(read_criterion(self.journal, 'missing')['status'], 'unavailable')
        with self.guard.connect() as db: db.execute("UPDATE requests SET action='shell'")
        self.assertEqual(read_criterion(self.journal, 'fixture')['status'], 'unsupported')
        missing = self.root/'missing.db'
        self.assertEqual(read_criterion(missing, 'fixture')['status'], 'unavailable'); self.assertFalse(missing.exists())

    def test_invalid_ids_do_not_select_paths(self):
        for rid in ('../outside', 'a/b', 'x'*129, ''):
            with self.assertRaises(ValueError): read_criterion(self.journal, rid)


if __name__ == '__main__': unittest.main()
