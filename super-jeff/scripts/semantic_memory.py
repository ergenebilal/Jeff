#!/usr/bin/env python3
"""Semantic Memory — brain/semantic_knowledge.json yöneticisi.
Öğrenilen kavramları, gerçekleri ve ilişkileri saklar."""
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

SEMANTIC_PATH: str = os.path.expanduser("~/.hermes/brain/semantic_knowledge.json")
TZ: timezone = timezone(timedelta(hours=3))


def _load() -> dict[str, Any]:
    """Semantic knowledge dosyasını oku."""
    if not os.path.exists(SEMANTIC_PATH):
        return {"kavramlar": [], "son_guncelleme": None}
    try:
        with open(SEMANTIC_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"kavramlar": [], "son_guncelleme": None}


def _save(data: dict[str, Any]) -> None:
    """Semantic knowledge dosyasına yaz."""
    data["son_guncelleme"] = datetime.now(TZ).isoformat()
    os.makedirs(os.path.dirname(SEMANTIC_PATH), exist_ok=True)
    with open(SEMANTIC_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def learn(kavram: str, aciklama: str, kategori: str = "genel",
          kaynak: str = "deneyim", onem: int = 5) -> dict[str, Any]:
    """Yeni bir kavram öğren. Varsa güncelle."""
    data: dict[str, Any] = _load()
    kavramlar: list[dict[str, Any]] = data["kavramlar"]

    # Var olanı bul
    for k in kavramlar:
        if k["kavram"].lower() == kavram.lower():
            k["aciklama"] = aciklama
            k["kategori"] = kategori
            k["kaynak"] = kaynak
            k["onem"] = onem
            k["guncellenme"] = datetime.now(TZ).isoformat()
            _save(data)
            return k

    # Yeni kavram
    entry: dict[str, Any] = {
        "kavram": kavram,
        "aciklama": aciklama,
        "kategori": kategori,
        "kaynak": kaynak,
        "onem": onem,
        "olusturulma": datetime.now(TZ).isoformat(),
        "guncellenme": datetime.now(TZ).isoformat(),
        "ziyaret_sayisi": 0,
    }
    kavramlar.append(entry)
    _save(data)
    return entry


def recall(kavram: str) -> Optional[dict[str, Any]]:
    """Bir kavramı hatırla. Ziyaret sayısını artırır."""
    data: dict[str, Any] = _load()
    for k in data["kavramlar"]:
        if kavram.lower() in k["kavram"].lower():
            k["ziyaret_sayisi"] = k.get("ziyaret_sayisi", 0) + 1
            _save(data)
            return k
    return None


def search(sorgu: str, kategori: Optional[str] = None) -> list[dict[str, Any]]:
    """Kavramlarda ara. İsme ve açıklamaya bakar."""
    data: dict[str, Any] = _load()
    sorgu_lower: str = sorgu.lower()
    results: list[dict[str, Any]] = []
    for k in data["kavramlar"]:
        if kategori and k.get("kategori") != kategori:
            continue
        if sorgu_lower in k["kavram"].lower() or sorgu_lower in k.get("aciklama", "").lower():
            results.append(k)
    return results


def get_unvisited(days: int = 30) -> list[dict[str, Any]]:
    """Belirtilen gündür ziyaret edilmeyen kavramları getir (unutma eğrisi)."""
    data: dict[str, Any] = _load()
    now = datetime.now(TZ)
    threshold = now - timedelta(days=days)
    unvisited: list[dict[str, Any]] = []
    for k in data["kavramlar"]:
        guncel = k.get("guncellenme", k.get("olusturulma", now.isoformat()))
        try:
            guncel_dt = datetime.fromisoformat(guncel)
            if guncel_dt < threshold:
                unvisited.append(k)
        except (ValueError, TypeError):
            continue
    return unvisited


def get_stats() -> dict[str, Any]:
    """Semantic bellek istatistikleri."""
    data: dict[str, Any] = _load()
    kavramlar: list[dict[str, Any]] = data["kavramlar"]
    kategoriler: dict[str, int] = {}
    for k in kavramlar:
        kat = k.get("kategori", "genel")
        kategoriler[kat] = kategoriler.get(kat, 0) + 1
    return {
        "toplam_kavram": len(kavramlar),
        "kategoriler": kategoriler,
        "son_guncelleme": data.get("son_guncelleme"),
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        s = get_stats()
        print(f"Toplam kavram: {s['toplam_kavram']}")
        for kat, sayi in sorted(s['kategoriler'].items()):
            print(f"  {kat}: {sayi}")
        print(f"Son güncelleme: {s['son_guncelleme']}")
    elif len(sys.argv) > 2 and sys.argv[1] == "search":
        results = search(sys.argv[2])
        for r in results:
            print(f"  {r['kavram']} ({r['kategori']}): {r['aciklama'][:80]}")
    elif len(sys.argv) > 1 and sys.argv[1] == "unvisited":
        uv = get_unvisited()
        print(f"{len(uv)} kavram uzun süredir ziyaret edilmedi:")
        for k in uv:
            print(f"  {k['kavram']} — son: {k.get('guncellenme','?')[:10]}")
    else:
        print(f"Kullanım: {sys.argv[0]} [stats|search <terim>|unvisited]")
