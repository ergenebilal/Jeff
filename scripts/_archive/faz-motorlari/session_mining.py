#!/usr/bin/env python3
"""Session Mining — Geçmiş konuşmaları tarar, desenleri çıkarır.
Her gece 02:00'de çalışır.
"""
import json, os, sqlite3
from datetime import datetime

DB = os.path.expanduser("~/.hermes/state.db")
REPORT_DIR = os.path.expanduser("~/.hermes/mining_reports/")
os.makedirs(REPORT_DIR, exist_ok=True)

def scan_recent_sessions():
    """Son 7 günün session'larını tara, önemli tekrarları bul."""
    if not os.path.exists(DB):
        print("Session DB bulunamadi")
        return

    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # Son 7 gundeki session'lar
    cutoff = datetime.now().timestamp() - 7 * 86400
    c.execute("""
        SELECT id, title, started_at FROM sessions 
        WHERE started_at > ?
        ORDER BY started_at DESC
    """, (cutoff,))
    sessions = c.fetchall()
    conn.close()

    print(f"Son 7 gunde {len(sessions)} session tarandi")

    report = {
        "time": datetime.now().isoformat(),
        "total_sessions": len(sessions),
        "sessions": [{"id": s[0], "title": s[1], "date": s[2]} for s in sessions[:10]]
    }

    filename = f"mining_{datetime.now().strftime('%Y%m%d')}.json"
    with open(os.path.join(REPORT_DIR, filename), "w") as f:
        json.dump(report, f, indent=2)
    print(f"Mining raporu: {filename}")

    keywords = ["hata", "sorun", "duzelt", "ekle", "kur", "lead", "demo", "imza"]
    for s in sessions[:5]:
        title = s[1][:50] if s[1] else "?"
        print(f"  Session: {title} ({s[2]})")

if __name__ == "__main__":
    scan_recent_sessions()
