#!/usr/bin/env python3
"""Ekip postanesine olay gönderir (mutasyonsuz testler için).

Kullanım:
    python3 ekip_olay_gonder.py <kim> <ne> <hedef> "<not>" ["<kanit>"]

kim ∈ {alfred, jeff, dewey, bilal} · ne ∈ {gonderildi, yanit, tamam, hata, not, durum}
Yalnız gerçek gönderimde ne=gonderildi kullan; testler ne=not/durum ile yapılır.
Serbest etiketli hedef (defter id'si olmayan) deftere hiç dokunmaz.
"""
import json
import os
import re
import sys
import urllib.request

ENV = '/home/hermes/.hermes/.env'
ANA_YOL = 'http://100.124.217.48:5678/webhook/ekip-olay'
YEDEK_YOL = 'https://n8n.aiergene.xyz/webhook/ekip-olay'


def token():
    try:
        m = re.search(r'^EKIP_POSTANE_TOKEN=(.*)$', open(ENV).read(), re.M)
        return m.group(1).strip() if m else os.environ.get('EKIP_POSTANE_TOKEN', '')
    except Exception:
        return os.environ.get('EKIP_POSTANE_TOKEN', '')


def gonder(yol, govde, tok):
    req = urllib.request.Request(
        yol,
        data=json.dumps(govde).encode(),
        headers={'Content-Type': 'application/json', 'x-ekip-token': tok},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.status, r.read().decode()


def main():
    if len(sys.argv) < 5:
        print(__doc__)
        return 2
    kim, ne, hedef, notu = sys.argv[1:5]
    kanit = sys.argv[5] if len(sys.argv) > 5 else 'ekip_olay_gonder.py'
    govde = {'kim': kim, 'ne': ne, 'hedef': hedef, 'not': notu, 'kanit': kanit}
    tok = token()
    if not tok:
        print('HATA: EKIP_POSTANE_TOKEN bulunamadi (', ENV, ')')
        return 3
    for yol in (ANA_YOL, YEDEK_YOL):
        try:
            kod, yanit = gonder(yol, govde, tok)
            print('YOL:', yol)
            print('HTTP', kod)
            print(yanit[:600])
            return 0 if kod == 200 else 1
        except Exception as e:
            print('YOL BASARISIZ:', yol, type(e).__name__, e)
    return 1


if __name__ == '__main__':
    sys.exit(main())
