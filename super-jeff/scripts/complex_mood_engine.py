#!/usr/bin/env python3
"""Complex Mood Engine — 8 temel duyguyu birleştirerek karmaşık duygu durumları üretir.
Mood Engine'in genişletilmiş halidir: aynı anda 2 duygu birleştirebilir."""

import json
import os
import random
from typing import Dict, List, Tuple, Optional

MOOD_STATE_PATH = os.path.expanduser("~/.hermes/brain/mood_state.json")

BASE_MOODS = {
    "sakin": {"enerji": 0.3, "polarite": 0.0, "renk": "mavi"},
    "hevesli": {"enerji": 0.9, "polarite": 0.8, "renk": "turuncu"},
    "endişeli": {"enerji": 0.6, "polarite": -0.4, "renk": "gri"},
    "kararlı": {"enerji": 0.8, "polarite": 0.3, "renk": "kırmızı"},
    "esprili": {"enerji": 0.7, "polarite": 0.9, "renk": "sarı"},
    "şefkatli": {"enerji": 0.4, "polarite": 0.7, "renk": "pembe"},
    "meraklı": {"enerji": 0.8, "polarite": 0.5, "renk": "yeşil"},
    "hüzünlü": {"enerji": 0.2, "polarite": -0.6, "renk": "lacivert"},
}

# İki duygu birleşim tablosu
BLEND_TABLE = {
    ("endişeli", "meraklı"): "tedirgin heyecan",
    ("hevesli", "meraklı"): "coşkulu keşif",
    ("endişeli", "kararlı"): "gergin kararlılık",
    ("hüzünlü", "sakin"): "dingin melankoli",
    ("meraklı", "sakin"): "sessiz merak",
    ("hevesli", "hüzünlü"): "buruk sevinç",
    ("esprili", "kararlı"): "sert şaka",
    ("hüzünlü", "şefkatli"): "içli merhamet",
    ("esprili", "sakin"): "ince espri",
    ("endişeli", "hüzünlü"): "kaygılı melankoli",
    ("hevesli", "kararlı"): "azimli coşku",
    ("kararlı", "sakin"): "soğukkanlı kararlılık",
    ("endişeli", "şefkatli"): "koruyucu kaygı",
    ("esprili", "hüzünlü"): "kara mizah",
    ("hevesli", "sakin"): "dingin neşe",
}


def _load_current_mood() -> dict:
    """Mevcut duygu durumunu yükle."""
    if os.path.exists(MOOD_STATE_PATH):
        try:
            with open(MOOD_STATE_PATH) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"mood": "sakin", "intensity": 0.5}


def _save_mood(state: dict) -> None:
    """Duygu durumunu kaydet."""
    os.makedirs(os.path.dirname(MOOD_STATE_PATH), exist_ok=True)
    with open(MOOD_STATE_PATH, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def get_base_mood(mood: str) -> dict:
    """Bir temel duygunun özelliklerini döndür."""
    return BASE_MOODS.get(mood, BASE_MOODS["sakin"])


def blend_moods(mood1: str, mood2: str) -> str:
    """İki duyguyu birleştir, isimlendirilmiş karma duygu döndür."""
    key = tuple(sorted([mood1, mood2]))
    if key in BLEND_TABLE:
        return BLEND_TABLE[key]
    # Bilinmeyen kombinasyon: ortalama enerji + polarite
    m1 = get_base_mood(mood1)
    m2 = get_base_mood(mood2)
    avg_energy = (m1["enerji"] + m2["enerji"]) / 2
    avg_pol = (m1["polarite"] + m2["polarite"]) / 2
    if avg_pol > 0.3:
        if avg_energy > 0.6:
            return f"canlı {mood1}-{mood2}"
        return f"yumuşak {mood1}-{mood2}"
    elif avg_pol < -0.3:
        return f"ağır {mood1}-{mood2}"
    return f"{mood1}-{mood2} karışımı"


def get_current_complex_mood() -> dict:
    """Mevcut duygu durumunu karmaşık formatta döndür.
    Dönüş: {primary_mood, secondary_mood, blend_name, intensity, energy, polarity}
    """
    state = _load_current_mood()
    primary = state.get("mood", "sakin")
    intensity = state.get("intensity", 0.5)

    # İkincil duygu seç (primary'e yakın ama aynı değil)
    candidates = [m for m in BASE_MOODS if m != primary]
    weights = []
    base = get_base_mood(primary)
    for c in candidates:
        cb = get_base_mood(c)
        # Enerji ve polarite farkına göre ağırlık
        enerji_fark = 1.0 - abs(base["enerji"] - cb["enerji"])
        polarite_fark = 1.0 - abs(base["polarite"] - cb["polarite"])
        weights.append(enerji_fark * 0.5 + polarite_fark * 0.5)
    total = sum(weights)
    if total > 0:
        probs = [w / total for w in weights]
        secondary = random.choices(candidates, weights=probs, k=1)[0]
    else:
        secondary = "sakin"

    blend = blend_moods(primary, secondary)
    base_p = get_base_mood(primary)
    base_s = get_base_mood(secondary)

    return {
        "primary_mood": primary,
        "secondary_mood": secondary,
        "blend_name": blend,
        "intensity": intensity,
        "energy": (base_p["enerji"] + base_s["enerji"]) / 2,
        "polarity": (base_p["polarite"] + base_s["polarite"]) / 2,
    }


def set_mood(primary: str, secondary: Optional[str] = None,
             intensity: float = 0.5) -> dict:
    """Duygu durumunu manuel set et."""
    if primary not in BASE_MOODS:
        raise ValueError(f"Bilinmeyen duygu: {primary}. "
                         f"Geçerli: {list(BASE_MOODS.keys())}")
    state = {"mood": primary, "intensity": max(0.0, min(1.0, intensity))}
    _save_mood(state)
    return get_current_complex_mood()


def list_blends() -> List[Dict]:
    """Tüm bilinen duygu birleşimlerini listele."""
    result = []
    for (m1, m2), name in sorted(BLEND_TABLE.items()):
        result.append({
            "mood1": m1, "mood2": m2,
            "base1": get_base_mood(m1),
            "base2": get_base_mood(m2),
            "blend_name": name,
        })
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--list":
        for b in list_blends():
            print(f"  {b['mood1']:10s} + {b['mood2']:10s} → {b['blend_name']}")
    else:
        cm = get_current_complex_mood()
        print(f"Primary: {cm['primary_mood']}")
        print(f"Secondary: {cm['secondary_mood']}")
        print(f"Blend: {cm['blend_name']}")
        print(f"Intensity: {cm['intensity']:.2f}")
        print(f"Energy: {cm['energy']:.2f}")
        print(f"Polarity: {cm['polarity']:.2f}")
