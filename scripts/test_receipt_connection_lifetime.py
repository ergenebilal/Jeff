"""Real SQLite faults must roll back and release the recorder connection."""
from contextlib import closing
import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

SOURCE=Path(__file__).resolve().parents[1]/'integrations/model-route-receipts/__init__.py'
spec=importlib.util.spec_from_file_location('receipt_lifetime',SOURCE)
receipts=importlib.util.module_from_spec(spec);spec.loader.exec_module(receipts)


class ReceiptConnectionLifetimeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'state.db'
        self.store=receipts.ReceiptStore(self.path,clock=lambda:1000)
        self.data={'session_id':'fixture','turn_id':'turn','api_request_id':'call',
                   'provider':'opencode-go','model':'fixture','base_url':'https://fixture.invalid/v1'}
        self.connections=[]
        self.addCleanup(lambda:[db.close() for db in self.connections])

    def track(self):
        connect=self.store.connect
        def tracked():
            db=connect();self.connections.append(db);return db
        return patch.object(self.store,'connect',side_effect=tracked)

    def assert_closed(self):
        self.assertTrue(self.connections)
        for db in self.connections:
            with self.assertRaises(sqlite3.ProgrammingError):
                db.execute('SELECT 1')

    def test_success_releases_connections(self):
        with self.track():
            self.store.pre(self.data);self.store.finish(self.data,'succeeded')
        self.assert_closed()

    def test_pre_failure_rolls_back_previous_running_receipt_and_closes(self):
        self.store.pre(self.data)
        with self.track(),self.assertRaises(ValueError):
            self.store.pre(dict(self.data,base_url='https://[invalid'))
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT status FROM model_route_receipts').fetchall(),[('running',)])
        self.assert_closed()

    def test_finish_failure_preserves_receipt_and_closes(self):
        self.store.pre(self.data)
        with self.track(),self.assertRaises(ValueError):
            self.store.finish(dict(self.data,provider='different'),'succeeded')
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('SELECT status FROM model_route_receipts').fetchall(),[('running',)])
        self.assert_closed()

    def test_schema_write_failure_closes_even_before_connect_returns(self):
        with closing(sqlite3.connect(self.path)) as db:
            db.execute('CREATE TABLE fixture (id INTEGER)')
        connect=sqlite3.connect
        def readonly(*args,**kwargs):
            db=connect(self.path.as_uri()+'?mode=ro',uri=True)
            self.connections.append(db);return db
        with patch.object(receipts.sqlite3,'connect',side_effect=readonly),self.assertRaises(sqlite3.OperationalError):
            self.store.connect()
        self.assert_closed()


if __name__=='__main__':unittest.main()
