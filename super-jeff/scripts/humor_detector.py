#!/usr/bin/env python3
"""Humor Detector — espri, ironi, abartı, alay, kelime oyunu gibi
mizah türlerini tespit eder ve uygun duygusal tepkiyi üretir.

5 mizah türü:
1. İroni — söylenenin tersini kastetme
2. Alay — hafif küçümseme ile espri
3. Abartı — aşırı büyütme/küçültme
4. Kelime oyunu — çift anlamlı kelimeler
5. Kuru mizah — düz ifade ile espri
"""

import json
import os
import sys
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

TZ = timezone(timedelta(hours=3))
HUMOR_LOG = os.path.expanduser("~/.hermes/brain/humor_log.jsonl")

# Mizah türü tanımları
HUMOR_TYPE_DEFS = {
    "ironi": {
        "anahtarlar": ["tabii ki", "elbette", "harika", "mükemmel", "çok iyi",
                       "bayıldım", "şaşırdım mı", "yine mi", "tabii ki yine"],
        "ters_anlam": ["kötü", "berbat", "hiç iyi değil"],
        "ornek": "Tabii ki yine her şey mükemmel çalışıyor (aslında çalışmıyor)",
    },
    "alay": {
        "anahtarlar": ["bravo", "aferin", "helal", "vay be", "ne kadar zeki",
                       "dahi", "profesyonel", "çökerttin"],
        "kucumseme": ["sadece", "bir tek", "üstelik"],
        "ornek": "Bravo, bir satır kod değiştirdin, tüm site çöktü",
    },
    "abarti": {
        "anahtarlar": ["asla", "herkes", "milyon", "sonsuz", "ölüyorum",
                       "patladım", "bin yıl", "milyar", "en uzun", "dünyanın en"],
        "engelleyiciler": ["hiçbir şey", "yapmadım", "erteledim"],
        "ornek": "Bu kadar işin arasında kahve bile içemedim, susuzluktan ölüyorum",
    },
    "kelime_oyunu": {
        "anahtarlar": ["ayrılır", "ikiye ayrılır", "arasındaki fark",
                       "deyince akla", "gibi", "ama", "yani"],
        "es_anlamli": True,
        "ornek": "Yazılımcılar ikiye ayrılır: kod yazanlar ve kod yazdığını sananlar",
    },
    "kuru_mizah": {
        "anahtarlar": ["aslında", "yani şöyle", "düz mantık", "tam olarak",
                       "beklediğim gibi", "hiçbir şey yapmadım", "yapmam zaten",
                       "yarına erteledim"],
        "düz_ifade": True,
        "ornek": "Bugün hiçbir şey yapmadım, yarına bıraktım. Yarın da yapmam.",
    },
}

# Test cümleleri
TEST_SENTENCES = [
    {
        "cumle": "Tabii ki yine her şey harika, API yine değişmiş (tabii ki)",
        "beklenen": "ironi",
    },
    {
        "cumle": "Bravo, bir satır kod yazdın, tüm sistemi çökerttin aferin",
        "beklenen": "alay",
    },
    {
        "cumle": "Bu iş hiç bitmeyecek, dünyanın en uzun projesi bu",
        "beklenen": "abarti",
    },
    {
        "cumle": "Yazılımcılar ikiye ayrılır: test yazanlar ve test yazdığını sananlar",
        "beklenen": "kelime_oyunu",
    },
    {
        "cumle": "Bugün hiçbir şey yapmadım, yarına erteledim. Yarın da yapmam zaten",
        "beklenen": "kuru_mizah",
    },
]


