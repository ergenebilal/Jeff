"""PR-03 regressions with real SQLite and local HTTP servers only."""
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'jeff2' / 'bridge'))
from task_contract import TaskCreate, TaskLedger
from executive_briefing import (BriefingStore, DuplicateReport, TelegramDelivery,
                                scan_sources, split_message)


class FixtureHandler(BaseHTTPRequestHandler):
    posts = []

    def do_GET(self):
        data = b'<html><title>Ornek Klinik</title><body>Ornek Klinik info@ornek.test</body></html>'
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        self.posts.append(json.loads(body))
        data = json.dumps({'ok': True, 'result': {'message_id': len(self.posts)}}).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_):
        pass


class BriefingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / 'canonical.db'
        self.now = datetime(2026, 9, 28, 9, 0, tzinfo=timezone.utc)

    def test_unavailable_database_is_unknown_not_zero(self):
        report = BriefingStore(self.db).snapshot(self.now)
        self.assertEqual(report.metrics['verified_yesterday'].value, 'UNKNOWN')
        self.assertIn('data unavailable', report.text)
        self.assertFalse(self.db.exists())

    def test_corrupt_database_is_unknown_not_zero(self):
        self.db.write_bytes(b'not a sqlite database')
        report = BriefingStore(self.db).snapshot(self.now)
        self.assertEqual(report.metrics['new_leads'].value, 'UNKNOWN')
        self.assertEqual(report.metrics['failed_stuck'].value, 'UNKNOWN')

    def test_real_ledger_counts_and_snapshot_provenance(self):
        yesterday = datetime(2026, 9, 27, 12, tzinfo=timezone.utc).timestamp()
        ledger = TaskLedger(self.db, clock=lambda: yesterday)
        ledger.initialize()
        ledger.create(TaskCreate(task_id='verified-1', source='test', goal='Pablo health',
                                 success_criteria=['pablo_health_ok'], risk_level='low',
                                 side_effect_class='none', approval_required=False))
        ledger.plan('verified-1', 'jeff')
        ledger.queue('verified-1', 'jeff')
        ledger.claim('verified-1', 'pablo')
        ledger.start('verified-1', 'pablo')
        ledger.finish('verified-1', 'pablo',
                      {'request_id': 'verified-1', 'status': 'SUCCESS'})
        ledger.verify('verified-1', lambda: {'status_code': 200, 'status': 'ok'})
        store = BriefingStore(self.db)
        store.initialize()
        report = store.snapshot(self.now)
        self.assertEqual(report.metrics['verified_yesterday'].value, 1)
        self.assertEqual(report.metrics['new_leads'].value, 0)
        self.assertTrue(report.metrics['verified_yesterday'].query)
        self.assertEqual(report.metrics['verified_yesterday'].snapshot_at,
                         self.now.isoformat())
        self.assertIn('Dün doğrulanan işler: 1', report.text)

    def test_radar_upserts_source_and_caps_new_candidates(self):
        store = BriefingStore(self.db)
        store.initialize()
        source = {'company_name': 'Ornek Klinik', 'city': 'Bursa',
                  'website': 'https://ornek.test', 'source_url': 'https://ornek.test',
                  'contact_channel': 'email', 'contact_value': 'info@ornek.test',
                  'evidence': 'Official clinic contact page',
                  'problem_hypothesis': 'Digital appointment flow could be reviewed',
                  'fit_score': 60}
        first = store.ingest([source], self.now)
        second = store.ingest([dict(source, fit_score=70)], self.now)
        self.assertEqual(first, {'created': 1, 'updated': 0})
        self.assertEqual(second, {'created': 0, 'updated': 1})
        leads = store.leads()
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]['fit_score'], 70)
        self.assertEqual(leads[0]['outreach_status'], 'NOT_SENT')
        self.assertEqual(leads[0]['verification_status'], 'UNVERIFIED')
        self.assertEqual(leads[0]['source_url'], source['source_url'])
        many = [dict(source, company_name=f'Clinic {index}',
                     website=f'https://clinic{index}.test',
                     source_url=f'https://clinic{index}.test') for index in range(12)]
        self.assertEqual(store.ingest(many, self.now)['created'], 10)

    def test_local_source_scan_and_telegram_idempotency(self):
        FixtureHandler.posts = []
        server = ThreadingHTTPServer(('127.0.0.1', 0), FixtureHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        url = f'http://127.0.0.1:{server.server_port}'
        source = {'company_name': 'Ornek Klinik', 'city': 'Bursa',
                  'website': url, 'source_url': url,
                  'contact_channel': 'email', 'contact_value': 'info@ornek.test',
                  'problem_hypothesis': 'Appointment workflow review', 'fit_score': 50}
        candidates = scan_sources([source], self.now, allow_loopback=True)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0]['verification_status'], 'VERIFIED')
        store = BriefingStore(self.db)
        store.initialize()
        self.assertEqual(store.ingest(candidates, self.now)['created'], 1)
        self.assertEqual(store.ingest(candidates, self.now)['created'], 0)
        report = store.snapshot(self.now)
        self.assertIn('Yeni leadler', report.text)
        delivery = TelegramDelivery(store, endpoint=url + '/sendMessage',
                                    token='fixture-token', chat_id='fixture-chat')
        delivery.send('report-2026-09-28', report.text)
        self.assertEqual(len(FixtureHandler.posts), 1)
        with self.assertRaises(DuplicateReport):
            delivery.send('report-2026-09-28', report.text)
        self.assertEqual(len(FixtureHandler.posts), 1)

    def test_split_message_preserves_text_under_telegram_limit(self):
        message = ('Klinik raporu\n' * 1000).rstrip()
        parts = split_message(message, max_chars=4096)
        self.assertTrue(all(len(part) <= 4096 for part in parts))
        self.assertEqual('\n'.join(parts), message)


if __name__ == '__main__':
    unittest.main()
