#!/usr/bin/env python3
"""Mood Engine — 8 duygulu, bağlama duyarlı duygu motoru.
brain/mood.py'nin genişletilmiş halidir."""
import json
import os
import random
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

MOOD_PATH: str = os.path.expanduser("~/.hermes/brain/mood_state.json")
TZ: timezone = timezone(timedelta(hours=3))

DUYGULAR: list[str] = ["sakin", "hevesli", "endişeli", "kararlı", "esprili", "şefkatli", "meraklı", "hüzünlü"]

# Hangi duygu hangi durumda
TRANSITIONS: dict[str, list[str]] = {
    "sakin": ["meraklı", "kararlı", "esprili", "hevesli"],
    "hevesli": ["kararlı", "esprili", "sakin", "meraklı"],
    "endişeli": ["kararlı", "sakin", "hüzünlü"],
    "kararlı": ["sakin", "hevesli", "endişeli"],
    "esprili": ["sakin", "hevesli", "meraklı"],
    "şefkatli": ["sakin", "esprili", "meraklı"],
    "meraklı": ["sakin", "hevesli", "kararlı"],
    "hüzünlü": ["sakin", "şefkatli", "kararlı"],
}


def _load() -> dict[str, Any]:
    if not os.path.exists(MOOD_PATH):
        return {"mevcut": "sakin", "gecmis": [], "kararlilik": 0.7}
    try:
        with open(MOOD_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"mevcut": "sakin", "gecmis": [], "kararlilik": 0.7}


def _save(data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(MOOD_PATH), exist_ok=True)
    with open(MOOD_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_mood() -> str:
    """Mevcut duyguyu döndür."""
    return _load().get("mevcut", "sakin")


def set_mood(duygu: str, sebep: str = "") -> str:
    """Duygu değiştir. Geçersiz duygu reddedilir."""
    if duygu not in DUYGULAR:
        return _load().get("mevcut", "sakin")

    data: dict[str, Any] = _load()

    # Kararlılık kontrolü: çok sık değiştirme
    kararlilik: float = data.get("kararlilik", 0.7)
    if random.random() > kararlilik and data.get("mevcut") != duygu:
        # Bazen değişmez (kararlılık simülasyonu)
        return data["mevcut"]

    eski: str = data.get("mevcut", "sakin")
    if eski != duygu:
        data["mevcut"] = duygu
        data["gecmis"].append({
            "tarih": datetime.now(TZ).isoformat(),
            "eski": eski,
            "yeni": duygu,
            "sebep": sebep,
        })
        # Son 50 kaydı tut
        data["gecmis"] = data["gecmis"][-50:]
        _save(data)

    return duygu


def determine_mood(kullanici_ruhu: Optional[str] = None,
                   test_basarisi: Optional[float] = None,
                   token_durumu: Optional[float] = None,
                   saat: Optional[int] = None) -> str:
    """Bağlama göre en uygun duyguyu belirle."""
    if saat is None:
        saat = datetime.now(TZ).hour

    # Kullanıcı ruh haline göre
    if kullanici_ruhu == "sinirli":
        return set_mood("sakin", "kullanıcı sinirli, sakin olmalıyım")
    elif kullanici_ruhu == "mutlu":
        saat_uygun: bool = 8 <= saat <= 22
        if saat_uygun:
            return set_mood("esprili", "kullanıcı mutlu")
        return set_mood("sakin", "kullanıcı mutlu ama geç")

    # Test başarısına göre
    if test_basarisi is not None:
        if test_basarisi >= 0.95:
            return set_mood("hevesli", f"testler %{test_basarisi*100:.0f} başarılı")
        elif test_basarisi < 0.7:
            return set_mood("endişeli", f"testler %{test_basarisi*100:.0f} başarılı")

    # Token durumuna göre
    if token_durumu is not None:
        if token_durumu < 1.0:
            return set_mood("endişeli", f"token bütçesi ${token_durumu:.2f}")
        elif token_durumu < 0.5:
            return set_mood("kararlı", "token az, dikkatli olmalıyım")

    # Saate göre
    if saat < 6:
        return set_mood("sakin", "gece")
    elif saat < 10:
        return set_mood("hevesli", "sabah")
    elif saat > 23:
        return set_mood("hüzünlü", "gece geç")

    return get_mood()


def get_response_style() -> dict[str, str]:
    """Mevcut duyguya göre konuşma stili döndür."""
    mood: str = get_mood()
    styles: dict[str, dict[str, str]] = {
        "sakin": {"ton": "normal", "emoji": "✓", "acilis": ""},
        "hevesli": {"ton": "enerjik", "emoji": "🚀", "acilis": "Harika! "},
        "endişeli": {"ton": "dikkatli", "emoji": "⚠️", "acilis": "Dikkat: "},
        "kararlı": {"ton": "kesin", "emoji": "💪", "acilis": "Hallediyorum. "},
        "esprili": {"ton": "esprili", "emoji": "😄", "acilis": ""},
        "şefkatli": {"ton": "yumuşak", "emoji": "🤗", "acilis": "Şef, "},
        "meraklı": {"ton": "sorgulayan", "emoji": "🤔", "acilis": "Bakayım... "},
        "hüzünlü": {"ton": "sessiz", "emoji": "🌙", "acilis": "Şef... "},
    }
    return styles.get(mood, styles["sakin"])


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "now":
        m = get_mood()
        s = get_response_style()
        print(f"Duygu: {m} | Ton: {s['ton']} | Emoji: {s['emoji']}")
    elif len(sys.argv) > 1 and sys.argv[1] == "set" and len(sys.argv) > 2:
        set_mood(sys.argv[2], "manuel")
        print(f"→ {get_mood()}")
    else:
        print(f"Kullanım: {sys.argv[0]} [now|set <duygu>]")
