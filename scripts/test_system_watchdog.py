import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from scripts import system_watchdog as wd


def check(key, results, grace=0):
    """A check whose outcome is taken from a mutable list so tests can flip it."""
    return wd.Check(key, f'label-{key}', 'etki', lambda: results[0], grace)


class Outbox:
    def __init__(self, accept=True):
        self.messages, self.accept = [], accept

    def __call__(self, text):
        if self.accept:
            self.messages.append(text)
        return self.accept


def step(checks, state, now, outbox):
    new_state, events = wd.evaluate(checks, state, now)
    return wd.apply_events(events, new_state, now, outbox)


class StateMachineTests(unittest.TestCase):
    def test_healthy_system_sends_nothing(self):
        res, box = [(True, 'active')], Outbox()
        state = step([check('a', res)], {}, 1000, box)
        self.assertEqual(box.messages, [])
        self.assertTrue(state['a']['ok'])

    def test_problem_is_announced_once_then_fixed_once(self):
        res, box, c = [(False, 'failed')], Outbox(), None
        c = [check('a', res)]
        state = step(c, {}, 1000, box)
        self.assertEqual(len(box.messages), 1)
        self.assertIn('Sorun var', box.messages[0])
        state = step(c, state, 1300, box)            # still down, 5 min later: silent
        self.assertEqual(len(box.messages), 1)
        res[0] = (True, 'active')
        state = step(c, state, 1600, box)
        self.assertEqual(len(box.messages), 2)
        self.assertIn('Duzeldi', box.messages[1])
        self.assertIn('10 dakika', box.messages[1])
        step(c, state, 1900, box)                     # stays fixed: silent
        self.assertEqual(len(box.messages), 2)

    def test_grace_period_hides_short_blips(self):
        res, box = [(False, 'x')], Outbox()
        c = [check('a', res, grace=600)]
        state = step(c, {}, 1000, box)
        state = step(c, state, 1300, box)
        self.assertEqual(box.messages, [])
        res[0] = (True, 'ok')                          # recovered before grace: no message at all
        step(c, state, 1500, box)
        self.assertEqual(box.messages, [])
        res[0] = (False, 'x')
        state = step(c, {}, 2000, box)
        state = step(c, state, 2700, box)              # past grace
        self.assertEqual(len(box.messages), 1)

    def test_reminder_after_six_hours(self):
        res, box = [(False, 'x')], Outbox()
        c = [check('a', res)]
        state = step(c, {}, 0, box)
        state = step(c, state, wd.REMIND_EVERY_SECONDS - 60, box)
        self.assertEqual(len(box.messages), 1)
        step(c, state, wd.REMIND_EVERY_SECONDS + 60, box)
        self.assertEqual(len(box.messages), 2)
        self.assertIn('Hala duzelmedi', box.messages[1])

    def test_failed_send_is_retried_next_run(self):
        res = [(False, 'x')]
        c = [check('a', res)]
        state = step(c, {}, 1000, Outbox(accept=False))
        self.assertFalse(state['a'].get('alerted'))
        box = Outbox()
        step(c, state, 1300, box)
        self.assertEqual(len(box.messages), 1)

    def test_failed_recovery_send_is_retried(self):
        res = [(False, 'x')]
        c = [check('a', res)]
        state = step(c, {}, 1000, Outbox())
        res[0] = (True, 'ok')
        state = step(c, state, 1300, Outbox(accept=False))
        box = Outbox()
        step(c, state, 1600, box)
        self.assertEqual(len(box.messages), 1)
        self.assertIn('Duzeldi', box.messages[0])

    def test_broken_probe_does_not_silence_others(self):
        def boom():
            raise RuntimeError('x')
        box = Outbox()
        good = [(False, 'down')]
        state = step([wd.Check('bad', 'B', 'e', boom), check('good', good)], {}, 1000, box)
        self.assertEqual(len(box.messages), 2)

    def test_message_is_plain_language(self):
        chk = wd.Check('k', 'Jeff (Telegram)', 'Jeff cevap vermez', lambda: (False, 'failed'))
        msg = wd.format_event('down', chk, 'failed', 0, 0)
        self.assertIn('Jeff (Telegram)', msg)
        self.assertIn('Jeff cevap vermez', msg)
        self.assertNotIn('Traceback', msg)


