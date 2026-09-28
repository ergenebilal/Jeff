#!/usr/bin/env python3
"""Bilal Profili — duygu, enerji, tekrar takibi.
Her mesaj analiz edilir ve profile işlenir."""
import json
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

PROFILE_PATH: str = os.path.expanduser("~/.hermes/brain/bilal_profile.json")
TZ: timezone = timezone(timedelta(hours=3))

def _load() -> dict[str, Any]:
    if not os.path.exists(PROFILE_PATH):
        return {
            "son_durum": {},
            "tekrarlar": {},
            "enerji_gecmisi": [],
            "tercihler": {},
            "stres_esigi": 0.5,  # 0-1 arası, yüksek = daha toleranslı
        }
    try:
        with open(PROFILE_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def _save(data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)
    with open(PROFILE_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def analyze_message(mesaj: str) -> dict[str, Any]:
    """Mesajın duygu/enerji/stres seviyesini analiz et."""
    uzunluk: int = len(mesaj)
    kelime_sayisi: int = len(mesaj.split())

    # Stres belirteçleri
    stres_indikatorleri: list[str] = ["hemen", "acil", "çabuk", "şimdi", "yetmedi", "bıktım",
                                      "sıkıldım", "yap şunu", "durum kötü", "patladı", "sinir"]
    kufur_indikatorleri: list[str] = ["lan", "amk", "aq", "siktir", "salak", "gerizekalı"]

    stres_sayisi: int = sum(1 for w in stres_indikatorleri if w in mesaj.lower())
    kufur_sayisi: int = sum(1 for w in kufur_indikatorleri if w in mesaj.lower())

    # Enerji seviyesi (uzun mesaj + detay = yüksek enerji, kısa = düşük/acele)
    if uzunluk > 200:
        enerji: str = "yüksek"
    elif uzunluk > 50:
        enerji = "normal"
    elif uzunluk > 10:
        enerji = "düşük"
    else:
        enerji = "çok_düşük"

    # Stres seviyesi
    if stres_sayisi >= 3 or kufur_sayisi >= 2:
        stres: str = "yüksek"
    elif stres_sayisi >= 1 or kufur_sayisi >= 1:
        stres = "orta"
    elif uzunluk < 20:
        stres = "hafif"  # kısa mesaj acele = hafif stres
    else:
        stres = "düşük"

    # Ruh hali
    if kufur_sayisi >= 1 or stres_sayisi >= 3:
        ruh_hali: str = "sinirli"
    elif "harika" in mesaj.lower() or "iyiyim" in mesaj.lower() or "süper" in mesaj.lower():
        ruh_hali = "mutlu"
    elif "?" in mesaj and uzunluk > 100:
        ruh_hali = "meraklı"
    elif uzunluk < 20:
        ruh_hali = "acele"
    else:
        ruh_hali = "nötr"

    return {
        "uzunluk": uzunluk,
        "kelime_sayisi": kelime_sayisi,
        "enerji": enerji,
        "stres": stres,
        "ruh_hali": ruh_hali,
        "stres_sayisi": stres_sayisi,
        "kufur_sayisi": kufur_sayisi,
    }

def track_message(mesaj: str, kaynak: str = "telegram") -> dict[str, Any]:
    """Mesajı profile işle ve analiz döndür."""
    analiz: dict[str, Any] = analyze_message(mesaj)
    data: dict[str, Any] = _load()

    # Son durumu güncelle
    data["son_durum"] = {
        "tarih": datetime.now(TZ).isoformat(),
        "analiz": analiz,
        "kaynak": kaynak,
    }

    # Enerji geçmişine ekle (son 100 kayıt)
    data["enerji_gecmisi"].append({
        "tarih": datetime.now(TZ).isoformat(),
        "enerji": analiz["enerji"],
        "stres": analiz["stres"],
        "ruh_hali": analiz["ruh_hali"],
    })
    data["enerji_gecmisi"] = data["enerji_gecmisi"][-100:]

    _save(data)
    return analiz

def track_repetition(konu: str) -> int:
    """Bir konunun kaç kez tekrarlandığını takip et."""
    data: dict[str, Any] = _load()
    tekrarlar: dict[str, Any] = data.get("tekrarlar", {})
    konu_lower: str = konu.lower()

    if konu_lower in tekrarlar:
        tekrarlar[konu_lower]["sayi"] += 1
        tekrarlar[konu_lower]["son"] = datetime.now(TZ).isoformat()
    else:
        tekrarlar[konu_lower] = {
            "sayi": 1,
            "ilk": datetime.now(TZ).isoformat(),
            "son": datetime.now(TZ).isoformat(),
        }

    data["tekrarlar"] = tekrarlar
    _save(data)
    return tekrarlar[konu_lower]["sayi"]

def get_energy_trend() -> str:
    """Son 10 mesajın enerji trendi."""
    data: dict[str, Any] = _load()
    gecmis: list[dict[str, Any]] = data.get("enerji_gecmisi", [])[-10:]
    if not gecmis:
        return "bilinmiyor"

    yuksek: int = sum(1 for g in gecmis if g.get("enerji") == "yüksek")
    dusuk: int = sum(1 for g in gecmis if g.get("enerji") in ("düşük", "çok_düşük"))

    if yuksek >= 6:
        return "yükseliyor"
    elif dusuk >= 6:
        return "düşüyor"
    return "stabil"

def get_response_advice() -> dict[str, str]:
    """Mevcut profile göre yanıt önerisi üret."""
    data: dict[str, Any] = _load()
    son: dict[str, Any] = data.get("son_durum", {})
    analiz: dict[str, Any] = son.get("analiz", {})
    ruh: str = analiz.get("ruh_hali", "nötr")
    stres: str = analiz.get("stres", "düşük")
    enerji: str = analiz.get("enerji", "normal")

    ton: str = "normal"
    uzunluk_uyari: str = "normal"
    if ruh == "sinirli" or stres == "yüksek":
        ton = "sakin ve kısa"
        uzunluk_uyari = "çok kısa (maks 2 cümle)"
    elif ruh == "mutlu":
        ton = "esprili ve sıcak"
        uzunluk_uyari = "normal"
    elif ruh == "acele":
        ton = "net ve kısa"
        uzunluk_uyari = "kısa (maks 3 cümle)"
    elif enerji == "düşük":
        ton = "destekleyici ve şefkatli"
        uzunluk_uyari = "orta"
        return {"ton": ton, "uzunluk": uzunluk_uyari, "tavsiye": "Şef yorgun, moral ver, iş yükü önerme"}

    return {"ton": ton, "uzunluk": uzunluk_uyari}

def get_repetition_alert(konu: str) -> Optional[str]:
    """Bir konu 2+ kez tekrarlandıysa uyarı ver."""
    data: dict[str, Any] = _load()
    sayi: int = data.get("tekrarlar", {}).get(konu.lower(), {}).get("sayi", 0)
    if sayi >= 3:
        return f"Bunu {sayi}. tekrarlayışın. Önceki konuşmada şöyle çözmüştük..."
    elif sayi >= 2:
        return f"Bunu daha önce konuşmuştuk, hatırlatmamı ister misin?"
    return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "analyze" and len(sys.argv) > 2:
        sonuc = analyze_message(sys.argv[2])
        print(json.dumps(sonuc, indent=2, ensure_ascii=False))
    elif len(sys.argv) > 1 and sys.argv[1] == "advice":
        print(json.dumps(get_response_advice(), indent=2, ensure_ascii=False))
    elif len(sys.argv) > 1 and sys.argv[1] == "trend":
        print(get_energy_trend())
    else:
        print(f"Kullanım: {sys.argv[0]} [analyze <mesaj>|advice|trend]")