def _log(entry: Dict) -> None:
    """Mizah analizi log'u."""
    os.makedirs(os.path.dirname(HUMOR_LOG), exist_ok=True)
    with open(HUMOR_LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def detect_humor(cumle: str) -> Dict:
    """Bir cümledeki mizah türünü tespit et.

    Args:
        cumle: Analiz edilecek cümle

    Returns:
        {
            'cumle': str,
            'mizah_turu': str,
            'guven': float,
            'aciklama': str,
            'duygusal_tepki': str,
            'alternatif': str
        }
    """
    cumle_lower = cumle.lower()
    skorlar = {}

    for humor_type, hdef in HUMOR_TYPE_DEFS.items():
        skor = 0.0
        for anahtar in hdef["anahtarlar"]:
            if anahtar in cumle_lower:
                skor += 0.25

        # Ters anlam kontrolü (ironi için)
        if humor_type == "ironi" and "ters_anlam" in hdef:
            for kelime in hdef["ters_anlam"]:
                if kelime in cumle_lower:
                    skor -= 0.1  # Gerçekten kötüyse ironi olmayabilir

        # Engelleyici kelime kontrolü
        if "engelleyiciler" in hdef:
            for kelime in hdef["engelleyiciler"]:
                if kelime in cumle_lower:
                    skor -= 0.4  # Engelleyici varsa bu tür olma ihtimali düşük

        skor = max(0.0, min(1.0, skor))
        if skor > 0:
            skorlar[humor_type] = skor

    if not skorlar:
        return {
            "cumle": cumle,
            "mizah_turu": "mizah_değil",
            "guven": 0.9,
            "aciklama": "Mizah tespit edilemedi, düz ifade",
            "duygusal_tepki": "nötr",
        }

    # En yüksek skorlu mizah türü
    en_iyi = max(skorlar, key=skorlar.get)
    en_iyi_skor = skorlar[en_iyi]

    # Duygusal tepki üret
    emotional_response = _generate_emotional_response(en_iyi, cumle)

    return {
        "cumle": cumle,
        "mizah_turu": en_iyi,
        "guven": round(en_iyi_skor, 2),
        "aciklama": f"{en_iyi.upper()} tespit edildi. Örnek: {HUMOR_TYPE_DEFS[en_iyi].get('ornek', '')}",
        "duygusal_tepki": emotional_response,
        "mood_onerisi": _recommend_mood(en_iyi),
    }


def _generate_emotional_response(humor_type: str, cumle: str) -> str:
    """Mizah türüne göre duygusal tepki üret."""
    responses = {
        "ironi": [
            "Espri yapıyorsun, ama ciddi kısmını da anlıyorum",
            "İroni dozajın yüksek bugün 😄",
            "Tersini söyleyerek anlatmak istediğini anladım",
        ],
        "alay": [
            "İnce alay var, tepki vermeden önce durup düşüneyim",
            "Hafif alaycı bir üslup sezdiğim kadarıyla",
            "Alayın dozunu ayarlıyorum, anlıyorum durumu 😅",
        ],
        "abarti": [
            "Abartıyı yakaladım, gerçek payını analiz ediyorum",
            "Biraz abartılı olmuş ama ana fikri anladım",
            "Mübalağa sanatı, mesaj alındı 🎯",
        ],
        "kelime_oyunu": [
            "Kelime oyunu yaptın, zekice!",
            "Çift anlamı fark ettim, güzel dokundurma",
            "Kelime oyununa geldim 😄",
        ],
        "kuru_mizah": [
            "Kuru mizah, ama içinde gerçek payı var",
            "Düz ifadeyle espri yapmak... klasik",
            "Soğuk espri, sıcak mesaj, anladım 😎",
        ],
    }
    return random.choice(responses.get(humor_type, ["Anladım"]))


def _recommend_mood(humor_type: str) -> str:
    """Mizah türüne göre önerilen duygu durumu."""
    mapping = {
        "ironi": "esprili",
        "alay": "esprili",
        "abarti": "hevesli",
        "kelime_oyunu": "esprili",
        "kuru_mizah": "sakin",
    }
    return mapping.get(humor_type, "sakin")


def test_humor_detection() -> Dict:
    """Test havuzundaki tüm cümleleri analiz et."""
    results = []
    dogru = 0
    for item in TEST_SENTENCES:
        r = detect_humor(item["cumle"])
        results.append({
            "cumle": item["cumle"][:60],
            "beklenen": item["beklenen"],
            "bulunan": r["mizah_turu"],
            "dogru": r["mizah_turu"] == item["beklenen"],
            "guven": r["guven"],
            "tepki": r["duygusal_tepki"],
        })
        if r["mizah_turu"] == item["beklenen"]:
            dogru += 1
        _log(r)

    return {
        "toplam": len(results),
        "dogru": dogru,
        "yanlis": len(results) - dogru,
        "sonuclar": results,
    }


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(description="Humor Detector — mizah tespit")
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("detect")
    p.add_argument("cumle", type=str)
    sub.add_parser("test")
    args = parser.parse_args()
    if args.command == "detect":
        r = detect_humor(args.cumle)
        print(f"📖 CUMLE: {r['cumle']}")
        print(f"🎭 MIZAH TURU: {r['mizah_turu']}")
    elif args.command == "test":
        h = test_humor_detection()
        print(f"Test: {h['dogru']}/{h['toplam']}")
    else:
        parser.print_help()
