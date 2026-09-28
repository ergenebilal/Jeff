#!/usr/bin/env python3
"""Ekip postanesi (ekip-postane-v1) — n8n iş akışını API ile oluşturur ve aktive eder."""
import json
import re
import secrets
import subprocess
import urllib.request

HERMES_ENV = '/home/hermes/.hermes/.env'


def env(key):
    m = re.search(rf'^{key}=(.*)$', open(HERMES_ENV).read(), re.M)
    return m.group(1).strip() if m else None


N8N_KEY = json.load(open('/home/hermes/.config/n8n-api.json'))['api_key']
BASE = 'https://n8n.aiergene.xyz'
TOKEN = env('EKIP_POSTANE_TOKEN')
CHAT_ID = env('TELEGRAM_ALLOWED_USERS')
TG_CRED_ID = '53vvI4oggqgeLtMo'
TG_CRED_NAME = 'Ekip Telegram Bot'


def api(method, path, payload=None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={'X-N8N-API-KEY': N8N_KEY, 'Content-Type': 'application/json'},
        method=method,
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


code = """
// Ekip olayını doğrula ve normalize et
const TOKEN = %r;
const h = ($json.headers || {});
const gelen = h['x-ekip-token'] || ($json.body && $json.body.token) || '';
if (gelen !== TOKEN) {
  return [{ json: { valid: false, reason: 'gecersiz_token' } }];
}
const b = $json.body || {};
const izinliKim = ['alfred', 'jeff', 'dewey', 'bilal'];
const izinliNe = ['gonderildi', 'yanit', 'tamam', 'hata', 'not', 'durum'];
const kim = String(b.kim || '').toLowerCase().trim();
const ne = String(b.ne || '').toLowerCase().trim();
if (!izinliKim.includes(kim)) { return [{ json: { valid: false, reason: 'gecersiz_kim:' + kim } }]; }
if (!izinliNe.includes(ne)) { return [{ json: { valid: false, reason: 'gecersiz_ne:' + ne } }]; }
const simdi = new Date().toISOString();
return [{ json: {
  valid: true,
  event: {
    olay_id: 'E' + Date.now() + '-' + Math.floor(Math.random() * 900 + 100),
    kim: kim,
    ne: ne,
    hedef: b.hedef ? String(b.hedef) : null,
    zaman: b.zaman ? String(b.zaman) : simdi,
    kanit: b.kanit ? String(b.kanit) : null,
    not: b.not ? String(b.not) : null,
    kayit_anI: simdi
  }
} }];
""".replace('%r', repr(TOKEN))

wf = {
    'name': 'ekip-postane-v1',
    'nodes': [
        {
            'parameters': {
                'httpMethod': 'POST',
                'path': 'ekip-olay',
                'responseMode': 'responseNode',
                'options': {},
                'headerParameters': {'parameters': [{'name': 'x-ekip-token'}]},
            },
            'id': 'wh-ekip',
            'name': 'Webhook — POST /ekip-olay',
            'type': 'n8n-nodes-base.webhook',
            'typeVersion': 2,
            'position': [0, 0],
            'webhookId': secrets.token_hex(8),
        },
        {
            'parameters': {'jsCode': code},
            'id': 'code-dogrula',
            'name': 'Doğrula + normalize et',
            'type': 'n8n-nodes-base.code',
            'typeVersion': 2,
            'position': [220, 0],
        },
        {
            'parameters': {
                'conditions': {
                    'options': {'caseSensitive': True, 'leftValue': '', 'typeValidation': 'loose', 'version': 2},
                    'conditions': [{
                        'id': 'c1',
                        'leftValue': '={{ $json.valid }}',
                        'rightValue': True,
                        'operator': {'type': 'boolean', 'operation': 'true', 'singleValue': True},
                    }],
                    'combinator': 'and',
                },
                'options': {},
            },
            'id': 'if-gecerli',
            'name': 'IF — geçerli mi',
            'type': 'n8n-nodes-base.if',
            'typeVersion': 2,
            'position': [440, 0],
        },
        {
            'parameters': {
                'chatId': CHAT_ID,
                'text': '=📬 EKİP OLAYI\nKim: {{ $json.event.kim }}\nNe: {{ $json.event.ne }}\nHedef: {{ $json.event.hedef || "—" }}\nSaat: {{ $json.event.zaman }}\nKanıt: {{ $json.event.kanit || "—" }}\nNot: {{ $json.event.not || "—" }}\nOlay no: {{ $json.event.olay_id }}',
                'additionalFields': {},
            },
            'id': 'tg-bildir',
            'name': 'Telegram — bildir',
            'type': 'n8n-nodes-base.telegram',
            'typeVersion': 1.2,
            'position': [660, -100],
            'credentials': {'telegramApi': {'id': TG_CRED_ID, 'name': TG_CRED_NAME}},
        },
        {
            'parameters': {
                'respondWith': 'json',
                'responseBody': "={{ { ok: true, alindi: $('Doğrula + normalize et').item.json.event } }}",
                'options': {},
            },
            'id': 'resp-kabul',
            'name': 'Yanıt — kabul',
            'type': 'n8n-nodes-base.respondToWebhook',
            'typeVersion': 1.1,
            'position': [880, -100],
        },
        {
            'parameters': {
                'respondWith': 'json',
                'responseBody': '={{ { ok: false, sebep: $json.reason } }}',
                'options': {'responseCode': 401},
            },
            'id': 'resp-red',
            'name': 'Yanıt — red',
            'type': 'n8n-nodes-base.respondToWebhook',
            'typeVersion': 1.1,
            'position': [660, 120],
        },
    ],
    'connections': {
        'Webhook — POST /ekip-olay': {'main': [[{'node': 'Doğrula + normalize et', 'type': 'main', 'index': 0}]]},
        'Doğrula + normalize et': {'main': [[{'node': 'IF — geçerli mi', 'type': 'main', 'index': 0}]]},
        'IF — geçerli mi': {'main': [
            [{'node': 'Telegram — bildir', 'type': 'main', 'index': 0}],
            [{'node': 'Yanıt — red', 'type': 'main', 'index': 0}],
        ]},
        'Telegram — bildir': {'main': [[{'node': 'Yanıt — kabul', 'type': 'main', 'index': 0}]]},
    },
    'settings': {'executionOrder': 'v1'},
}

# --- mevcut aynı isimli iş akışını temizle ---
mevcut = api('GET', '/api/v1/workflows?limit=100')['data']
for w in mevcut:
    if w['name'] == 'ekip-postane-v1':
        api('DELETE', f"/api/v1/workflows/{w['id']}")
        print('eski sürüm silindi:', w['id'][:8])

olusan = api('POST', '/api/v1/workflows', wf)
print('oluşturuldu:', olusan['id'][:8], '| ad:', olusan['name'], '| aktif:', olusan['active'])

aktif = api('POST', f"/api/v1/workflows/{olusan['id']}/publish")
print('yayında:', aktif.get('active'))
print('ID:', olusan['id'])
open('/tmp/ekip_wf_id', 'w').write(olusan['id'])
