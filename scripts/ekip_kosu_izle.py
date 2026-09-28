#!/usr/bin/env python3
"""n8n koşusunun webhook kaynağını inceler (IP/başlık izi) — read-only.

Kullanım: python3 ekip_kosu_izle.py <kosu_id>
"""
import json
import sys
import urllib.request

N8N_KEY = json.load(open('/home/hermes/.config/n8n-api.json'))['api_key']
BASE = 'https://n8n.aiergene.xyz'


def api(path):
    req = urllib.request.Request(BASE + path, headers={'X-N8N-API-KEY': N8N_KEY})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read().decode())


def main():
    kid = sys.argv[1] if len(sys.argv) > 1 else '43'
    d = api(f'/api/v1/executions/{kid}?includeData=true')
    rd = ((d.get('data') or {}).get('resultData') or {}).get('runData') or {}
    print('kosu:', d.get('id'), '| durum:', d.get('status'),
          '| baslangic:', d.get('startedAt'), '| mod:', d.get('mode'))
    for ad in ('Webhook — POST /ekip-olay', 'Webhook - POST /ekip-olay'):
        if ad in rd:
            j = rd[ad][0]['data']['main'][0][0]['json']
            h = j.get('headers') or {}
            for k in sorted(h):
                if k.lower() in ('x-forwarded-for', 'x-real-ip', 'user-agent', 'host',
                                 'x-ekip-token', 'cf-connecting-ip', 'x-forwarded-host'):
                    v = h[k]
                    if k.lower() == 'x-ekip-token':
                        v = f'<gizli {len(str(v))} karakter>'
                    print(f'  {k}: {v}')
            print('  govde:', json.dumps(j.get('body'), ensure_ascii=False)[:300])


if __name__ == '__main__':
    main()
