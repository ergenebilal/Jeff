"""A failed recorder must not let the status view present cached success as current."""
from contextlib import closing
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from scripts import jeff_status

PLUGIN=Path(__file__).resolve().parents[1]/'integrations/model-route-receipts/__init__.py'
spec=importlib.util.spec_from_file_location('receipt_observability',PLUGIN)
receipts=importlib.util.module_from_spec(spec);spec.loader.exec_module(receipts)

class ReceiptObservabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'state.db'
        self.marker=self.path.parent/'model-route-receipt-error.json'
        self.clock=[1000.]
        self.store=receipts.ReceiptStore(self.path,clock=lambda:self.clock[0])
        self.data={'session_id':'fixture','turn_id':'turn','api_request_id':'call',
                   'provider':'opencode-go','model':'fixture','base_url':'https://fixture.invalid/v1'}
        self.store.pre(self.data);self.store.finish(self.data,'succeeded')

    def write_error(self,at=1010,**extra):
        self.marker.write_text(json.dumps(dict(status='unknown',observed_at=at,error_type='OperationalError',**extra)))

    def assert_unknown(self,text):
        self.assertIn('bilinmiyor',text)
        self.assertNotIn('sonuç: succeeded',text)
        self.assertNotIn('SECRET',text)

    def test_real_sqlite_write_failure_creates_marker_and_overrides_cached_success(self):
        connections=[]
        def readonly():
            db=sqlite3.connect(self.path.as_uri()+'?mode=ro',uri=True);db.row_factory=sqlite3.Row
            connections.append(db);return db
        try:
            with patch.object(self.store,'connect',side_effect=readonly),patch.object(receipts,'_store',return_value=self.store),patch.object(receipts.time,'time',return_value=1010):
                receipts.pre(**dict(self.data,api_request_id='failed-write'))
            self.assertTrue(self.marker.is_file())
            self.assertEqual(json.loads(self.marker.read_text())['error_type'],'OperationalError')
            self.assert_unknown(jeff_status.model_route_line(self.path,1020))
        finally:
            for db in connections:db.close()
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT count(*) FROM model_route_receipts').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT status FROM model_route_receipts').fetchone()[0],'succeeded')

    def test_later_completed_receipt_recovers_without_deleting_failure_history(self):
        self.write_error()
        self.assert_unknown(jeff_status.model_route_line(self.path,1020))
        self.clock[0]=1030
        data=dict(self.data,api_request_id='recovered-call')
        self.store.pre(data);self.store.finish(data,'succeeded')
        self.assertIn('sonuç: succeeded',jeff_status.model_route_line(self.path,1040))
        self.assertTrue(self.marker.exists())

    def test_corrupt_or_unreadable_marker_is_unknown_without_leaking_content(self):
        for payload in ('SECRET corrupt marker','[]','null','{"observed_at":"SECRET"}'):
            with self.subTest(payload=payload):
                self.marker.write_text(payload)
                self.assert_unknown(jeff_status.model_route_line(self.path,1020))
        self.marker.unlink();self.marker.mkdir()
        self.assert_unknown(jeff_status.model_route_line(self.path,1020))

    def test_invalid_and_future_marker_timestamps_cannot_hide_telemetry_failure(self):
        for at in (float('nan'),float('inf'),True,2000):
            with self.subTest(at=at):
                self.write_error(at)
                self.assert_unknown(jeff_status.model_route_line(self.path,1020))

    def test_future_receipt_is_not_current_success(self):
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute('UPDATE model_route_receipts SET started_at=2000,ended_at=2010')
        self.assert_unknown(jeff_status.model_route_line(self.path,1020))

    def test_running_call_does_not_clear_recorder_failure(self):
        self.write_error()
        self.clock[0]=1030
        self.store.pre(dict(self.data,api_request_id='still-running'))
        self.assert_unknown(jeff_status.model_route_line(self.path,1040))

    def test_inconsistent_completed_receipt_is_unknown(self):
        for started,ended,status in ((1000,None,'succeeded'),(1000,990,'succeeded'),
                                     (1000,1000,'SECRET'),(1000,1000,'running'),
                                     ('SECRET',1000,'succeeded')):
            with self.subTest(started=started,ended=ended,status=status):
                with closing(sqlite3.connect(self.path)) as db,db:
                    db.execute('UPDATE model_route_receipts SET started_at=?,ended_at=?,status=?',
                               (started,ended,status))
                self.assert_unknown(jeff_status.model_route_line(self.path,1020))

    def test_stale_receipt_stays_historical_and_failed_recovery_stays_failed(self):
        self.assertIn('geçmiş/bitmemiş',jeff_status.model_route_line(self.path,3000))
        self.write_error()
        self.clock[0]=1030
        data=dict(self.data,api_request_id='later-failed',error={'type':'AuthError'})
        self.store.pre(data);self.store.finish(data,'failed')
        text=jeff_status.model_route_line(self.path,1040)
        self.assertIn('sonuç: failed',text)
        self.assertNotIn('sonuç: succeeded',text)

    def test_no_marker_and_old_marker_keep_valid_recent_receipt(self):
        self.assertIn('sonuç: succeeded',jeff_status.model_route_line(self.path,1020))
        self.write_error(990)
        self.assertIn('sonuç: succeeded',jeff_status.model_route_line(self.path,1020))

if __name__=='__main__':unittest.main()
