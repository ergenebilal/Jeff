"""Missing source evidence cannot certify an empty canonical approval queue."""
from contextlib import closing
from datetime import datetime,timezone
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from jeff2.bridge.approval_ledger import ApprovalLedger
from scripts import approval_inventory


class ApprovalSnapshotIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'bridge.db';ApprovalLedger(self.path).initialize()
        self.now=datetime(2026,10,4,12,tzinfo=timezone.utc)
        with closing(sqlite3.connect(self.path)) as db,db:
            db.executescript('CREATE TABLE task_records (task_id TEXT,status TEXT,updated_at TEXT);'
                             'CREATE TABLE alfred_heartbeat (id INTEGER);'
                             'CREATE TABLE node_approval_snapshots (node_id TEXT PRIMARY KEY,observed_at REAL,payload TEXT);')

    def save(self,at=None,**changes):
        snapshot=dict(journal_waiting=0,journal_expired=0,journal_complete=True,
                      marketing_waiting=0,marketing_old=0,marketing_complete=True)
        snapshot.update(changes)
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('INSERT OR REPLACE INTO node_approval_snapshots VALUES(?,?,?)',
                       ('pablo',self.now.timestamp() if at is None else at,json.dumps(snapshot)))

    def test_future_snapshot_does_not_certify_complete_coverage(self):
        self.save(at=self.now.timestamp()+3600)
        view=approval_inventory.collect(self.path,self.now)
        self.assertIn('Pablo ve pazarlama onayları',view['unavailable'])

    def test_nonboolean_coverage_is_unknown(self):
        for flag in ('false',1,None):
            with self.subTest(flag=flag):
                self.save(journal_complete=flag)
                self.assertIsNone(approval_inventory.collect(self.path,self.now))

    def test_invalid_counts_do_not_enter_verified_totals(self):
        for field,value in (('journal_waiting',True),('marketing_waiting','0'),
                            ('journal_legacy_expired',-18),('marketing_legacy_expired',1.5),
                            ('notification_delivery_unknown','0')):
            with self.subTest(field=field,value=value):
                self.save(**{field:value})
                self.assertIsNone(approval_inventory.collect(self.path,self.now))

    def test_valid_empty_snapshot_is_complete(self):
        self.save()
        view=approval_inventory.collect(self.path,self.now)
        self.assertEqual(view['waiting'],0);self.assertEqual(view['unavailable'],[])

    def test_explicit_partial_snapshot_names_missing_source(self):
        self.save(marketing_complete=False)
        view=approval_inventory.collect(self.path,self.now)
        self.assertIn('Pazarlama onayları',view['unavailable'])


if __name__=='__main__':unittest.main()
