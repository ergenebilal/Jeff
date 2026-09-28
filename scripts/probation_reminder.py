#!/usr/bin/env python3
"""Denetimli Serbestlik hatırlatıcısı — yarın randevu varsa bildirir."""
from datetime import date, timedelta

schedule = [
    ("2026-06-26", "Seminer", "15 Temmuz Konferans Salonu"),
    ("2026-07-21", "Seminer", "15 Temmuz Konferans Salonu"),
    ("2026-08-14", "Program", "B Blok 1. Kat"),
    ("2026-08-28", "Program", "B Blok 1. Kat"),
    ("2026-09-11", "Program", "B Blok 1. Kat"),
    ("2026-09-25", "Program", "B Blok 1. Kat"),
    ("2026-10-09", "Program", "B Blok 1. Kat"),
    ("2026-10-23", "Program", "B Blok 1. Kat"),
    ("2026-11-06", "Program", "B Blok 1. Kat"),
    ("2026-11-20", "Program", "B Blok 1. Kat"),
    ("2026-12-04", "Program", "B Blok 1. Kat"),
    ("2026-12-18", "Program", "B Blok 1. Kat"),
    ("2026-12-18", "Bireysel Görüşme (Esra Canlı - 16:00)", "B Blok 1. Kat"),
]

tomorrow = date.today() + timedelta(days=1)
tomorrow_str = tomorrow.strftime("%Y-%m-%d")
day_name = tomorrow.strftime("%A")

reminders = []
for dt_str, event_type, location in schedule:
    if dt_str == tomorrow_str:
        reminders.append(f"📌 **{event_type}** — {location}")

if reminders:
    msg = f"⚠️ **Yarın Denetimli Serbestlik randevun var!**\n\nTarih: {tomorrow.strftime('%d %B %Y')} ({day_name})\nSaat: 15:30\n\n" + "\n".join(reminders)
    msg += "\n\nHazırlığını yap, aksatma! 💪"
    print(msg)
else:
    # Silent — nothing to report
    pass
