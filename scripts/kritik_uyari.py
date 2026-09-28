#!/usr/bin/env python3
"""Kritik tarih uyarıları — Hermes cron tarafından çağrılır.
Çıktı: sadece uyarı varsa mesaj, yoksa sessiz."""
import sys
sys.path.insert(0, '/home/hermes/hermes_data')
from tools import kritik_tarih_uyarilari

if __name__ == "__main__":
    result = kritik_tarih_uyarilari()
    if result["adet"] > 0:
        print("📅 KRİTİK TARİH UYARILARI")
        for u in result["uyarilar"]:
            print(u["mesaj"])
