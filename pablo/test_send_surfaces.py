"""The approval gate must recognise a SEND gesture on any sensitive surface, however it is performed
(named action, Enter, clicking a labelled Send button, browser automation) and must leave reading,
navigating autonomous; unresolved clicks on sensitive surfaces require approval."""
import unittest
from unittest import mock

import pablo_task_guard as guard


def gate(action, params, title=''):
    with mock.patch.object(guard, '_foreground_window_title', return_value=title), \
            mock.patch.object(guard, '_coordinate_target', return_value={'name': '', 'window': ''}):
        return guard.is_approval_required(action, params)[0]


class SendGestureTests(unittest.TestCase):
    def test_enter_in_any_sensitive_window_needs_approval(self):
        for title in ('WhatsApp', 'Instagram • Direct - Google Chrome', 'Gelen Kutusu - Gmail', 'Yeni ileti - Outlook',
                      'Home / X - Google Chrome', 'LinkedIn Messaging', 'Telegram Web'):
            self.assertTrue(gate('gui_type', {'text': 'merhaba', 'enter': True}, title), title)

    def test_typing_without_enter_stays_autonomous_even_in_a_sensitive_window(self):
        self.assertFalse(gate('gui_type', {'text': 'merhaba'}, 'Instagram - Direct'))

    def test_enter_in_a_harmless_window_stays_autonomous(self):
        self.assertFalse(gate('gui_type', {'text': 'notlar', 'enter': True}, 'Not Defteri'))
        self.assertFalse(gate('gui_type', {'text': 'kod', 'enter': True}, 'Visual Studio Code'))

    def test_clicking_a_labelled_send_button_in_a_sensitive_window_needs_approval(self):
        for label in ('Gönder', 'Send', 'Paylaş', 'Share', 'Post', 'Tweet', 'Yayınla', 'Reply', 'Yanıtla'):
            self.assertTrue(gate('gui_click', {'control_name': label}, 'Instagram - Direct'), label)
        self.assertTrue(gate('gui_click', {'name': 'Send', 'window_title': 'Gmail'}, ''))

    def test_clicking_a_send_button_in_a_harmless_window_stays_autonomous(self):
        self.assertFalse(gate('gui_click', {'control_name': 'Gönder'}, 'Not Defteri'))

    def test_unresolved_sensitive_click_needs_approval_but_named_navigation_does_not(self):
        self.assertTrue(gate('gui_click', {'x': 100, 'y': 200}, 'WhatsApp'))
        self.assertFalse(gate('gui_click', {'control_name': 'Sohbetler'}, 'WhatsApp'))
        self.assertFalse(gate('gui_click', {'control_name': 'Ara'}, 'Instagram'))

    def test_observed_control_overrides_claimed_label(self):
        with mock.patch.object(guard, '_foreground_window_title', return_value='WhatsApp'), \
                mock.patch.object(guard, '_coordinate_target', return_value={'name': 'Send', 'window': 'WhatsApp'}):
            self.assertTrue(guard.is_approval_required('gui_click', {'x': 1, 'y': 2, 'name': 'Ara'})[0])

    def test_observed_navigation_stays_autonomous(self):
        with mock.patch.object(guard, '_foreground_window_title', return_value='WhatsApp'), \
                mock.patch.object(guard, '_coordinate_target', return_value={'name': 'Sohbetler', 'window': 'WhatsApp'}):
            self.assertFalse(guard.is_approval_required('gui_click', {'x': 1, 'y': 2})[0])

    def test_supplied_window_cannot_hide_sensitive_foreground(self):
        self.assertTrue(gate('gui_click', {'name': 'Send', 'window_title': 'Not Defteri'}, 'WhatsApp'))

    def test_observed_window_catches_inactive_sensitive_target(self):
        with mock.patch.object(guard, '_foreground_window_title', return_value='Not Defteri'), \
                mock.patch.object(guard, '_coordinate_target', return_value={'name': 'Send', 'window': 'WhatsApp'}):
            self.assertTrue(guard.is_approval_required('gui_click', {'x': 1, 'y': 2})[0])

    def test_missing_or_invalid_contact_flag_requires_approval(self):
        for params in ({}, {'is_new_contact': 'false'}, {'is_new_contact': 0},
                       {'is_new_contact': False, 'new_recipient': True}):
            self.assertTrue(gate('whatsapp_send', params))
        self.assertFalse(gate('whatsapp_send', {'is_new_contact': False}))
        self.assertFalse(gate('whatsapp_draft', {}))

    def test_shell_red_lines_ignore_argument_order_and_language(self):
        for command in ('powershell -Command "Remove-Item -LiteralPath C:\\fixture -Recurse -Force"',
                        'python -c "import os; os.remove(\'fixture.txt\')"',
                        'python -c "from pathlib import Path; Path(\'fixture.txt\').unlink()"',
                        'pwsh -EncodedCommand fixture', 'python -c "exec(payload)"',
                        'python -c "pyautogui.press(\'enter\')"'):
            self.assertTrue(gate('shell', {'command': command}), command)
        for command in ('Get-Content fixture.txt', 'dir', 'python -c "print(1)"'):
            self.assertFalse(gate('shell', {'command': command}), command)

    def test_public_profile_and_real_delivery_do_not_depend_on_caller_flags(self):
        self.assertTrue(gate('marketing_playbook', {'playbook': 'instagram_bio'}))
        self.assertTrue(gate('marketing_playbook', {'playbook': 'deliver_campaign', 'simulated': False}))
        self.assertFalse(gate('marketing_playbook', {'playbook': 'deliver_campaign', 'simulated': True}))

    def test_browser_click_on_send_needs_approval_only_on_sensitive_pages(self):
        self.assertTrue(gate('browser_act', {'type': 'click', 'selector': 'button[aria-label="Send"]'}, 'Instagram • Direct'))
        self.assertTrue(gate('browser_act', {'type': 'click', 'selector': 'Paylaş', 'url': 'https://www.instagram.com/'}, ''))
        self.assertFalse(gate('browser_act', {'type': 'click', 'selector': 'button.send'}, 'Ürün listesi - cybergene.co'))

    def test_browser_enter_on_a_sensitive_page_needs_approval(self):
        self.assertTrue(gate('browser_act', {'type': 'press', 'value': 'Enter'}, 'Gmail - Yeni ileti'))
        self.assertTrue(gate('browser_act', {'type': 'type', 'text': 'merhaba', 'enter': True}, 'LinkedIn'))
        self.assertFalse(gate('browser_act', {'type': 'press', 'value': 'Enter'}, 'Google Arama'))

    def test_reading_and_navigating_are_never_gated(self):
        for action, params in (('browser_read', {}), ('browser_open', {'url': 'https://www.instagram.com/direct/inbox/'}),
                               ('screenshot', {}), ('window_list', {}), ('window_focus', {'title': 'WhatsApp'}),
                               ('browser_act', {'type': 'scroll'})):
            self.assertFalse(gate(action, params, 'Instagram - Direct'), action)

    def test_existing_red_lines_are_unchanged(self):
        self.assertTrue(gate('social_post', {}))
        self.assertTrue(gate('whatsapp_send', {'is_new_contact': True}))
        self.assertTrue(gate('shell', {'command': 'rmdir /s /q C:\\data'}))
        self.assertTrue(gate('payment', {}))
        self.assertFalse(gate('read_file', {'path': 'a.txt'}))


if __name__ == '__main__':
    unittest.main()
