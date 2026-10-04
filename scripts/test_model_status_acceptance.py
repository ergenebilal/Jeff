"""R01 acceptance: real success time and probe health remain separate evidence."""
from contextlib import closing
import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from scripts import jeff_status

PLUGIN=Path(__file__).resolve().parents[1]/'integrations/model-route-receipts/__init__.py'
spec=importlib.util.spec_from_file_location('status_acceptance_receipts',PLUGIN)
receipts=importlib.util.module_from_spec(spec);spec.loader.exec_module(receipts)


class ModelStatusAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'state.db';self.clock=[1000.]
        self.store=receipts.ReceiptStore(self.path,clock=lambda:self.clock[0])
        self.data={'session_id':'fixture','turn_id':'turn','api_request_id':'call',
                   'provider':'opencode-go','model':'fixture','base_url':'https://fixture.invalid/v1'}

    def call(self,status='succeeded',**changes):
        data=dict(self.data,**changes);self.store.pre(data);self.store.finish(data,status)

    def test_latest_failure_does_not_move_last_success_time(self):
        self.call()
        self.clock[0]=1010;self.call('failed',api_request_id='failed',error={'type':'AuthError'})
        self.assertIn('sonuç: failed',jeff_status.model_route_line(self.path,1100))
        line=jeff_status.model_success_line(self.path,1100)
        self.assertIn('opencode-go',line);self.assertIn('01.01.1970 00:16:40 UTC',line)
        self.assertNotIn('00:16:50',line)

    def test_actual_fallback_reason_and_success_time_are_visible(self):
        self.call('failed',error={'type':'AuthError'})
        self.clock[0]=1010;self.call(provider='proxy')
        self.assertIn('fallback nedeni: AuthError',jeff_status.model_route_line(self.path,1100))
        line=jeff_status.model_success_line(self.path,1100)
        self.assertIn('proxy',line);self.assertIn('01.01.1970 00:16:50 UTC',line)

    def test_running_future_and_inconsistent_receipts_do_not_advance_success(self):
        self.call()
        self.clock[0]=1010;self.store.pre(dict(self.data,api_request_id='running'))
        self.clock[0]=2000;self.call(api_request_id='future')
        with closing(sqlite3.connect(self.path)) as db,db:
            db.execute("UPDATE model_route_receipts SET status='succeeded',started_at=1050,ended_at=1040 WHERE call_id='running'")
        line=jeff_status.model_success_line(self.path,1100)
        self.assertIn('00:16:40 UTC',line)
        self.assertNotIn('00:33:20',line)

    def test_missing_database_is_unknown_and_not_created(self):
        self.assertIn('bilinmiyor',jeff_status.model_success_line(self.path,1100))
        self.assertFalse(self.path.exists())

    def test_no_success_is_unknown(self):
        self.call('failed')
        self.assertIn('bilinmiyor',jeff_status.model_success_line(self.path,1100))

    def test_spare_probe_success_does_not_hide_preferred_failure(self):
        path=Path(self.temp.name)/'health.json'
        path.write_text(json.dumps({'checked_at':1000,'main':'opencode-go',
                                   'routes':[{'route':'opencode-go','ok':False},{'route':'proxy','ok':True}]}))
        line=jeff_status.model_probe_line(path,1100)
        self.assertIn('opencode-go yanıt vermedi',line)
        self.assertIn('proxy',line);self.assertIn('01.01.1970 00:16:40 UTC',line)
        self.assertNotIn('başarılı çağrı',line)

    def test_stale_or_corrupt_probe_is_unknown(self):
        path=Path(self.temp.name)/'health.json'
        for data in ('SECRET corrupt',json.dumps({'checked_at':0,'main':'proxy','routes':[{'route':'proxy','ok':True}]})):
            with self.subTest(data=data):
                path.write_text(data)
                line=jeff_status.model_probe_line(path,3000)
                self.assertIn('bilinmiyor',line);self.assertNotIn('SECRET',line)

    def test_status_screen_contains_all_three_evidence_lines(self):
        screen=jeff_status.build_status(gateway=lambda:'gateway',jobs=lambda:'jobs',reports=lambda:'reports',dog=lambda:[],
            model=lambda:'actual call fixture',model_success=lambda:'real success time fixture',
            model_probe=lambda:'preferred probe fixture')
        for expected in ('actual call fixture','real success time fixture','preferred probe fixture'):
            self.assertIn(expected,screen)


if __name__=='__main__':unittest.main()
