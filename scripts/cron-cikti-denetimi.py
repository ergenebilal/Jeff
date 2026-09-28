#!/usr/bin/env python3
"""Kullanıcıya giden cron çıktılarının içerik denetimi.

`last_status: ok` doğru çıktı demek değildir (bkz. hermes-operasyon §12c).
Bu script son 24 saatte ÜRETİLEN çıktıları içerik açısından tarar:
  - Latin dışı alfabe karışması (Korece/Arapça/Kiril/CJK)
  - başka bir görevin konusuna kayma (sağlık işinde iş/fırsat analizi vb.)
  - "şimdi üreteceğim" gibi çıktı yerine vaat
  - aşırı kısa yanıt
Temizse HİÇBİR ŞEY yazmaz (sessiz). Sorun varsa tek blok halinde rapor eder.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

CRON = Path('/home/hermes/.hermes/cron')
JOBS = CRON / 'jobs.json'
OUT = CRON / 'output'
PENCERE = 24 * 3600

# Konu başlığı -> o işte GEÇMEMESİ gereken kelimeler
YASAK = {
    'saglik': ['fırsat tespiti', 'ade ', 'pazar araştırma', 'lead gen', 'komisyon', 'freelancer'],
    'firsat': ['sağlık rutini', 'tartı', 'takviye'],
    'tartim': ['fırsat tespiti', 'lead gen'],
}
VAAT = ['üretmeye geçiyorum', 'üreteceğim.', 'çıktıyı üretmeye']
LATIN_DISI = re.compile(r'[\u0600-\u06FF\u0400-\u04FF\u4E00-\u9FFF\uAC00-\uD7AF]')


def yukle():
    try:
        return {j['id']: j for j in json.load(open(JOBS))['jobs']}
    except Exception:
        return {}


def son_yanit(yol):
    try:
        metin = yol.read_text(errors='ignore')
    except Exception:
        return None
    if '## Response' not in metin:
        return None
    return metin.split('## Response', 1)[1].strip()


def denetle():
    isler = yukle()
    simdi = time.time()
    bulgular = []
    for jid in isler:
        if isler[jid].get('deliver') != 'origin':   # yalnız kullanıcıya giden işler
            continue
        d = OUT / jid
        if not d.exists():
            continue
        for f in d.glob('*.md'):
            if simdi - f.stat().st_mtime > PENCERE:
                continue
            yanit = son_yanit(f)
            if not yanit:
                continue
            ad = isler[jid].get('name', jid)
            sebepler = []
            disi = LATIN_DISI.findall(yanit)
            if len(disi) >= 3:
                sebepler.append(f'Latin dışı alfabe karışmış ({len(disi)} karakter)')
            alt = yanit.lower()
            for anahtar, kelimeler in YASAK.items():
                if anahtar in ad.lower():
                    for k in kelimeler:
                        if k in alt:
                            sebepler.append(f'konu kayması: "{k}"')
            for v in VAAT:
                if v in alt:
                    sebepler.append('çıktı yerine vaat cümlesi')
            if len(yanit.split()) < 15 and '[silent]' not in alt:
                sebepler.append(f'aşırı kısa yanıt ({len(yanit.split())} kelime)')
            if sebepler:
                bulgular.append(f"- **{ad}** ({f.name})\n  - " + '\n  - '.join(sorted(set(sebepler))))
    return bulgular


if __name__ == '__main__':
    bulgular = denetle()
    if bulgular:
        print('⚠️ CRON ÇIKTI DENETİMİ — şüpheli çıktı bulundu:\n')
        print('\n'.join(bulgular))
        print('\nNe yapılır: çıktıyı oku (~/.hermes/cron/output/<id>/), model override ve konu kilidini kontrol et.')
        sys.exit(0)
    sys.exit(0)
