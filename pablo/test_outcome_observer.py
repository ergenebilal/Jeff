import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'repo/pablo') if (ROOT/'repo/pablo').exists() else str(ROOT/'pablo'))
from pablo_task_guard import TaskGuard
from pablo_local_drafts import LocalDraftStore, expectation
spec=importlib.util.spec_from_file_location('p64b_observer',Path(__file__).with_name('pablo_outcome_observer.py'))
observer=importlib.util.module_from_spec(spec);spec.loader.exec_module(observer)


class CurrentObservationTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.root=Path(temp.name);self.journal=self.root/'journal.db';self.rid='fixture'
        self.params={'name':'proof','format':'txt','content':'private fixture bytes'}
        self.guard=TaskGuard(self.journal,{},'fixture',lambda:False,clock=lambda:1000)
        self.guard.execute('local_draft',self.params,self.rid)
        self.expected=expectation(self.rid,self.params)
        self.file=self.guard.local_drafts.path(self.rid,self.expected)

    def observe(self):
        return observer.observe_current(self.journal,self.rid,clock=lambda:1200)

    def journal_hash(self):
        return hashlib.sha256(self.journal.read_bytes()).hexdigest()

    def test_positive_reads_current_bytes_without_journal_event_or_file_write(self):
        before=self.journal_hash();mtime=self.file.stat().st_mtime_ns
        with mock.patch.object(LocalDraftStore,'write',side_effect=AssertionError('write')):
            result=self.observe()
        self.assertEqual(result['status'],'matched');self.assertTrue(result['file_bytes_matched_at_observation'])
        self.assertEqual(before,self.journal_hash());self.assertEqual(mtime,self.file.stat().st_mtime_ns)
        for key in ('journal_status_updated','execution_authorized','reexecution_authorized',
                    'customer_delivery_verified','semantic_quality_verified'):
            self.assertIs(result[key],False)
        self.assertNotIn(str(self.root),json.dumps(result));self.assertNotIn(self.params['content'],json.dumps(result))

    def test_file_changed_after_old_success_is_now_mismatch(self):
        self.file.write_bytes(b'changed bytes')
        old=self.guard.get(self.rid);self.assertTrue(old['outcome_verified'])
        before=self.journal_hash();result=self.observe()
        self.assertEqual(result['status'],'mismatch');self.assertEqual(before,self.journal_hash())
        self.assertEqual(self.guard.get(self.rid),old)

    def test_unknown_execution_can_have_matching_file_without_updating_status(self):
        with self.guard.connect() as db:db.execute("UPDATE requests SET status='OUTCOME_UNKNOWN' WHERE id=?",(self.rid,))
        before=self.journal_hash();self.assertEqual(self.observe()['status'],'matched')
        self.assertEqual(before,self.journal_hash())
        with self.guard.connect() as db:self.assertEqual(db.execute('SELECT status FROM requests').fetchone()[0],'OUTCOME_UNKNOWN')

    def test_missing_file_and_missing_journal_do_not_create_or_replay(self):
        self.file.unlink();before=self.journal_hash();self.assertEqual(self.observe()['status'],'unavailable')
        self.assertEqual(before,self.journal_hash())
        missing=self.root/'nonexistent.db'
        self.assertEqual(observer.observe_current(missing,'fixture',clock=lambda:1200)['status'],'unavailable')
        self.assertFalse(missing.exists())

    def test_active_writer_is_deferred_without_reading_a_missing_file(self):
        with self.guard.connect() as db:
            db.execute("UPDATE requests SET status='IN_PROGRESS',observation_after=1300 WHERE id=?",(self.rid,))
        self.file.unlink();before=self.journal_hash()
        with mock.patch.object(LocalDraftStore,'observe',side_effect=AssertionError('premature read')):
            self.assertEqual(self.observe()['status'],'deferred')
        self.assertEqual(before,self.journal_hash())

    def test_changed_input_or_duplicate_stored_keys_do_not_verify(self):
        for raw in (json.dumps(self.params|{'content':'new bytes'}), '{"content":"x","content":"y"}'):
            with self.guard.connect() as db:db.execute('UPDATE requests SET params=? WHERE id=?',(raw,self.rid))
            before=self.journal_hash();self.assertEqual(self.observe()['status'],'unavailable');self.assertEqual(before,self.journal_hash())

    def test_binding_change_during_file_read_invalidates_observation(self):
        original=LocalDraftStore.observe
        def changed(store,rid,expected):
            result=original(store,rid,expected)
            with self.guard.connect() as db:db.execute('UPDATE requests SET digest=? WHERE id=?',('a'*64,rid))
            return result
        with mock.patch.object(LocalDraftStore,'observe',changed):
            result=self.observe()
        self.assertEqual(result['status'],'unavailable');self.assertIsNone(result['observed_sha256'])

    def test_unsupported_action_does_not_read_or_publish(self):
        with self.guard.connect() as db:db.execute("UPDATE requests SET action='shell' WHERE id=?",(self.rid,))
        before=self.journal_hash()
        with mock.patch.object(LocalDraftStore,'observe',side_effect=AssertionError('unsupported read')):
            self.assertEqual(self.observe()['status'],'unsupported')
        self.assertEqual(before,self.journal_hash())

    def test_directory_cannot_supply_file_evidence(self):
        self.file.unlink();self.file.mkdir();before=self.journal_hash()
        self.assertEqual(self.observe()['status'],'unavailable');self.assertEqual(before,self.journal_hash())

    @unittest.skipUnless(os.name=='posix','Real symlink needs Linux; Windows may lack link privileges')
    def test_redirected_file_cannot_supply_matching_bytes(self):
        target=self.root/'outside';target.write_bytes(self.expected.data)
        self.file.unlink();self.file.symlink_to(target);before=self.journal_hash()
        self.assertEqual(self.observe()['status'],'unavailable');self.assertEqual(before,self.journal_hash())

    def test_file_change_between_stat_and_open_is_unavailable_not_accepted(self):
        original=os.open
        def changed(path,*args,**kwargs):
            self.file.write_bytes(b'changed during read with different length')
            return original(path,*args,**kwargs)
        before=self.journal_hash()
        with mock.patch('pablo_local_drafts.os.open',changed):
            result=self.observe()
        self.assertEqual(result['status'],'unavailable');self.assertEqual(before,self.journal_hash())

    def test_invalid_identity_clock_and_future_window(self):
        for rid in ('../fixture','',True):
            with self.assertRaises(ValueError):observer.observe_current(self.journal,rid,clock=lambda:1200)
        for value in (True,float('inf'),0):
            with self.assertRaises(ValueError):observer.observe_current(self.journal,self.rid,clock=lambda:value)
        with self.guard.connect() as db:db.execute('UPDATE requests SET observation_after=-1 WHERE id=?',(self.rid,))
        self.assertEqual(self.observe()['status'],'unavailable')


if __name__=='__main__':unittest.main()
