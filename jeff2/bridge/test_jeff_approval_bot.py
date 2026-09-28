"""Jeff approval consumer tests without external Telegram calls."""

import unittest

from jeff2.bridge.jeff_approval_bot import JeffApprovalBot, validate_config


class JeffApprovalBotTests(unittest.TestCase):
    def setUp(self):
        self.card = {'task_id': 'task-1', 'approval_id': 'approval-1',
                     'digest': 'a' * 64, 'type': 'BROWSER_ACTION',
                     'payload': '{"url":"https://example.test"}', 'notified': False,
                     'decision': None}
        self.sent = []
        self.decisions = []
        self.claimed = False

        def bridge_call(method, path, body=None):
            if method == 'GET' and path == '/alfred/approvals':
                return {'approvals': [] if self.claimed else [self.card]}
            if method == 'POST' and path == '/alfred/approvals/task-1/claim':
                old = self.claimed
                self.claimed = True
                self.card['notified'] = True
                return {'claimed': not old}
            if method == 'GET' and path == '/alfred/approval-card/approval-1':
                return self.card
            if method == 'POST' and path == '/alfred/approvals/task-1/decision':
                self.decisions.append(body)
                self.card['decision'] = body['decision']
                return {'status': 'decided'}
            raise AssertionError((method, path))

        def telegram_call(method, payload):
            self.sent.append((method, payload))
            return {'ok': True}

        self.bot = JeffApprovalBot('42', bridge_call, telegram_call)

    def test_owner_callback_is_bound_and_single_use(self):
        self.bot.send_pending()
        self.bot.send_pending()
        messages = [payload for method, payload in self.sent if method == 'sendMessage']
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['chat_id'], '42')
        self.assertIn('a:approval-1', str(messages[0]['reply_markup']))
        update = {'callback_query': {'id': 'callback-1', 'data': 'a:approval-1',
                                     'from': {'id': 42}, 'message': {'chat': {'id': 42}}}}
        self.bot.handle_update(update)
        self.bot.handle_update(update)
        self.assertEqual(len(self.decisions), 1)
        self.assertEqual(self.decisions[0]['digest'], 'a' * 64)
        self.assertEqual(self.decisions[0]['actor_id'], '42')
        self.assertEqual(self.decisions[0]['chat_id'], '42')

    def test_wrong_owner_and_long_payload_fail_closed(self):
        self.card['payload'] = 'x' * 5000
        self.bot.send_pending()
        self.assertFalse(self.claimed)
        self.assertEqual(self.sent, [])
        self.bot.handle_update({'callback_query': {'id': 'callback-2',
            'data': 'a:approval-1', 'from': {'id': 99}, 'message': {'chat': {'id': 42}}}})
        self.assertEqual(self.decisions, [])

    def test_missing_or_conflicting_configuration_fails_closed(self):
        config = {'BRIDGE_KEY': 'bridge', 'JEFF_APPROVAL_KEY': 'jeff',
                  'APPROVAL_OWNER_ID': '42', 'JEFF_APPROVAL_BOT_TOKEN': 'fixture-token',
                  'BRIDGE_URL': 'http://127.0.0.1:7700'}
        self.assertEqual(validate_config(config)['owner_id'], '42')
        for changed in ({'JEFF_APPROVAL_BOT_TOKEN': ''},
                        {'BRIDGE_URL': 'http://example.test:7700'},
                        {'JEFF_APPROVAL_KEY': 'bridge'},
                        {'TASK_WORKER_KEY': 'jeff'},
                        {'TELEGRAM_BOT_TOKEN': 'fixture-token'}):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                validate_config({**config, **changed})


if __name__ == '__main__':
    unittest.main()
