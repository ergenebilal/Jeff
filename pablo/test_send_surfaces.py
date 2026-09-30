"""The approval gate must recognise a SEND gesture on any sensitive surface, however it is performed
(named action, Enter, clicking a labelled Send button, browser automation) and must leave reading,
navigating and unlabelled clicks fully autonomous."""
import unittest
from unittest import mock

import pablo_task_guard as guard


def gate(action, params, title=''):
    with mock.patch.object(guard, '_foreground_window_title', return_value=title):
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

    def test_unlabelled_clicks_and_other_buttons_in_sensitive_windows_stay_autonomous(self):
        self.assertFalse(gate('gui_click', {'x': 100, 'y': 200}, 'WhatsApp'))               # reading chats
        self.assertFalse(gate('gui_click', {'control_name': 'Sohbetler'}, 'WhatsApp'))
        self.assertFalse(gate('gui_click', {'control_name': 'Ara'}, 'Instagram'))

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
