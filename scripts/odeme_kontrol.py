#!/usr/bin/env python3
"""Ödeme bildirimi kontrol scripti — her gün çalışır.
Bugün ve yarın ödemesi olan borçları bildirir.
"""
import json
import os
from datetime import datetime, timedelta

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.json")

GUN_ADLARI = {
    "Monday": "Pazartesi", "Tuesday": "Salı", "Wednesday": "Çarşamba",
    "Thursday": "Perşembe", "Friday": "Cuma", "Saturday": "Cumartesi", "Sunday": "Pazar"
}

def main():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print("Henüz veri yok.")
        return

    borc = data.get("borc", {})
    if not borc:
        print("Borç verisi yok.")
        return

    now = datetime.now()
    bugun = now.day
    yarin = (now + timedelta(days=1)).day
    bugun_adi = GUN_ADLARI.get(now.strftime("%A"), now.strftime("%A"))
    yarin_adi = GUN_ADLARI.get((now + timedelta(days=1)).strftime("%A"), "")

    mesajlar = []

    # KMH kontrol (kmhList - dizi)
    for kmh in borc.get("kmhList", []):
        odeme = kmh.get("odeme")
        if odeme and int(odeme) == yarin:
            ad = kmh.get("ad", "KMH")
            tutar = kmh.get("bakiye", 0)
            mesajlar.append(f"🏦 {ad} — YARIN ({yarin_adi}) SON GÜN! (₺{tutar:,.0f})")
        elif odeme and int(odeme) == bugun:
            ad = kmh.get("ad", "KMH")
            tutar = kmh.get("bakiye", 0)
            mesajlar.append(f"🏦 {ad} — BUGÜN SON GÜN! (₺{tutar:,.0f})")

    # Kredi kartları kontrol
    for kredi in borc.get("krediler", []):
        odeme = kredi.get("odeme")
        if odeme and int(odeme) == yarin:
            ad = kredi.get("ad", "Kredi Kartı")
            tutar = kredi.get("borc", 0)
            mesajlar.append(f"💳 {ad} — YARIN ({yarin_adi}) SON GÜN! (₺{tutar:,.0f})")
        elif odeme and int(odeme) == bugun:
            ad = kredi.get("ad", "Kredi Kartı")
            tutar = kredi.get("borc", 0)
            mesajlar.append(f"💳 {ad} — BUGÜN SON GÜN! (₺{tutar:,.0f})")

    # Vergiler kontrol (vade tarihi)
    for vergi in borc.get("vergiler", []):
        vade = vergi.get("vade", "")
        if vade:
            try:
                vade_tarih = datetime.strptime(vade, "%Y-%m-%d").date()
                if vade_tarih == (now + timedelta(days=1)).date():
                    tur = vergi.get("tur", "Vergi")
                    tutar = vergi.get("tutar", 0)
                    mesajlar.append(f"📄 {tur} — YARIN ({yarin_adi}) SON GÜN! (₺{tutar:,.0f})")
                elif vade_tarih == now.date():
                    tur = vergi.get("tur", "Vergi")
                    tutar = vergi.get("tutar", 0)
                    mesajlar.append(f"📄 {tur} — BUGÜN SON GÜN! (₺{tutar:,.0f})")
            except ValueError:
                pass

    if mesajlar:
        print("⚠️ ÖDEME HATIRLATMALARI")
        print("══════════════════════")
        for m in mesajlar:
            print(m)
        print(f"\nToplam {len(mesajlar)} ödeme bildirimi")
    # sessiz kal — sadece ödeme varsa bildir

if __name__ == "__main__":
    main()
