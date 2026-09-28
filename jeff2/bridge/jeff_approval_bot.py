"""Jeff-owned Telegram consumer for Bridge approval cards.

This process must have a dedicated Telegram token and be the only poller for it.
"""

import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request


APPROVAL_ID = re.compile(r'[A-Za-z0-9-]{1,62}\Z')


def validate_config(environ):
    bridge_key = environ.get('BRIDGE_KEY')
    jeff_key = environ.get('JEFF_APPROVAL_KEY')
    owner_id = environ.get('APPROVAL_OWNER_ID')
    token = environ.get('JEFF_APPROVAL_BOT_TOKEN')
    base_url = environ.get('BRIDGE_URL', 'http://127.0.0.1:7700').rstrip('/')
    parsed = urllib.parse.urlparse(base_url)
    if (not bridge_key or not jeff_key or bridge_key == jeff_key
            or jeff_key == environ.get('TASK_WORKER_KEY')
            or not owner_id or not token
            or token == environ.get('TELEGRAM_BOT_TOKEN')
            or parsed.scheme != 'http'
            or parsed.hostname not in ('127.0.0.1', 'localhost', '::1')
            or parsed.username or parsed.password or parsed.path or parsed.query):
        raise ValueError('Dedicated Jeff approval credentials, owner and loopback Bridge URL required')
    return {'bridge_key': bridge_key, 'jeff_key': jeff_key,
            'owner_id': str(owner_id), 'token': token, 'base_url': base_url}


def approval_message(card):
    approval_id = str(card.get('approval_id', ''))
    if not APPROVAL_ID.fullmatch(approval_id):
        return None
    fields = {name: html.escape(str(card.get(name, '')), quote=True)
              for name in ('task_id', 'type', 'payload', 'digest')}
    if not all(fields.values()) or len(fields['digest']) != 64:
        return None
    message = (
        '🚨 <b>JEFF — ONAY TALEBİ</b>\n\n'
        f"Görev: <code>{fields['task_id']}</code>\n"
        f"Eylem: <code>{fields['type']}</code>\n"
        f"Parametreler: <code>{fields['payload']}</code>\n"
        f"SHA-256: <code>{fields['digest']}</code>\n\n"
        'Bu tam görev için onay verilsin mi?'
    )
    if len(message) > 3500:
        return None
    return {'text': message, 'parse_mode': 'HTML',
            'reply_markup': {'inline_keyboard': [[
                {'text': '✅ Onayla', 'callback_data': 'a:' + approval_id},
                {'text': '❌ Reddet', 'callback_data': 'r:' + approval_id},
            ]]}}


class JeffApprovalBot:
    def __init__(self, owner_id, bridge_call, telegram_call):
        self.owner_id = str(owner_id)
        self.bridge_call = bridge_call
        self.telegram_call = telegram_call

    def send_pending(self):
        cards = self.bridge_call('GET', '/alfred/approvals')['approvals']
        for card in cards:
            message = approval_message(card)
            if not message:
                continue  # Manual review; never claim a card the owner cannot read.
            task_id = urllib.parse.quote(str(card['task_id']), safe='')
            claimed = self.bridge_call('POST', f'/alfred/approvals/{task_id}/claim')
            if claimed.get('claimed'):
                self.telegram_call('sendMessage', {'chat_id': self.owner_id, **message})

    def handle_update(self, update):
        callback = update.get('callback_query')
        if not callback:
            return
        data = callback.get('data', '')
        actor = str(callback.get('from', {}).get('id', ''))
        chat = str(callback.get('message', {}).get('chat', {}).get('id', ''))
        if (actor != self.owner_id or chat != self.owner_id
                or len(data) < 3 or data[:2] not in ('a:', 'r:')
                or not APPROVAL_ID.fullmatch(data[2:])):
            return
        approval_id = data[2:]
        try:
            card = self.bridge_call(
                'GET', '/alfred/approval-card/' + urllib.parse.quote(approval_id, safe=''))
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
            self.telegram_call('answerCallbackQuery',
                               {'callback_query_id': callback['id'], 'text': 'Onay bulunamadı'})
            return
        if not card.get('notified') or card.get('decision'):
            self.telegram_call('answerCallbackQuery',
                               {'callback_query_id': callback['id'], 'text': 'Onay artık beklemiyor'})
            return
        decision = 'approve' if data[:2] == 'a:' else 'reject'
        task_id = urllib.parse.quote(str(card['task_id']), safe='')
        body = {'approval_id': approval_id, 'digest': card['digest'],
                'decision': decision, 'actor_id': actor, 'chat_id': chat}
        self.bridge_call('POST', f'/alfred/approvals/{task_id}/decision', body)
        self.telegram_call('answerCallbackQuery',
                           {'callback_query_id': callback['id'], 'text': 'Karar kaydedildi'})


def _json_post(url, body, headers, timeout=20):
    request = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'),
                                     headers={'Content-Type': 'application/json', **headers})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def run(environ=None):
    config = validate_config(os.environ if environ is None else environ)
    bridge_headers = {'X-Bridge-Key': config['bridge_key'],
                      'X-Jeff-Approval-Key': config['jeff_key']}

    def bridge_call(method, path, body=None):
        url = config['base_url'] + path
        if method == 'GET':
            with urllib.request.urlopen(
                    urllib.request.Request(url, headers=bridge_headers), timeout=10) as response:
                return json.load(response)
        return _json_post(url, body or {}, bridge_headers, timeout=10)

    def telegram_call(method, body):
        url = f"https://api.telegram.org/bot{config['token']}/{method}"
        response = _json_post(url, body, {}, timeout=25)
        if response.get('ok') is not True:
            raise RuntimeError('Telegram did not acknowledge request')
        return response

    bot = JeffApprovalBot(config['owner_id'], bridge_call, telegram_call)
    offset = 0
    while True:
        try:
            bot.send_pending()
            updates = telegram_call('getUpdates', {'offset': offset, 'timeout': 15})
            for update in updates.get('result', []):
                bot.handle_update(update)
                offset = max(offset, update['update_id'] + 1)
        except Exception as exc:
            # Transport errors may contain the bot token in their URL.
            print(f'Jeff approval bot waiting for reconciliation: {type(exc).__name__}', flush=True)
            time.sleep(3)


if __name__ == '__main__':
    run()
