#!/usr/bin/env python3
"""Reality Check — dış kaynaklardan gelen bilgilerin doğruluğunu sorgula.
reality-checker rolünün motoru."""
import json
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

REALITY_PATH: str = os.path.expanduser("~/.hermes/brain/reality_checks.json")
TZ: timezone = timezone(timedelta(hours=3))
GUVENILIR_KAYNAKLAR: list[str] = [
    "github.com", "gitlab.com", "docs.python.org", "pypi.org",
    "npmjs.com", "docker.com", "kubernetes.io", "nginx.org",
    "postgresql.org", "mysql.com", "redis.io",
]


def _load() -> list[dict[str, Any]]:
    if not os.path.exists(REALITY_PATH):
        return []
    try:
        with open(REALITY_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save(data: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(REALITY_PATH), exist_ok=True)
    with open(REALITY_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def check_kaynak(url: str) -> dict[str, Any]:
    """Bir URL'nin güvenilirliğini değerlendir."""
    sonuc: dict[str, Any] = {
        "url": url,
        "guvenilir": False,
        "sebep": "",
    }

    # Bilinen güvenilir kaynaklar
    for guvenilir in GUVENILIR_KAYNAKLAR:
        if guvenilir in url.lower():
            sonuc["guvenilir"] = True
            sonuc["sebep"] = f"bilinen güvenilir kaynak: {guvenilir}"
            return sonuc

    # Şüpheli domain'ler
    supheli: list[str] = [r"\.xyz$", r"\.top$", r"free.*\.com", r"best.*\.site"]
    for s in supheli:
        if re.search(s, url.lower()):
            sonuc["guvenilir"] = False
            sonuc["sebep"] = f"şüpheli domain pattern: {s}"
            return sonuc

    # HTTPS kontrolü
    if not url.startswith("https://"):
        sonuc["guvenilir"] = False
        sonuc["sebep"] = "HTTPS kullanılmıyor"
        return sonuc

    # Bilinmiyor — nötr
    sonuc["guvenilir"] = None
    sonuc["sebep"] = "tanınmayan kaynak, doğrulama gerekli"
    return sonuc


def check_veri_kaynagi(kaynak_turu: str, veri: str) -> dict[str, Any]:
    """Bir veri kaynağının güvenilirliğini değerlendir."""
    sonuc: dict[str, Any] = {
        "kaynak": kaynak_turu,
        "guvenilirlik": "orta",
        "notlar": [],
    }

    if kaynak_turu == "tavily_web":
        sonuc["guvenilirlik"] = "orta"
        sonuc["notlar"].append("Tavily genel web arar, doğruluk garantisi yok")
        sonuc["notlar"].append(f"Veri boyutu: {len(veri)} karakter — kısa sonuçlar güvenilmez olabilir")
    elif kaynak_turu == "terminal":
        sonuc["guvenilirlik"] = "yüksek"
        sonuc["notlar"].append("Direkt sistem çıktısı, en güvenilir kaynak")
    elif kaynak_turu == "kullanici":
        sonuc["guvenilirlik"] = "yüksek"
        sonuc["notlar"].append("Kullanıcı bilgisi, niyetine güvenilir")
    elif kaynak_turu == "ai_tahmin":
        sonuc["guvenilirlik"] = "düşük"
        sonuc["notlar"].append("AI tahmini, halüsinasyon riski var — doğrulanmalı")
    else:
        sonuc["guvenilirlik"] = "düşük"
        sonuc["notlar"].append("Bilinmeyen kaynak türü")

    return sonuc


def log_reality_check(konu: str, kaynak: str, karar: str) -> dict[str, Any]:
    """Gerçeklik kontrolünü logla."""
    entry: dict[str, Any] = {
        "timestamp": datetime.now(TZ).isoformat(),
        "konu": konu,
        "kaynak": kaynak,
        "karar": karar,
    }
    data: list[dict[str, Any]] = _load()
    data.append(entry)
    _save(data)
    return entry


def weekly_audit() -> str:
    """Son 7 günün kararlarını ve kaynak kullanımını gözden geçir."""
    data: list[dict[str, Any]] = _load()
    since: str = (datetime.now(TZ) - timedelta(days=7)).isoformat()
    recent: list[dict[str, Any]] = [c for c in data if c.get("timestamp", "") >= since]

    if not recent:
        return "Son 7 günde gerçeklik kontrolü kaydı yok."

    lines: list[str] = [f"Son 7 günde {len(recent)} gerçeklik kontrolü:"]
    for c in recent[-10:]:
        lines.append(f"  {c['konu'][:40]} → {c['karar']} ({c['kaynak']})")
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "check" and len(sys.argv) > 2:
        r = check_kaynak(sys.argv[2])
        print(f"{'✅' if r['guvenilir'] else '❌'} {r['url']}")
        print(f"  {r['sebep']}")
    elif len(sys.argv) > 1 and sys.argv[1] == "audit":
        print(weekly_audit())
    else:
        print(f"Kullanım: {sys.argv[0]} [check <url>|audit]")