class ProbeTests(unittest.TestCase):
    def test_http_locked_door_counts_as_up(self):
        def opener(url, timeout):
            raise urllib.error.HTTPError(url, 403, 'no', {}, None)
        self.assertTrue(wd.http_reachable('http://x', wd.any_answer, opener=opener)()[0])
        self.assertFalse(wd.http_reachable('http://x', opener=opener)()[0])

    def test_http_no_answer_is_down(self):
        def opener(url, timeout):
            raise OSError('refused')
        ok, detail = wd.http_reachable('http://x', opener=opener)()
        self.assertFalse(ok)
        self.assertIn('yanit yok', detail)

    def test_unit_active(self):
        run = lambda *a, **k: SimpleNamespace(stdout='active\n')  # noqa: E731
        self.assertTrue(wd.unit_active('u', runner=run)()[0])
        run = lambda *a, **k: SimpleNamespace(stdout='failed\n')  # noqa: E731
        self.assertFalse(wd.unit_active('u', runner=run)()[0])

    def test_backup_freshness(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertFalse(wd.backup_fresh(d)()[0])           # none at all
            f = Path(d) / 'jeff-backup-1.tar.gz'
            f.write_bytes(b'x')
            mtime = f.stat().st_mtime
            self.assertTrue(wd.backup_fresh(d, now=lambda: mtime + 3600)()[0])
            self.assertFalse(wd.backup_fresh(d, now=lambda: mtime + 40 * 3600)()[0])

    def test_disk(self):
        full = lambda p: SimpleNamespace(used=95, total=100)  # noqa: E731
        roomy = lambda p: SimpleNamespace(used=10, total=100)  # noqa: E731
        self.assertFalse(wd.disk_ok(usage=full)()[0])
        self.assertTrue(wd.disk_ok(usage=roomy)()[0])

    def test_telegram_conflict_threshold(self):
        many = lambda *a, **k: SimpleNamespace(stdout='Polling conflict\n' * 3)  # noqa: E731
        few = lambda *a, **k: SimpleNamespace(stdout='Polling conflict\n')  # noqa: E731
        self.assertFalse(wd.telegram_not_fighting(runner=many)()[0])
        self.assertTrue(wd.telegram_not_fighting(runner=few)()[0])

    def test_unreadable_journal_does_not_cry_wolf(self):
        def boom(*a, **k):
            raise OSError('x')
        self.assertTrue(wd.telegram_not_fighting(runner=boom)()[0])


class IoTests(unittest.TestCase):
    def test_state_roundtrip_and_corrupt_file(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 's.json'
            self.assertEqual(wd.load_state(p), {})
            wd.save_state(p, {'a': {'ok': False}})
            self.assertEqual(wd.load_state(p), {'a': {'ok': False}})
            p.write_text('{broken')
            self.assertEqual(wd.load_state(p), {})

    def test_env_file_parsing(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'e'
            p.write_text('# c\nALERT_CHAT_ID="42"\nALERT_BOT_TOKEN=abc\n')
            self.assertEqual(wd.load_env_file(p), {'ALERT_CHAT_ID': '42', 'ALERT_BOT_TOKEN': 'abc'})
            self.assertEqual(wd.load_env_file(Path(d) / 'missing'), {})

    def test_telegram_sender_reports_failure(self):
        def opener(req, timeout):
            raise OSError('net')
        self.assertFalse(wd.telegram_sender('t', '1', opener=opener)('hi'))

    def test_dry_run_prints_and_saves_state(self):
        with tempfile.TemporaryDirectory() as d:
            fake = lambda backup_dir: [check('demo', [(False, 'x')])]  # noqa: E731
            with mock.patch.object(wd, 'default_checks', fake):
                code = wd.main(['--state', str(Path(d) / 's.json'), '--dry-run', '--backup-dir', d])
            self.assertEqual(code, 0)
            state = json.loads((Path(d) / 's.json').read_text())
            self.assertTrue(state['demo']['alerted'])

    def test_missing_credentials_is_an_error(self):
        import os
        old = {k: os.environ.pop(k, None) for k in ('ALERT_BOT_TOKEN', 'ALERT_CHAT_ID')}
        try:
            with tempfile.TemporaryDirectory() as d:
                self.assertEqual(wd.main(['--state', str(Path(d) / 's.json')]), 2)
        finally:
            for k, v in old.items():
                if v is not None:
                    os.environ[k] = v


if __name__ == '__main__':
    unittest.main()
