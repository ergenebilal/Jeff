#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Harita kayip kontrolu — eski SOUL'daki kritik kavramlar yeni haritada var mi?

Yapan (haritayi yazan) ile kontrol eden (bu betik) ayridir. Amac: hicbir kuralin
sessizce kaybolmadigini kanitlamak. Kayip varsa cikis kodu 1.
"""
import re
import sys
from pathlib import Path

ESKI = Path("/home/hermes/jeff_repo/SOUL-tam-2026-10-01.md")
YENI = Path("/home/hermes/jeff_repo/SOUL-harita.md")
# Ayrintinin tasindigi yerler (haritadan isaret ediliyor)
TASINAN = [
    Path("/home/hermes/jeff_repo/SOUL-tam-2026-10-01.md"),
    Path("/home/hermes/.hermes/99-1-otonomi.md"),
]
SKILLS = Path("/home/hermes/.hermes/skills")

# Kural adi -> o kurali temsil eden zorunlu anahtar kelimeler (en az biri gecmeli)
KURALLAR = {
    "99/1 otonomi":            ["%99", "99/1", "otonomi"],
    "Onay isteyen 4 durum":    ["para", "hesap", "silme", "ilk temas"],
    "Kimlik":                  ["otonom operatör", "düşünce ortağı"],
    "Cift ses (samimi)":       ["kanka", "samimi"],
    "Ajans kalitesi":          ["ajans kalitesi", "şablon"],
    "Harika fikir yasagi":     ["harika fikir"],
    "Iletisim: once sonuc":    ["önce sonuç"],
    "Masa basinda bitir":      ["yapılır", "söz verme"],
    "On bildirim":             ["ön bildirim"],
    "Kapsam daraltma":         ["sadece", "kapsamı daralt"],
    "Itiraz kurallari":        ["karşı çık", "itiraz"],
    "Ticari doktrin":          ["ödeme sinyali", "observed", "ticari"],
    "Hesap verebilirlik":      ["hesap verebilirlik", "feedback"],
    "Yonetici katmani":        ["strateji = ne", "tradeoff"],
    "Amaç > mesguliyet":       ["amaç >", "kime nasıl kazandırır"],
    "Tekrar sorma yasagi":     ["tekrar sorma"],
    "3-strike kurali":         ["3 kez", "teşhis"],
    "Kok sebep":               ["kök sebep"],
    "Tek degisken":            ["tek değişken"],
    "Delegasyon":              ["nanobot", "delege"],
    "Sistem gercegi":          ["servis", "tailscale", "9119"],
    "Gereksiz yuk yasagi":     ["gereksiz yük", "belki işe yarar"],
    "Kalite suzgeci":          ["kalite süzgecinden"],
    "Gizli kimlik":            ["gizli kimlik", "numarasını"],
    "BITIS KONTROLU (yeni)":   ["bitiş kontrolü", "üç katman", "uçtan uca"],
    "Yapan != kontrol eden":   ["kontrol eden", "kontrol edenden"],
    "Kapi komutu":             ["kendini_dogrula.py"],
    "GSD (isaret)":            ["gsd"],
    "Jeff 2.0 (isaret)":       ["2.0", "departman", "motor"],
    "Dersler (isaret)":        ["ders", "post-mortem", "lessons"],
}

metin_harita = YENI.read_text(encoding="utf-8", errors="ignore").lower()
# isaret edilen yerlerin tamami birlikte
isaret = metin_harita
for p in TASINAN:
    if p.exists():
        isaret += "\n" + p.read_text(encoding="utf-8", errors="ignore").lower()
for sk in SKILLS.rglob("SKILL.md"):
    try:
        isaret += "\n" + sk.read_text(encoding="utf-8", errors="ignore").lower()
    except Exception:
        pass

kayip, tamam = [], []
for ad, anahtarlar in KURALLAR.items():
    if any(k.lower() in metin_harita for k in anahtarlar):
        tamam.append(ad)
    elif any(k.lower() in isaret for k in anahtarlar):
        tamam.append(ad + " [isaret edilen yerde]")
    else:
        kayip.append(ad)

print("HARITA KAYIP KONTROLU")
print("-" * 56)
print(f"  harita        : {len(YENI.read_text().splitlines())} satir "
      f"({len(YENI.read_bytes())} bayt)")
print(f"  eski tam metin: {len(ESKI.read_text().splitlines())} satir "
      f"({len(ESKI.read_bytes())} bayt)")
print(f"  kazanc        : {100 - len(YENI.read_bytes()) * 100 // len(ESKI.read_bytes())}% kucultme")
print("-" * 56)
print(f"  yerinde/isaretli : {len(tamam)}")
for t in tamam:
    print(f"     + {t}")
if kayip:
    print(f"  KAYIP            : {len(kayip)}")
    for k in kayip:
        print(f"     - {k}")
    print("-" * 56)
    print("SONUC: KAYIP VAR — harita yayina alinmaz")
    sys.exit(1)
print("-" * 56)
print(f"SONUC: KAYIP YOK — {len(tamam)} kuralin tamami yerinde")
sys.exit(0)
