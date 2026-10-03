import json
import sqlite3
import tempfile
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from scripts import morning_report as mr
from scripts import system_watchdog as wd

NOW = datetime(2026, 9, 30, 4, 30, tzinfo=timezone.utc)  # 07:30 in Istanbul
PREAMBLE = 'CyberGene showroom. Kullanıcı işletme sahibidir; fiyat, klinik, randevu, telefon. '


def wrapped(question):
    return PREAMBLE + 'İşletme sahibinin sorusu: ' + question


def make_chat_db(path, messages):
    db = sqlite3.connect(path)
    db.execute('CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, '
               'sender TEXT, text TEXT, timestamp TEXT, notified_telegram INTEGER DEFAULT 0)')
    for sid, sender, text, hours_ago in messages:
        stamp = (NOW - timedelta(hours=hours_ago)).isoformat()
        db.execute('INSERT INTO messages (session_id,sender,text,timestamp) VALUES (?,?,?,?)',
                   (sid, sender, text, stamp))
    db.commit()
    db.close()


def make_bridge_db(path, statuses):
    """statuses: 'waiting_approval' or ('waiting_approval', hours_old)."""
    db = sqlite3.connect(path)
    db.execute('CREATE TABLE task_records (task_id TEXT, status TEXT, updated_at TEXT)')
    for i, entry in enumerate(statuses):
        status, hours = entry if isinstance(entry, tuple) else (entry, 1)
        db.execute('INSERT INTO task_records VALUES (?,?,?)',
                   (f't{i}', status, (NOW - timedelta(hours=hours)).isoformat()))
    db.commit()
    db.close()


class ParsingTests(unittest.TestCase):
    def test_question_is_taken_after_the_marker(self):
        self.assertEqual(mr.visitor_question(wrapped('Fiyat nedir?')), 'Fiyat nedir?')
        self.assertEqual(mr.visitor_question('Merhaba'), 'Merhaba')

    def test_preamble_words_do_not_make_a_lead(self):
        # The old report scanned the preamble and counted every showroom message as a lead.
        self.assertEqual(mr.classify(mr.visitor_question(wrapped('Nasıl çalışıyorsunuz?'))), 'normal')

    def test_classification(self):
        self.assertEqual(mr.classify('bağlantı testi'), 'test')
        self.assertEqual(mr.classify('Hello, final migration check'), 'test')
        self.assertEqual(mr.classify('Fiyat teklifi alabilir miyim?'), 'warm')
        self.assertEqual(mr.classify('Beni 0532 123 45 67 numarasından arayın'), 'warm')
        self.assertEqual(mr.classify('ben@firma.com adresine yazın'), 'warm')
        self.assertEqual(mr.classify('Kliniğimde gece mesajlara yetişemiyoruz'), 'normal')


