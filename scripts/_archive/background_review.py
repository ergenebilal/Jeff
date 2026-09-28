#!/usr/bin/env python3
"""Background Review v1.0 - Proaktif on bellek ve skill guncelleme analizi.

Calisma: Her 30 dakikada bir hermes cron ile
Amac:
  1. suggest_next_action - son konusma konusuna gore bir sonraki ihtiyaci tahmin
  2. suggest_skill_update - son cozumleri tara, skill guncellemesi oner

Output: /home/hermes/.hermes/data/background_review.json
"""

import json
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

HOME = Path.home()
HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(HOME / ".hermes")))
OUTPUT_FILE = HERMES_HOME / "data" / "background_review.json"
SESSION_LOG = HERMES_HOME / "logs"
SKILLS_DIR = HERMES_HOME / "skills"

TURKIYE_SAAT = timezone(timedelta(hours=3))

_KONU_ANAHTARLARI = {
    "finans": [
        "borc", "borc", "odeme", "deme", "denizbank", "para", "gelir",
        "kredi", "bakiye", "usd", "eur", "dolar", "euro", "hesap", "bank",
    ],
    "radar": [
        "radar", "trafik", "denetim", "polis", "bursa", "mudanya", "yol",
    ],
    "teknik": [
        "server", "sunucu", "vps", "docker", "deploy", "kurmak", "kurulum",
        "hata", "bug", "error", "fail", "log", "backup", "nginx", "python", "node",
    ],
    "urun": [
        "gumroad", "urun", "urun", "satin", "satis", "pazarla", "dijital", "indir",
    ],
    "plan": [
        "plan", "strateji", "hedef", "yol haritasi", "karar", "gelecek", "vizyon",
    ],
}


def _son_konusmalar(limit=5):
    """Son oturum loglarindan konu basliklarini cikar."""
    konular = []
    if not SESSION_LOG.exists():
        return konular
    log_dosyalari = sorted(
        SESSION_LOG.glob("*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    for dosya in log_dosyalari[:limit]:
        try:
            with open(dosya, encoding="utf-8", errors="replace") as f:
                for satir in f.readlines()[-20:]:
                    satir = satir.strip()
                    if not satir:
                        continue
                    try:
                        veri = json.loads(satir)
                        msg = veri.get("content", veri.get("message", ""))
                        if msg and len(msg) > 5:
                            konular.append(msg[:200])
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue
    return konular


def _konu_analizi(konular):
    """Konu listesinden ana temayi cikar."""
    metin = " ".join(konular).lower()
    skorlar = {}
    for kategori, kelimeler in _KONU_ANAHTARLARI.items():
        skor = sum(1 for k in kelimeler if k in metin)
        if skor > 0:
            skorlar[kategori] = skor
    if not skorlar:
        return "genel"
    return max(skorlar, key=skorlar.get)


def _tahmin_uret(konu):
    """Konuya gore bir sonraki ihtiyaci tahmin et."""
    now = datetime.now(TURKIYE_SAAT)
    gun = now.strftime("%d %B %Y")

    tahminler = {
        "finans": {
            "tahmin": "Bilal yarin finans durumunu sorabilir.",
            "hazirlik": "Denizbank odeme tarihlerini kontrol et, bakiyeleri hazirla",
            "tetikleyici": "11 Haziran Denizbank odemesi yaklasiyor",
        },
        "radar": {
            "tahmin": "Bilal yarin yine radar sorgulayabilir.",
            "hazirlik": "Sabah 07:00 de Bursa radar noktalarini hazirla",
            "tetikleyici": "Bilal genelde sabah radar sorar",
        },
        "teknik": {
            "tahmin": "Bilal teknik bir konuda devam etmek isteyebilir.",
            "hazirlik": "Son teknik islemin durumunu kontrol et",
            "tetikleyici": "Teknik konuda yarim kalmis is olabilir",
        },
        "urun": {
            "tahmin": "Bilal urun satis durumunu sorabilir.",
            "hazirlik": "Gumroad satis rakamlarini ve yeni siparisleri hazirla",
            "tetikleyici": "Urun lansmani veya satis takibi",
        },
        "plan": {
            "tahmin": "Bilal strateji degerlendirmesi yapabilir.",
            "hazirlik": "Son kararlari ve ilerleme durumunu ozetle",
            "tetikleyici": "Planlama ve karar alma zamani",
        },
        "genel": {
            "tahmin": "Bilal genel durum sorgulayabilir.",
            "hazirlik": "Sistem durumu ve gunluk ozeti hazirla",
            "tetikleyici": "Genel durum takibi",
        },
    }

    base = tahminler.get(konu, tahminler["genel"])
    return {
        "zaman": gun,
        "konu": konu,
        "tahmin": base["tahmin"],
        "hazirlik": base["hazirlik"],
        "tetikleyici": base["tetikleyici"],
    }


def suggest_next_action():
    """Son konusmalara gore bir sonraki ihtiyaci tahmin et."""
    konular = _son_konusmalar()
    konu = _konu_analizi(konular)
    tahmin = _tahmin_uret(konu)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"type": "next_action", "data": tahmin, "updated": datetime.now(TURKIYE_SAAT).isoformat()},
            f,
            indent=2,
            ensure_ascii=False,
        )

    return tahmin


def suggest_skill_update():
    """Son cozumleri tara ve guncellenmesi gereken skill leri oner."""
    oneriler = []
    if not SKILLS_DIR.exists():
        return oneriler

    now = datetime.now()
    for skill_dizini in SKILLS_DIR.rglob("SKILL.md"):
        skill_adi = skill_dizini.parent.name
        skill_mtime = datetime.fromtimestamp(skill_dizini.stat().st_mtime)
        gun_farki = (now - skill_mtime).days

        if gun_farki >= 30:
            oneriler.append({
                "skill": skill_adi,
                "durum": "paslanmis",
                "son_guncelleme": skill_mtime.strftime("%Y-%m-%d"),
                "gun_gecmis": gun_farki,
                "oneri": f"{skill_adi} skill i {gun_farki} gundur guncellenmemis.",
            })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"type": "skill_update", "data": oneriler, "updated": datetime.now(TURKIYE_SAAT).isoformat()},
            f,
            indent=2,
            ensure_ascii=False,
        )

    return oneriler


def run_full_review():
    """Her iki analizi de calistir ve tek sonuc dondur."""
    next_action = suggest_next_action()
    skill_updates = suggest_skill_update()

    result = {
        "zaman": datetime.now(TURKIYE_SAAT).isoformat(),
        "next_action": next_action,
        "skill_updates": skill_updates,
        "skill_paslanmis_sayisi": len(skill_updates),
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result
