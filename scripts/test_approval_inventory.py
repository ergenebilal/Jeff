import asyncio
import json
import sqlite3
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

# Also work when invoked alone, without the active runner's PYTHONPATH.
ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / 'jeff2' / 'bridge', ROOT / 'pablo'):
    sys.path.insert(0, str(directory))

from scripts import approval_inventory as inventory
from scripts import morning_report

NOW = datetime(2026, 10, 1, 12, tzinfo=timezone.utc)


class ApprovalInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'bridge.db'
        db = sqlite3.connect(self.path)
        db.executescript("CREATE TABLE task_records(task_id TEXT,status TEXT,updated_at TEXT); "
                         "CREATE TABLE alfred_heartbeat(id INTEGER); "
                         "CREATE TABLE node_approval_snapshots(node_id TEXT PRIMARY KEY,observed_at REAL,payload TEXT);")
        db.commit()
        db.close()

    def snapshot(self, at=None, **changes):
        data = {'journal_waiting': 2, 'journal_expired': 1, 'journal_complete': True,
                'marketing_waiting': 3, 'marketing_old': 1, 'marketing_complete': True}
        data.update(changes)
        db = sqlite3.connect(self.path)
        try:
            db.execute('INSERT INTO node_approval_snapshots VALUES(?,?,?)', ('pablo', at or NOW.timestamp(), json.dumps(data)))
            db.commit()
        finally:
            db.close()

    def test_all_sources_are_counted_without_counting_expired_approvals(self):
        self.snapshot()
        db = sqlite3.connect(self.path)
        db.execute('INSERT INTO task_records VALUES(?,?,?)', ('t', 'waiting_approval', '2026-09-01T12:00:00+00:00'))
        db.commit(); db.close()
        panel = Path(self.temp.name) / 'panel.db'
        db = sqlite3.connect(panel)
        db.execute('CREATE TABLE approvals(status TEXT,created_at INTEGER)')
        db.executemany('INSERT INTO approvals VALUES(?,?)', [('Bekliyor', NOW.timestamp()), ('Onaylandı', NOW.timestamp())])
        db.commit(); db.close()
        result = inventory.collect(self.path, NOW, panel_db=panel)
        self.assertEqual((result['waiting'], result['old'], result['expired']), (7, 2, 1))
        self.assertEqual(result['sources'], {'tasks': 1, 'journal': 2, 'marketing': 3, 'panel': 1})
        self.assertEqual(result['unavailable'], [])

    def test_missing_stale_and_partial_sources_are_never_reported_as_zero(self):
        self.assertIn('Pablo ve pazarlama onayları', inventory.collect(self.path, NOW)['unavailable'])
        self.snapshot(at=NOW.timestamp() - 181)
        self.assertIn('Pablo ve pazarlama onayları', inventory.collect(self.path, NOW)['unavailable'])
        db = sqlite3.connect(self.path)
        db.execute('DELETE FROM node_approval_snapshots'); db.commit(); db.close()
        self.snapshot(marketing_complete=False)
        result = inventory.collect(self.path, NOW, panel_db=Path(self.temp.name) / 'missing.db')
        self.assertEqual(result['waiting'], 2)
        self.assertEqual(result['unavailable'], ['Pazarlama onayları', 'Panel onayları'])
        self.assertFalse((Path(self.temp.name) / 'missing.db').exists())

    def test_report_explains_incomplete_coverage_and_expiry(self):
        self.snapshot(marketing_complete=False)
        counts = inventory.collect(self.path, NOW)
        report = morning_report.build_report(None, counts, None, None, NOW)
        self.assertIn('Onay verisi alınamadı: Pazarlama onayları', report)
        self.assertIn('Süresi dolmuş onay: 1', report)

    def test_journal_snapshot_tracks_expiry_and_consumption(self):
        from pablo_task_guard import TaskGuard
        action = mock.Mock(return_value={'ok': True})
        clock = [10]
        guard = TaskGuard(Path(self.temp.name) / 'journal.db', {'ping': action}, 42, lambda: True, clock=lambda: clock[0], ttl=5)
        req = guard.execute('ping', {'require_approval': True}, 'test')
        self.assertEqual(guard.approval_snapshot()['journal_waiting'], 1)
        clock[0] = 20
        self.assertEqual(guard.approval_snapshot()['journal_expired'], 1)
        self.assertEqual(guard.approve(req['approval_id'], 42, 42)['status'], 'REJECTED')
        self.assertEqual(guard.approval_snapshot()['journal_expired'], 1)

    def test_heartbeat_and_read_api_use_authenticated_shared_view(self):
        import jeff_bridge_api as bridge
        path = str(Path(self.temp.name) / 'api.db')
        with mock.patch.object(bridge, 'DB_PATH', path), mock.patch.object(bridge, 'BRIDGE_KEY', 'fixture-key'):
            asyncio.run(bridge.init_db())
            body = bridge.AlfredHeartbeat(agent='pablo', approval_snapshot=bridge.NodeApprovalSnapshot(
                journal_waiting=2, journal_complete=True, marketing_waiting=3, marketing_complete=True))
            asyncio.run(bridge.alfred_heartbeat(body, 'fixture-key'))
            data = asyncio.run(bridge.approval_inventory('fixture-key'))
            self.assertEqual(data['waiting'], 0)
            self.assertTrue(data['canonical'])
            self.assertTrue(any('mutabakat' in v for v in data['unavailable']))
            with self.assertRaises(bridge.HTTPException):
                asyncio.run(bridge.approval_inventory('wrong-key'))
            with self.assertRaises(ValueError):
                bridge.NodeApprovalSnapshot(journal_waiting=-1)

    def test_canonical_view_preserves_legacy_archive_counts_without_duplicate_waiting(self):
        from approval_ledger import ApprovalLedger
        ledger=ApprovalLedger(self.path);ledger.initialize()
        self.snapshot(journal_waiting=0,marketing_waiting=0,journal_legacy_expired=18,marketing_legacy_expired=3)
        result=inventory.collect(self.path,NOW)
        self.assertEqual(result['waiting'],0);self.assertEqual(result['expired'],21)


if __name__ == '__main__':
    unittest.main()
