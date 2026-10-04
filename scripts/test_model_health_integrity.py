"""Invalid probe evidence must never certify the preferred model route."""
import json
from pathlib import Path
import tempfile
import unittest

from scripts import model_health as health


class ModelHealthIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'health.json'

    def report(self,**changes):
        return dict({'checked_at':1000,'main':'opencode-go','routes':[
            {'route':'opencode-go','ok':True},{'route':'proxy','ok':True}]},**changes)

    def probe(self,report,now=1100):
        self.path.write_text(json.dumps(report))
        return health.watchdog_probe(self.path,now=lambda:now)()

    def test_future_or_nonfinite_timestamp_is_not_healthy(self):
        for timestamp in (2000,float('nan'),float('inf'),-1,'SECRET',None):
            with self.subTest(timestamp=timestamp):
                report=self.report(checked_at=timestamp)
                ok,text=self.probe(report)
                self.assertFalse(ok);self.assertNotIn('SECRET',text)
                self.assertEqual(health.health_snapshot(report,now=lambda:1100)['health_status'],'unknown')

    def test_boolean_timestamp_is_not_a_measurement(self):
        report=self.report(checked_at=True)
        self.assertFalse(self.probe(report,now=2)[0])
        self.assertEqual(health.health_snapshot(report,now=lambda:2)['health_status'],'unknown')

    def test_truthy_values_are_not_success_receipts(self):
        for value in ('false',1,[],None):
            with self.subTest(value=value):
                report=self.report(routes=[{'route':'opencode-go','ok':value}])
                self.assertFalse(self.probe(report)[0])
                self.assertNotEqual(health.summarize(report)[0],'all_ok')
                view=health.health_snapshot(report,now=lambda:1100)
                self.assertEqual(view['health_status'],'unknown')
                self.assertEqual(view['preferred_status'],'unknown')

    def test_missing_preferred_route_does_not_assume_proxy(self):
        report=self.report(routes=[{'route':'proxy','ok':True}]);report.pop('main')
        self.assertFalse(self.probe(report)[0])
        self.assertNotEqual(health.summarize(report)[0],'all_ok')

    def test_invalid_inventory_cannot_certify_health_or_raise(self):
        for report in (None,[],self.report(routes='SECRET'),self.report(routes=[None]),
                       self.report(routes=[{'route':[], 'ok':True}]),
                       self.report(routes=[{'route':'opencode-go','ok':False},
                                           {'route':'opencode-go','ok':True}])):
            with self.subTest(report=report):
                ok,text=self.probe(report)
                self.assertFalse(ok);self.assertNotIn('SECRET',text)
                self.assertEqual(health.health_snapshot(report,now=lambda:1100)['health_status'],'unknown')

    def test_conflicting_credentials_do_not_certify_preferred_route(self):
        report=self.report(env_conflicts=['OPENCODE_GO_API_KEY'])
        view=health.health_snapshot(report,now=lambda:1100)
        self.assertEqual(view['health_status'],'unknown')
        self.assertEqual(view['preferred_status'],'unknown')
        self.assertFalse(self.probe(report)[0])

    def test_valid_primary_failure_and_recovery_still_work(self):
        good=self.report();self.assertTrue(self.probe(good)[0])
        bad=self.report(routes=[{'route':'opencode-go','ok':False},{'route':'proxy','ok':True}])
        ok,text=self.probe(bad);self.assertFalse(ok);self.assertIn('yedek yolla',text)
        self.assertEqual(health.health_snapshot(bad,now=lambda:1100)['health_status'],'degraded')
        self.assertTrue(self.probe(good)[0])


if __name__=='__main__':unittest.main()