class CollectTests(unittest.TestCase):
    def test_site_counts_real_test_and_warm_within_24h(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / 'chat.db'
            make_chat_db(db, [
                ('aaaaaaaaaa', 'visitor', wrapped('Fiyat teklifi istiyorum'), 3),
                ('aaaaaaaaaa', 'ai', 'Tabii', 3),
                ('bbbbbbbbbb', 'visitor', wrapped('Kliniğim için ne yaparsınız?'), 5),
                ('cccccccccc', 'visitor', 'baglanti testi', 2),
                ('dddddddddd', 'visitor', wrapped('Fiyat nedir?'), 30),   # older than 24h
            ])
            site = mr.collect_site(db, NOW)
        self.assertEqual((site['real'], site['warm'], site['test']), (2, 1, 1))
        self.assertEqual(site['warm_items'][0][2], 'Fiyat teklifi istiyorum')

    def test_anonymous_site_counters_are_summed_and_shown(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / 'chat.db'
            make_chat_db(db, [('aaaaaaaaaa', 'visitor', wrapped('Merhaba'), 3)])
            con = sqlite3.connect(db)
            con.execute("CREATE TABLE events (day TEXT, name TEXT, path TEXT, n INTEGER DEFAULT 0, PRIMARY KEY (day, name, path))")
            day = NOW.strftime('%Y-%m-%d')
            con.executemany("INSERT INTO events VALUES (?,?,?,?)", [
                (day, 'visit', '/', 12), (day, 'visit', '/showroom/', 3), (day, 'showroom_link', '/', 5),
                (day, 'whatsapp_click', '/', 2), (day, 'pilot_call', '/', 1), (day, 'faq_open', '/', 4),
                ('2000-01-01', 'visit', '/', 999)])
            con.commit(); con.close()
            site = mr.collect_site(db, NOW)
        self.assertEqual(site['traffic']['visit'], 15)
        text = mr.build_report(site, None, None, 3, NOW.astimezone())
        self.assertIn("Siteyi gezen (tarayıcı oturumu): 15, showroom'a geçen: 5", text)
        self.assertIn("WhatsApp'a basan: 3 (pilot düğmesi: 1)", text)

    def test_sessions_named_test_are_never_visitors(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / 'chat.db'
            make_chat_db(db, [('test_load_1', 'visitor', wrapped('Merhaba nasılsınız'), 1),
                              ('test_watchdog_9', 'visitor', wrapped('Merhaba'), 1),
                              ('cg_showroom_real', 'visitor', wrapped('Kliniğim için ne yaparsınız?'), 1)])
            site = mr.collect_site(db, NOW)
        self.assertEqual((site['real'], site['test']), (1, 2))

    def test_missing_counter_table_is_not_a_crash(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / 'chat.db'
            make_chat_db(db, [('aaaaaaaaaa', 'visitor', wrapped('Merhaba'), 3)])
            self.assertIsNone(mr.collect_site(db, NOW)['traffic'])

    def test_unreadable_database_is_none_not_zero(self):
        self.assertIsNone(mr.collect_site('/nonexistent/x.db', NOW))
        self.assertIsNone(mr.collect_approvals('/nonexistent/x.db'))
        self.assertIsNone(mr.collect_health('/nonexistent/s.json', time.time()))

    def test_approvals(self):
        with tempfile.TemporaryDirectory() as d:
            db = Path(d) / 'b.db'
            make_bridge_db(db, ['waiting_approval', ('waiting_approval', 60), 'failed', 'verified'])
            data = mr.collect_approvals(db, NOW)
            self.assertEqual({k: data[k] for k in ('waiting', 'old', 'stuck')}, {'waiting': 2, 'old': 1, 'stuck': 1})

    def test_health_lists_problems_by_plain_label_and_detects_stale_watchdog(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 's.json'
            p.write_text(json.dumps({'unit:nginx': {'ok': False, 'detail': 'failed'}, 'disk': {'ok': True}}))
            fresh = mr.collect_health(p, p.stat().st_mtime + 60)
            self.assertEqual(fresh['bad'], [('Web sunucusu', 'failed')])
            self.assertFalse(fresh['stale'])
            self.assertTrue(mr.collect_health(p, p.stat().st_mtime + 3600)['stale'])

    def test_backup_age(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(mr.collect_backup(d, time.time()))
            f = Path(d) / 'jeff-backup-1.tar.gz'
            f.write_bytes(b'x')
            self.assertEqual(mr.collect_backup(d, f.stat().st_mtime + 5 * 3600), 5)


class ReportTests(unittest.TestCase):
    LOCAL = NOW.astimezone(timezone(timedelta(hours=3)))

    def report(self, site, approvals, health, backup=3):
        return mr.build_report(site, approvals, health, backup, self.LOCAL)

    def test_calm_day(self):
        text = self.report({'real': 0, 'warm': 0, 'test': 0, 'warm_items': []}, {'waiting': 0, 'stuck': 0},
                           {'total': 14, 'bad': [], 'stale': False, 'age_min': 2})
        self.assertIn('Onay bekleyen iş yok', text)
        self.assertIn('14/14 kontrol sağlam', text)
        self.assertIn('Acil görünen bir şey yok', text)

    def test_warm_lead_leads_the_suggestion_and_shows_local_time(self):
        site = {'real': 1, 'warm': 1, 'test': 2,
                'warm_items': [(NOW - timedelta(hours=1), 'aaaaaaaa', 'Fiyat teklifi istiyorum')]}
        text = self.report(site, {'waiting': 1, 'stuck': 0}, {'total': 14, 'bad': [], 'stale': False, 'age_min': 1})
        self.assertIn('Sıcak fırsat: 1', text)
        self.assertIn('06:30', text)                       # 03:30 UTC -> 06:30 local
        self.assertIn('Deneme/test konuşması: 2 (sayılmadı)', text)
        self.assertIn('önce onlara dönüş', text)

    def test_missing_sources_say_so_instead_of_zero(self):
        text = self.report(None, None, None, backup=None)
        self.assertEqual(text.count('veri alinamadi'), 3)
        self.assertIn('kaynaklarını kontrol', text)
        self.assertNotIn('Test görünmeyen ziyaretçi konuşması: 0', text)

    def test_stale_watchdog_is_flagged(self):
        text = self.report({'real': 0, 'warm': 0, 'test': 0, 'warm_items': []}, {'waiting': 0, 'stuck': 0},
                           {'total': 14, 'bad': [], 'stale': True, 'age_min': 90})
        self.assertIn('90 dakikadır kayıt yazmıyor', text)
        self.assertNotIn('kontrol sağlam', text)

    def test_no_internal_names(self):
        text = self.report(None, None, None)
        for name in ('Jeff', 'Pablo', 'Guardian'):
            self.assertNotIn(name, text)

    def test_split_message(self):
        parts = mr.split_message('\n'.join(['x' * 100] * 100), limit=1000)
        self.assertTrue(all(len(p) <= 1000 for p in parts))
        self.assertEqual(sum(p.count('x' * 100) for p in parts), 100)


class KindTests(unittest.TestCase):
    LOCAL = NOW.astimezone(timezone(timedelta(hours=3)))

    def test_titles_and_advice_heading_differ_per_kind(self):
        empty = {'real': 0, 'warm': 0, 'test': 0, 'warm_items': []}
        ok = {'total': 14, 'bad': [], 'stale': False, 'age_min': 1}
        ap = {'waiting': 0, 'old': 0, 'stuck': 0}
        evening = mr.build_report(empty, ap, ok, 2, self.LOCAL, 'evening')
        weekly = mr.build_report(empty, ap, ok, 2, self.LOCAL, 'weekly')
        self.assertIn('gün sonu özeti', evening)
        self.assertIn('YARIN İÇİN ÖNERİM', evening)
        self.assertIn('SİTEDE SON 7 GÜN', weekly)

    def test_old_approvals_are_called_out_and_lead_the_advice(self):
        text = mr.build_report({'real': 0, 'warm': 0, 'test': 0, 'warm_items': []},
                               {'waiting': 3, 'old': 2, 'stuck': 0},
                               {'total': 14, 'bad': [], 'stale': False, 'age_min': 1}, 2, self.LOCAL)
        self.assertIn('2 tanesi 2 günden uzun süredir bekliyor', text)
        self.assertIn('2 iş 2 günden uzun süredir onayını bekliyor', text)

    def test_evening_window_is_since_local_midnight(self):
        self.assertEqual(mr.WINDOW_HOURS['evening'](datetime(2026, 9, 30, 19, 5)), 20)
        self.assertEqual(mr.WINDOW_HOURS['weekly'](datetime(2026, 9, 30, 19, 5)), 168)


class DeliveryTests(unittest.TestCase):
    def run_main(self, d, now, extra=(), sent=None):
        chat, bridge = Path(d) / 'c.db', Path(d) / 'b.db'
        if not chat.exists():
            make_chat_db(chat, [])
            make_bridge_db(bridge, [])
        argv = ['--chat-db', str(chat), '--bridge-db', str(bridge), '--watchdog-state', str(Path(d) / 's.json'),
                '--backup-dir', d, '--sent-state', str(Path(d) / 'sent.json'), *extra]
        sender = mock.Mock(return_value=True) if sent is None else sent
        with mock.patch.object(wd, 'telegram_sender', return_value=sender):
            code = mr.main(argv, now=now)
        return code, sender

    def creds(self, d):
        (Path(d) / 'e').write_text('ALERT_BOT_TOKEN=t\nALERT_CHAT_ID=1\n')
        return ['--send', '--env-file', str(Path(d) / 'e')]

    def test_too_early_does_not_send(self):
        with tempfile.TemporaryDirectory() as d:
            early = datetime(2026, 9, 30, 3, 0, tzinfo=timezone.utc)  # 06:00 Istanbul
            code, sender = self.run_main(d, early, self.creds(d))
            self.assertEqual(code, 0)
            sender.assert_not_called()

    def test_routine_report_is_local_and_never_marked_delivered(self):
        with tempfile.TemporaryDirectory() as d:
            args=self.creds(d)
            code,sender=self.run_main(d,NOW,args)
            self.assertEqual(code,0);sender.assert_not_called()
            self.assertTrue(list((Path(d)/'reports').glob('morning-*.txt')))
            self.assertFalse((Path(d)/'sent.json').exists())
            code,sender=self.run_main(d,NOW+timedelta(minutes=10),args)
            sender.assert_not_called()

    def test_local_reports_require_no_telegram_credentials(self):
        with tempfile.TemporaryDirectory() as d,mock.patch.dict('os.environ',{},clear=True):
            code,sender=self.run_main(d,NOW,['--send'])
            self.assertEqual(code,0);sender.assert_not_called()

    def test_all_routine_kinds_stay_quiet(self):
        with tempfile.TemporaryDirectory() as d:
            for kind in ('morning','evening','weekly'):
                code,sender=self.run_main(d,NOW,self.creds(d)+['--kind',kind,'--at','00:00'])
                self.assertEqual(code,0);sender.assert_not_called()

    def test_until_and_weekday_guards(self):
        with tempfile.TemporaryDirectory() as d:
            args = self.creds(d)
            late = datetime(2026, 9, 30, 12, 0, tzinfo=timezone.utc)           # 15:00 Istanbul
            code, sender = self.run_main(d, late, args + ['--until', '11:00'])
            sender.assert_not_called()
            # 30 Sep 2026 is a Wednesday (weekday 2)
            code, sender = self.run_main(d, NOW, args + ['--kind', 'weekly', '--weekday', '6', '--at', '00:00'])
            sender.assert_not_called()
            code, sender = self.run_main(d, NOW, args + ['--kind', 'weekly', '--weekday', '2', '--at', '00:00'])
            sender.assert_not_called()

    def test_dry_run_never_sends_or_marks_sent(self):
        with tempfile.TemporaryDirectory() as d:
            code, sender = self.run_main(d, NOW, ['--dry-run'])
            self.assertEqual(code, 0)
            sender.assert_not_called()
            self.assertFalse((Path(d) / 'sent.json').exists())


if __name__ == '__main__':
    unittest.main()
