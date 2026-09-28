#!/usr/bin/env python3
"""Ekip postanesi olay toplayıcı.

n8n'deki 'ekip-postane-v1' iş akışının yeni koşularını okur, olayları
/home/hermes/fpc/ekip-olaylar.jsonl dosyasına ekler ve satış hattı
kayıt defterini (cevap-log.csv) güvenli şekilde günceller.

Elle çalıştırma:  python3 /home/hermes/ekip_olay_al.py [--test]
"""
import csv
import json
import os
import shutil
import sys
import urllib.request
from datetime import datetime

FPC = '/home/hermes/fpc'
OLAYLAR = os.path.join(FPC, 'ekip-olaylar.jsonl')
DEFTER = os.path.join(FPC, 'cevap-log.csv')
ISARET = os.path.join(FPC, '.ekip_son_kosu')
N8N_KEY = json.load(open('/home/hermes/.config/n8n-api.json'))['api_key']
BASE = 'https://n8n.aiergene.xyz'
IS_AKISI = (open('/home/hermes/fpc/.ekip_is_akisi_id').read().strip()
            if os.path.exists('/home/hermes/fpc/.ekip_is_akisi_id')
            else open('/tmp/ekip_wf_id').read().strip())


def api(path):
    req = urllib.request.Request(BASE + path, headers={'X-N8N-API-KEY': N8N_KEY})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def son_kosu():
    try:
        return int(open(ISARET).read().strip())
    except Exception:
        return 0


def gecerli_olay(kosu):
    """Koşudan olayı çıkar; geçersiz/hatalı koşularda None döner."""
    rd = ((kosu.get('data') or {}).get('resultData') or {})
    if kosu.get('status') != 'success':
        return None
    for ad in ('Doğrula + normalize et', 'Dogrula + normalize et'):
        girdi = (rd.get('runData') or {}).get(ad)
        if girdi:
            veri = girdi[0].get('data', {}).get('main', [[None]])[0]
            if veri:
                j = veri[0].get('json', {})
                if j.get('valid'):
                    return j.get('event')
    return None


def deftere_islev(event):
    """Olayı kayıt defterine işler. Yalnız doldurur, silmez. (satır, değişenler) döner."""
    hedef = (event.get('hedef') or '').strip()
    if not hedef:
        return None, []
    with open(DEFTER, encoding='utf-8-sig', newline='') as f:
        satirlar = list(csv.reader(f, delimiter=';'))
    if len(satirlar) < 2:
        return None, []
    baslik = satirlar[0]
    idx = {ad: i for i, ad in enumerate(baslik)}
    if 'id' not in idx:
        return None, []
    degisen = []
    bulundu = None
    for satir in satirlar[1:]:
        if not satir or satir[idx['id']] != hedef:
            continue
        bulundu = hedef
        ne = event.get('ne')
        zaman = event.get('zaman') or ''
        if ne == 'gonderildi':
            if 't0_gonderim' in idx and not satir[idx['t0_gonderim']]:
                satir[idx['t0_gonderim']] = zaman
                degisen.append('t0_gonderim')
            if 'asama' in idx:
                satir[idx['asama']] = '4-TEST_INTEREST (gonderildi)'
                degisen.append('asama')
        elif ne == 'yanit':
            if 'cevap_verdi' in idx:
                satir[idx['cevap_verdi']] = 'evet'
                degisen.append('cevap_verdi')
            if 'yanit_saati' in idx:
                satir[idx['yanit_saati']] = zaman
                degisen.append('yanit_saati')
            if 'asama' in idx:
                satir[idx['asama']] = '4-TEST_INTEREST (yanit geldi)'
                degisen.append('asama')
            if 'yanit_dk' in idx and 't0_gonderim' in idx and satir[idx['t0_gonderim']]:
                try:
                    t0 = datetime.fromisoformat(satir[idx['t0_gonderim']].replace('Z', '+00:00'))
                    t1 = datetime.fromisoformat(zaman.replace('Z', '+00:00'))
                    satir[idx['yanit_dk']] = str(int((t1 - t0).total_seconds() // 60))
                    degisen.append('yanit_dk')
                except Exception:
                    pass
        if 'not' in idx and event.get('not'):
            mevcut = satir[idx['not']] or ''
            ek = f"[{event.get('kim','?')}:{ne}] {event['not']}"
            satir[idx['not']] = (mevcut + ' | ' + ek).strip(' |')
            degisen.append('not')
        break
    if degisen:
        shutil.copy2(DEFTER, os.path.join(FPC, '.cevap-log.yedek.csv'))
        with open(DEFTER, 'w', encoding='utf-8', newline='') as f:
            csv.writer(f, delimiter=';').writerows(satirlar)
    return bulundu, degisen


def main():
    son = son_kosu()
    veri = api(f'/api/v1/executions?workflowId={IS_AKISI}&limit=100&includeData=true')
    kosular = sorted(veri['data'], key=lambda k: int(k['id']))
    islenen = 0
    with open(OLAYLAR, 'a', encoding='utf-8') as f:
        for kosu in kosular:
            kid = int(kosu['id'])
            if kid <= son:
                continue
            event = gecerli_olay(kosu)
            if event:
                event['kosu_id'] = kid
                f.write(json.dumps(event, ensure_ascii=False) + '\n')
                satir, degisen = deftere_islev(event)
                print(f"olay alındı: {event['kim']} / {event['ne']} / {event.get('hedef') or '-'} "
                      f"| defter: {satir or 'eşleşme yok'} {degisen or ''}")
                islenen += 1
            son = max(son, kid)
    open(ISARET, 'w').write(str(son))
    if islenen:
        print(f"işlenen yeni olay: {islenen} | son koşu işareti: {son}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
