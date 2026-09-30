#!/usr/bin/env python3
"""
CyberGene site funnel raporu — cerezsiz anonim olaylardan.
Kaynak: cybergene-chat/data/support_chat.db (events, sessions, messages)
Kullanim: python3 site_funnel.py [--days 7] [--json]
"""
import argparse, json, sqlite3, sys, datetime
from pathlib import Path

DB = Path("/home/hermes/cybergene-chat/data/support_chat.db")

# Huni sirasi: ziyaret -> showroom -> sohbet -> donusum
FUNNEL = [
    ("visit",          "Site ziyareti"),
    ("showroom_link",  "Showroom'a geçiş"),
    ("job_ask",        "Canlı asistana soru"),
    ("job_pick",       "Örnek iş seçimi"),
    ("faq_open",       "SSS açma"),
    ("whatsapp_click", "WhatsApp tıklama"),
    ("pilot_call",     "Ücretsiz görüşme talebi"),
    ("phone_click",    "Telefon tıklama"),
    ("email_click",    "E-posta tıklama"),
]
CONV = ["whatsapp_click", "pilot_call", "phone_click", "email_click"]


def q(sql, args=()):
    if not DB.exists():
        return []
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    try:
        return c.execute(sql, args).fetchall()
    finally:
        c.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=a.days)).strftime("%Y-%m-%d")

    # gunluk olay toplamlari
    rows = q("SELECT day, name, SUM(n) FROM events WHERE day>=? GROUP BY day,name", (since,))
    by_event = {}
    by_day = {}
    for day, name, n in rows:
        by_event[name] = by_event.get(name, 0) + n
        by_day.setdefault(day, {})[name] = by_day.get(day, {}).get(name, 0) + n

    # sohbet istatistigi
    sess_total = q("SELECT COUNT(DISTINCT session_id) FROM sessions")[0][0] if q("SELECT 1 FROM sessions LIMIT 1") else 0
    sess_period = q("SELECT COUNT(DISTINCT session_id) FROM sessions WHERE created_at>=?", ((datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=a.days)).isoformat(),))[0][0]
    msg_period = q("SELECT COUNT(*) FROM messages WHERE timestamp>=?", ((datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=a.days)).isoformat(),))[0][0]

    # sayfa kirilimi
    pages = q("SELECT path, SUM(n) FROM events WHERE day>=? GROUP BY path ORDER BY SUM(n) DESC LIMIT 10", (since,))

    out = {
        "period_days": a.days,
        "since": since,
        "events": by_event,
        "by_day": by_day,
        "chat": {"sessions_period": sess_period, "messages_period": msg_period, "sessions_total": sess_total},
        "pages": [{"path": p, "n": n} for p, n in pages],
        "conversions": sum(by_event.get(k, 0) for k in CONV),
    }

    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return

    print(f"📊 CyberGene Site Hunisi — son {a.days} gün (başlangıç {since})")
    print("=" * 52)
    print()
    print("HUNİ:")
    for key, label in FUNNEL:
        n = by_event.get(key, 0)
        bar = "█" * min(n, 40)
        print(f"  {label:24s} {n:5d}  {bar}")
    print()
    print(f"  {'DÖNÜŞÜM (wa+tel+mail+pilot)':24s} {out['conversions']:5d}")
    print()
    print("SOHBET:")
    print(f"  Oturum (dönem): {sess_period}   Mesaj (dönem): {msg_period}   Toplam oturum: {sess_total}")
    print()
    print("EN ÇOK GEZİLEN SAYFALAR:")
    for p in out["pages"]:
        print(f"  {p['n']:4d}  {p['path']}")
    print()
    print("GÜNLÜK:")
    for day in sorted(by_day):
        tot = sum(by_day[day].values())
        print(f"  {day}: {tot} olay")


if __name__ == "__main__":
    main()
