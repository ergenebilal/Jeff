#!/usr/bin/env python3
"""Episodic Memory — brain/episodic_memory.jsonl yöneticisi.
Önemli olayları timestamp'li olarak kaydeder."""
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

EPISODIC_PATH: str = os.path.expanduser("~/.hermes/brain/episodic_memory.jsonl")
TZ: timezone = timezone(timedelta(hours=3))


def record(olay_tipi: str, ozet: str, sonuc: str = "",
           duygu_durumu: str = "nötr",
           ilgili_skill: str = "",
           metadata: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Yeni bir episodik olay kaydet. Otomatik timestamp ekler."""
    entry: dict[str, Any] = {
        "timestamp": datetime.now(TZ).isoformat(),
        "olay_tipi": olay_tipi,
        "ozet": ozet,
        "sonuc": sonuc,
        "duygu_durumu": duygu_durumu,
        "ilgili_skill": ilgili_skill,
    }
    if metadata:
        entry["metadata"] = metadata

    os.makedirs(os.path.dirname(EPISODIC_PATH), exist_ok=True)
    with open(EPISODIC_PATH, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    return entry


def recall(limit: int = 10,
           olay_tipi: Optional[str] = None,
           since: Optional[str] = None) -> list[dict[str, Any]]:
    """Son olayları getir. İsteğe bağlı filtreleme."""
    if not os.path.exists(EPISODIC_PATH):
        return []

    entries: list[dict[str, Any]] = []
    with open(EPISODIC_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    # Filtrele
    if olay_tipi:
        entries = [e for e in entries if e.get("olay_tipi") == olay_tipi]
    if since:
        entries = [e for e in entries if e.get("timestamp", "") >= since]

    # Reverse chronological
    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return entries[:limit]


def get_recent_summary(days: int = 1) -> str:
    """Son N günün özetini döndürür (sabah brifingi için)."""
    since: str = (datetime.now(TZ) - timedelta(days=days)).isoformat()
    recent: list[dict[str, Any]] = recall(limit=50, since=since)

    if not recent:
        return "Son 24 saatte kayda değer olay yok."

    lines: list[str] = [f"Son {days} günde {len(recent)} olay:"]
    for e in recent[:10]:
        ts: str = e.get("timestamp", "?")[11:19]  # sadece saat
        tip: str = e.get("olay_tipi", "?")
        ozet: str = e.get("ozet", "")[:80]
        sonuc: str = e.get("sonuc", "")
        icon: str = "✅" if "başarılı" in sonuc.lower() or "tamam" in sonuc.lower() else "ℹ️"
        lines.append(f"  {icon} [{ts}] {tip}: {ozet}")
    return "\n".join(lines)


def count_by_type() -> dict[str, int]:
    """Olay tiplerine göre dağılım."""
    if not os.path.exists(EPISODIC_PATH):
        return {}
    counts: dict[str, int] = {}
    with open(EPISODIC_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
                tip = e.get("olay_tipi", "bilinmeyen")
                counts[tip] = counts.get(tip, 0) + 1
            except json.JSONDecodeError:
                continue
    return counts


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        print(get_recent_summary())
    elif len(sys.argv) > 1 and sys.argv[1] == "count":
        for tip, sayi in sorted(count_by_type().items()):
            print(f"  {tip}: {sayi}")
    else:
        print(f"Kullanım: {sys.argv[0]} [summary|count]")
