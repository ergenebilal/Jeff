#!/usr/bin/env python3
"""Teslim öncesi PDF denetimi (rapor-pdf-teslimi skill'i).

Kullanım:
    python3 pdf_dogrula.py <pdf> [--yatay] [--bekle "89 gün"] [--bekle "640"]

Ne yapar:
  - sayfa sayısı + karakter sayısı
  - Türkçe glif kontrolü (ş ğ İ ı ö ü ç görünüyor mu)
  - kusur regex taraması: HTML etiketi, bozuk karakter, ilçe eki, çift boşluk,
    kaybolan satır kırılması, tek başına alıntı işareti
  - --yatay: her sayfanın genişliği yüksekliğinden büyük mü
  - --bekle: PDF metninde bulunması gereken dizeler (dosya adı, kritik sayı vb.)

Çıkış kodu: kusur / eksik dize varsa 1, temizse 0.

Neden ayrı dosya: kusur regex'lerinin kendisi ('&nbsp;') komut satırına gömülünce
terminal guard'ı ampersand'ı arka planlama sanıp komutu reddedebiliyor.
"""
import argparse
import re
import sys

from pypdf import PdfReader

KUSURLAR = {
    'html etiketi': r'<br>|&nbsp;|&lt;',
    'bozuk karakter': r'[\u00cd\u00c3\u00c5\u00fe\u00fd\u00f0\u0307]',
    'ilce eki hatasi': r"Y\u0131ld\u0131r\u0131m'de|Mudanya'de",
    'cift bosluk': r'\S  +\S',
    'kaybolan kirilma': r'\w\u00b7',
    'tek basina alinti': r'^>\s*$',
}
TR_GLIFLER = 'şğıİöüçŞĞÖÜÇ'


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('pdf')
    ap.add_argument('--yatay', action='store_true', help='her sayfa yatay mı')
    ap.add_argument('--bekle', action='append', default=[], help='PDF metninde bulunması gereken dize')
    a = ap.parse_args()

    r = PdfReader(a.pdf)
    txt = '\n'.join((p.extract_text() or '') for p in r.pages)

    sorunlar = []

    print(f'sayfa: {len(r.pages)} | karakter: {len(txt)}')
    if len(txt.strip()) < 200:
        sorunlar.append('metin neredeyse boş — font gömülmemiş ya da render düşmüş')

    bulunan = sorted(set(TR_GLIFLER) & set(txt))
    print('Turkce glifler:', ''.join(bulunan) or 'YOK')
    if not set('şğıİöüç') & set(txt):
        sorunlar.append('hiç Türkçe glif yok — yazı tipi yedeğe düşmüş olabilir')

    for ad, pat in KUSURLAR.items():
        m = re.findall(pat, txt, flags=re.M)
        durum = 'TEMIZ' if not m else f'{len(m)} ADET'
        print(f'{ad}: {durum}', (m[:3] if m else ''))
        if m:
            sorunlar.append(f'{ad} ({len(m)})')

    if a.yatay:
        dikey = [i + 1 for i, p in enumerate(r.pages) if p.mediabox.width <= p.mediabox.height]
        print('yatay olmayan sayfalar:', dikey or 'yok')
        if dikey:
            sorunlar.append(f'yatay beklenirken dikey sayfa: {dikey}')

    for d in a.bekle:
        n = txt.count(d)
        print(f'beklenen "{d}": {n}')
        if n == 0:
            sorunlar.append(f'eksik dize: "{d}"')

    print()
    if sorunlar:
        print('SONUC: KUSURLU ->', '; '.join(sorunlar))
        return 1
    print('SONUC: TEMIZ')
    return 0


if __name__ == '__main__':
    sys.exit(main())
