import json
import sqlite3
import tempfile
import unittest
from datetime import timedelta, timezone
from pathlib import Path
from unittest import mock

from scripts import lead_alert as la

TZ = timezone(timedelta(hours=3))
PREAMBLE = 'CyberGene showroom. Kullanıcı işletme sahibidir; fiyat, klinik, randevu, telefon. '


def wrapped(q):
    return PREAMBLE + 'İşletme sahibinin sorusu: ' + q


class Chat:
    """A throwaway chat database shaped like the real one."""

    def __init__(self, directory):
        self.path = Path(directory) / 'chat.db'
        self.state = Path(directory) / 'state.json'
        db = sqlite3.connect(self.path)
        db.execute('CREATE TABLE messages (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, '
                   'sender TEXT, text TEXT, timestamp TEXT)')
        db.commit()
        db.close()

    def add(self, sid, text, sender='visitor'):
        db = sqlite3.connect(self.path)
        db.execute('INSERT INTO messages (session_id,sender,text,timestamp) VALUES (?,?,?,?)',
                   (sid, sender, text, '2026-09-30T10:30:00+00:00'))
        db.commit()
        db.close()

    def run(self, send):
        return la.run(self.path, self.state, send, TZ)


def outbox(accept=True):
    box = mock.Mock(return_value=accept)
    return box


class LeadAlertTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.chat = Chat(self._dir.name)

    def tearDown(self):
        self._dir.cleanup()

    def test_first_run_only_remembers_position(self):
        self.chat.add('s1', wrapped('Fiyat teklifi istiyorum'))
        send = outbox()
        self.assertIn('initialized', self.chat.run(send))
        send.assert_not_called()
        self.chat.run(send)                      # nothing new, still silent
        send.assert_not_called()

    def test_warm_message_alerts_once_per_conversation(self):
        self.chat.run(outbox())
        self.chat.add('sess-aaaaaa', wrapped('Fiyat teklifi istiyorum'))
        self.chat.add('sess-aaaaaa', wrapped('Ayrıca randevu da lazım'))
        send = outbox()
        self.chat.run(send)
        self.assertEqual(send.call_count, 1)
        text = send.call_args[0][0]
        self.assertIn('sıcak bir fırsat', text)
        self.assertIn('Fiyat teklifi istiyorum', text)
        self.assertIn('#aaaaaa', text)
        self.assertIn('13:30', text)             # 10:30 UTC -> 13:30 Istanbul
        self.assertNotIn('CyberGene showroom', text)   # the preamble never leaks into the alert
        self.chat.run(send)                      # already handled
        self.assertEqual(send.call_count, 1)

    def test_tests_and_ordinary_questions_are_silent(self):
        self.chat.run(outbox())
        self.chat.add('s1', wrapped('baglanti testi'))
        self.chat.add('s2', wrapped('Kliniğim için ne yaparsınız?'))
        self.chat.add('s3', 'Hello', sender='ai')
        send = outbox()
        self.chat.run(send)
        send.assert_not_called()

    def test_preamble_words_alone_never_trigger(self):
        self.chat.run(outbox())
        self.chat.add('s1', wrapped('Nasıl çalışıyorsunuz?'))
        send = outbox()
        self.chat.run(send)
        send.assert_not_called()

    def test_leaving_contact_details_sends_a_second_alert_with_them(self):
        self.chat.run(outbox())
        self.chat.add('s1', wrapped('Fiyat nedir?'))
        self.chat.add('s1', wrapped('Beni 0532 123 45 67 numarasından arayın'))
        send = outbox()
        self.chat.run(send)
        self.assertEqual(send.call_count, 2)
        self.assertIn('0532 123 45 67', send.call_args_list[1][0][0])
        self.assertIn('iletişim bilgisi bıraktı', send.call_args_list[1][0][0])

    def test_contact_first_does_not_double_alert(self):
        self.chat.run(outbox())
        self.chat.add('s1', wrapped('Ulaşın: ali@firma.com'))
        self.chat.add('s1', wrapped('Fiyat da öğrenmek isterim'))
        send = outbox()
        self.chat.run(send)
        self.assertEqual(send.call_count, 1)

    def test_failed_send_is_retried_and_not_lost(self):
        self.chat.run(outbox())
        self.chat.add('s1', wrapped('Fiyat teklifi istiyorum'))
        self.chat.run(outbox(accept=False))
        send = outbox()
        self.chat.run(send)
        self.assertEqual(send.call_count, 1)
        self.chat.run(send)
        self.assertEqual(send.call_count, 1)

    def test_burst_is_capped_and_finished_on_next_run(self):
        self.chat.run(outbox())
        for i in range(8):
            self.chat.add(f's{i}', wrapped('Fiyat teklifi istiyorum'))
        send = outbox()
        self.chat.run(send)
        self.assertEqual(send.call_count, la.MAX_ALERTS_PER_RUN)
        self.chat.run(send)
        self.assertEqual(send.call_count, 8)

    def test_unreadable_database_is_reported_not_crashed(self):
        self.assertEqual(la.run('/nonexistent/x.db', self._dir.name + '/s.json', outbox(), TZ), 'db-unavailable')

    def test_contacts_in(self):
        self.assertEqual(la.contacts_in('0532 123 45 67 ve ali@firma.com'), ['0532 123 45 67', 'ali@firma.com'])
        self.assertEqual(la.contacts_in('sadece merhaba'), [])

    def test_main_dry_run(self):
        self.chat.run(outbox())
        self.chat.add('s1', wrapped('Fiyat teklifi istiyorum'))
        code = la.main(['--chat-db', str(self.chat.path), '--state', str(self.chat.state), '--dry-run'])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(self.chat.state.read_text())['last_id'], 1)

    def test_main_needs_credentials(self):
        with mock.patch.dict('os.environ', {}, clear=True):
            self.assertEqual(la.main(['--chat-db', str(self.chat.path), '--state', str(self.chat.state)]), 2)


if __name__ == '__main__':
    unittest.main()
