#!/usr/bin/env python3
"""Aha Moments — çözümlerden pattern çıkarma ve transfer etme."""
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

AHA_PATH: str = os.path.expanduser("~/.hermes/brain/aha_moments.json")
TZ: timezone = timezone(timedelta(hours=3))


def _load() -> list[dict[str, Any]]:
    if not os.path.exists(AHA_PATH):
        return []
    try:
        with open(AHA_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save(data: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(AHA_PATH), exist_ok=True)
    with open(AHA_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def capture(problem: str, cozum: str, pattern: str,
            alternatif_kullanim: str, kategori: str = "genel") -> dict[str, Any]:
    """Bir çözümden çıkarılan pattern'i kaydet."""
    entry: dict[str, Any] = {
        "timestamp": datetime.now(TZ).isoformat(),
        "problem": problem,
        "cozum": cozum,
        "pattern": pattern,
        "alternatif_kullanim": alternatif_kullanim,
        "kategori": kategori,
        "kullanildi": False,
    }
    data: list[dict[str, Any]] = _load()
    data.append(entry)
    _save(data)
    return entry


def get_unused(limit: int = 5) -> list[dict[str, Any]]:
    """Henüz kullanılmamış pattern'leri getir."""
    return [a for a in _load() if not a.get("kullanildi")][:limit]


def mark_used(pattern_id: int) -> None:
    """Pattern'i kullanıldı olarak işaretle."""
    data: list[dict[str, Any]] = _load()
    if 0 <= pattern_id < len(data):
        data[pattern_id]["kullanildi"] = True
        data[pattern_id]["kullanildi_tarih"] = datetime.now(TZ).isoformat()
        _save(data)


def suggest_for(problem: str) -> Optional[dict[str, Any]]:
    """Bir probleme uygun pattern öner."""
    data: list[dict[str, Any]] = _load()
    problem_lower: str = problem.lower()
    for a in reversed(data):
        if a.get("kullanildi"):
            continue
        # Pattern açıklamasında problem kelimeleri geçiyor mu?
        if any(w in a.get("pattern", "").lower() for w in problem_lower.split()):
            return a
    return None


def get_stats() -> dict[str, Any]:
    data: list[dict[str, Any]] = _load()
    return {
        "toplam": len(data),
        "kullanilan": sum(1 for a in data if a.get("kullanildi")),
        "kullanilmayan": sum(1 for a in data if not a.get("kullanildi")),
        "kategoriler": list(set(a.get("kategori", "genel") for a in data)),
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        s = get_stats()
        print(f"Toplam: {s['toplam']}, Kullanılan: {s['kullanilan']}, Bekleyen: {s['kullanilmayan']}")
    elif len(sys.argv) > 2 and sys.argv[1] == "capture":
        capture(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "", "", "")
        print("✅ Pattern kaydedildi")
    elif len(sys.argv) > 1 and sys.argv[1] == "unused":
        for a in get_unused():
            print(f"  {a['pattern'][:60]}")
    else:
        print(f"Kullanım: {sys.argv[0]} [stats|capture <problem> <cozum>|unused]")
