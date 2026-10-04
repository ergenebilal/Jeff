import json
import tempfile
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

from scripts import jeff_status as js


def runner(active='active', log=''):
    def run(cmd, **kw):
        return SimpleNamespace(stdout=active if cmd[0] == 'systemctl' else log)
    return run


class GatewayTests(unittest.TestCase):
    def test_running(self):
        self.assertIn('çalışıyor', js.gateway_line(runner()))

    def test_down(self):
        self.assertIn('ÇALIŞMIYOR', js.gateway_line(runner(active='failed')))

    def test_fighting_copies_are_called_out(self):
        text = js.gateway_line(runner(log='Telegram polling conflict\n' * 4))
        self.assertIn('başka bir kopya', text)

    def test_unreadable_says_so(self):
        def boom(*a, **k):
            raise OSError('x')
        self.assertIn(js.UNAVAILABLE, js.gateway_line(boom))


class JobsTests(unittest.TestCase):
    def test_delivery_failed_timeout_interrupted_unknown_are_visible(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'jobs.json'
            p.write_text(json.dumps({'jobs':[
                {'name':'opp-digest-push','last_status':'delivery_failed','last_run':'fixture time'},
                {'name':'slow','last_status':'timeout'},
                {'name':'cut','last_status':'interrupted'},
                {'name':'new-result','last_status':'unexpected'},
                {'name':'never-run'},
                {'name':'paused-old-error','enabled':False,'last_status':'error'}]}))
            text=js.hermes_jobs_line(p)
        for name in ('opp-digest-push','slow','cut','new-result','never-run','fixture time','unexpected'):
            self.assertIn(name,text)
        self.assertNotIn('paused-old-error',text)
        self.assertIn('teslim başarısız',text)

    def test_all_failures_remain_visible_above_four(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'jobs.json'
            p.write_text(json.dumps([{'id':str(i),'last_status':'error'} for i in range(6)]))
            text=js.hermes_jobs_line(p)
        self.assertIn('5 [son çalışma:',text)

    def test_invalid_inventory_is_unknown(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'jobs.json'; p.write_text('{"jobs":17}')
            self.assertIn(js.UNAVAILABLE,js.hermes_jobs_line(p))

    def test_counts_active_paused_and_failing(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'jobs.json'
            p.write_text(json.dumps({'jobs': [
                {'name': 'a', 'enabled': True, 'last_status': 'ok'},
                {'name': 'b', 'enabled': True, 'last_status': 'error'},
                {'name': 'c', 'enabled': True, 'paused_at': '2026-09-01'},
                {'name': 'd', 'enabled': False},
            ]}))
            text = js.hermes_jobs_line(p)
        self.assertIn('2 aktif, 2 duraklatılmış', text)
        self.assertIn('hata veren: b', text)

    def test_missing_file(self):
        self.assertIn(js.UNAVAILABLE, js.hermes_jobs_line('/nonexistent/jobs.json'))


class ReportsAndWatchdogTests(unittest.TestCase):
    def test_reports(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 's.json'
            p.write_text(json.dumps({'last_sent': '2026-09-29', 'last_sent_evening': '2026-09-28'}))
            text = js.reports_line(p)
        self.assertIn('sabah: 2026-09-29', text)
        self.assertIn('akşam: 2026-09-28', text)
        self.assertIn('haftalık: henüz gitmedi', text)

    def test_watchdog_all_good_and_problem_and_stale(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'w.json'
            p.write_text(json.dumps({'disk': {'ok': True}, 'unit:nginx': {'ok': False, 'detail': 'failed'}}))
            mtime = p.stat().st_mtime
            lines = js.watchdog_lines(p, mtime + 60)
            self.assertTrue(any('Web sunucusu' in x for x in lines))
            p.write_text(json.dumps({'disk': {'ok': True}}))
            mtime = p.stat().st_mtime
            self.assertIn('hepsi sağlam', js.watchdog_lines(p, mtime + 60)[0])
            self.assertIn('güncel olmayabilir', js.watchdog_lines(p, mtime + 7200)[0])

    def test_watchdog_missing(self):
        self.assertIn(js.UNAVAILABLE, js.watchdog_lines('/nonexistent/w.json')[0])


class BuildTests(unittest.TestCase):
    def test_whole_screen_is_plain_and_free_of_internal_names(self):
        text = js.build_status(datetime(2026, 9, 30, 6, 0, tzinfo=timezone.utc),
                               gateway=lambda: 'Jeff (Telegram): çalışıyor',
                               jobs=lambda: 'işler', reports=lambda: 'raporlar', dog=lambda: ['bekçi tamam'],
                               jarvis=lambda: 'Pablo’da 13 açık iş var')
        self.assertIn('Jeff durumu', text)
        self.assertIn('Pablo’da 13 açık iş var', text)
        self.assertNotIn('request_id', text)
        self.assertNotIn('Traceback', text)


if __name__ == '__main__':
    unittest.main()
