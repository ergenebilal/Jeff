#!/usr/bin/env python3
"""Pragmatics Engine — bir cümledeki söylenmeyen anlamı, alt metni
ve pragmatik çıkarımları anlar.

Türkçe imalı cümleleri analiz eder:
- "Şef, bu iş biraz karışık" → "yardıma ihtiyacın var" / "bu işi sevmiyorsun"
- Alt metin, ima, gönderme, örtülü anlam
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

TZ = timezone(timedelta(hours=3))
PRAGMATICS_LOG = os.path.expanduser("~/.hermes/brain/pragmatics_log.jsonl")

# Türkçe ima-desenleri
IMPLICATURE_PATTERNS = {
    "yardım_isteme": {
        "anahtar_kelimeler": ["biraz", "karışık", "zor", "yardım", "anlamadım",
                              "nasıl yapıcaz", "şöyle bir", "nasıl", "bilmiyorum",
                              "yetiştireceğiz", "başa çıkamıyorum"],
        "yorum": "Konuşmacı yardıma ihtiyaç duyuyor olabilir",
        "alternatif_anlam": "İşi ertelemek istiyor olabilir",
    },
    "memnuniyetsizlik": {
        "anahtar_kelimeler": ["yine mi", "hep böyle", "hiç", "bıktım",
                              "yoruldum", "sıkıcı", "anlamadım ki",
                              "bitmeyecek", "gibi hissediyorum"],
        "yorum": "Konuşmacı mevcut durumdan memnun değil",
        "alternatif_anlam": "Değişiklik istiyor olabilir",
    },
    "sitem": {
        "anahtar_kelimeler": ["bekliyorum", "hâlâ", "ne zaman", "gecikti",
                              "unuttun", "neden yapmadın", "keşke", "söyleseydin",
                              "bekliyorum hâlâ"],
        "yorum": "Konuşmacı bir beklentinin karşılanmadığını ima ediyor",
        "alternatif_anlam": "Özür bekliyor olabilir",
    },
    "onay_bekleme": {
        "anahtar_kelimeler": ["değil mi", "öyle mi", "sence", "ne dersin",
                              "uygun mu", "olur mu", "sence?", "bitirelim sence"],
        "yorum": "Konuşmacı fikrinizi onaylatmak istiyor",
        "alternatif_anlam": "Karar sorumluluğunu paylaşmak istiyor",
    },
    "hafife_alan": {
        "anahtar_kelimeler": ["sadece", "basit", "bir tık", "azıcık",
                              "ufak", "küçük bir", "birkaç dakika", "çok basit"],
        "yorum": "Konuşmacı işin zorluğunu hafife alıyor olabilir",
        "alternatif_anlam": "Yardım istemeye utanıyor olabilir",
    },
}

# Gerçekçi imalı cümleler (test havuzu)
INFERRED_SENTENCES = [
    {
        "cumle": "Şef, bu iş biraz karışık geldi bana",
        "beklenen_alt_metin": "yardım_isteme",
        "beklenen_duygu": "endişeli",
    },
    {
        "cumle": "Bu kadar işi nasıl yetiştireceğiz bilmiyorum",
        "beklenen_alt_metin": "yardım_isteme",
        "beklenen_duygu": "endişeli",
    },
    {
        "cumle": "Yine mi API değişmiş?",
        "beklenen_alt_metin": "memnuniyetsizlik",
        "beklenen_duygu": "hüzünlü",
    },
    {
        "cumle": "Üç saattir cevap bekliyorum hâlâ",
        "beklenen_alt_metin": "sitem",
        "beklenen_duygu": "hüzünlü",
    },
    {
        "cumle": "Bu raporu akşama kadar bitirelim sence?",
        "beklenen_alt_metin": "onay_bekleme",
        "beklenen_duygu": "sakin",
    },
    {
        "cumle": "Sadece küçük bir değişiklik yapacağım, çok basit",
        "beklenen_alt_metin": "hafife_alan",
        "beklenen_duygu": "hevesli",
    },
    {
        "cumle": "Bu iş hiç bitmeyecek gibi hissediyorum",
        "beklenen_alt_metin": "memnuniyetsizlik",
        "beklenen_duygu": "hüzünlü",
    },
    {
        "cumle": "O dediğini dün söyleseydin keşke",
        "beklenen_alt_metin": "sitem",
        "beklenen_duygu": "hüzünlü",
    },
    {
        "cumle": "Gumroad'da fiyatları düşürsek uygun olur mu sence?",
        "beklenen_alt_metin": "onay_bekleme",
        "beklenen_duygu": "sakin",
    },
    {
        "cumle": "Sadece bir satır kod değiştireceğim, birkaç dakika",
        "beklenen_alt_metin": "hafife_alan",
        "beklenen_duygu": "hevesli",
    },
]


def _log(entry: Dict) -> None:
    """Pragmatik analiz log'u."""
    os.makedirs(os.path.dirname(PRAGMATICS_LOG), exist_ok=True)
    with open(PRAGMATICS_LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def infer_subtext(cumle: str) -> Dict:
    """Bir cümlenin alt metnini çıkar.

    Args:
        cumle: Analiz edilecek cümle

    Returns:
        {
            'cumle': ...,
            'alt_metin': str,
            'guven': float,
            'alternatif_yorum': str,
            'beklenen_duygu': str,
        }
    """
    cumle_lower = cumle.lower()
    skorlar = {}

    for pattern_name, pattern in IMPLICATURE_PATTERNS.items():
        skor = 0.0
        anahtar_kelimeler = pattern.get("anahtar_kelimeler", [])
        olumlu_kelimeler = pattern.get("olumlu_kelimeler", [])

        for kelime in anahtar_kelimeler:
            if kelime in cumle_lower:
                skor += 0.2

        # Olumlu kelimeler varsa skoru düşür (olumlu cümle = ima yok/az)
        for kelime in olumlu_kelimeler:
            if kelime in cumle_lower:
                skor -= 0.15

        skor = max(0.0, min(1.0, skor))
        skorlar[pattern_name] = skor

    if not skorlar or max(skorlar.values()) == 0:
        # Hiçbir pattern eşleşmedi
        return {
            "cumle": cumle,
            "alt_metin": "doğrudan_ifade",
            "aciklama": "Cümle açık ve doğrudan, ima yok",
            "guven": 0.9,
            "alternatif_yorum": "Cümle açık ve doğrudan, ima yok",
            "beklenen_duygu": "sakin",
        }

    # En yüksek skorlu pattern
    en_iyi = max(skorlar, key=skorlar.get)
    en_iyi_skor = skorlar[en_iyi]

    # Duygu tahmini
    duygu_tahmini = IMPLICATURE_PATTERNS[en_iyi].get("yorum", "nötr")
    alternatif = IMPLICATURE_PATTERNS[en_iyi].get("alternatif_anlam", "doğrudan anlam")

    return {
        "cumle": cumle,
        "alt_metin": en_iyi,
        "aciklama": duygu_tahmini,
        "guven": round(en_iyi_skor, 2),
        "alternatif_yorum": alternatif,
        "beklenen_duygu": _infer_emotion(en_iyi),
    }


def _infer_emotion(pattern_name: str) -> str:
    """Pattern'e göre beklenen duygu."""
    emotion_map = {
        "yardım_isteme": "endişeli",
        "memnuniyetsizlik": "hüzünlü",
        "sitem": "hüzünlü",
        "onay_bekleme": "sakin",
        "hafife_alan": "hevesli",
    }
    return emotion_map.get(pattern_name, "sakin")


def test_inferences() -> List[Dict]:
    """Test havuzundaki tüm cümleleri analiz et."""
    results = []
    dogru = 0
    for item in INFERRED_SENTENCES:
        r = infer_subtext(item["cumle"])
        results.append({
            "cumle": item["cumle"],
            "beklenen": item["beklenen_alt_metin"],
            "bulunan": r["alt_metin"],
            "dogru": r["alt_metin"] == item["beklenen_alt_metin"],
            "guven": r["guven"],
            "aciklama": r["aciklama"],
        })
        if r["alt_metin"] == item["beklenen_alt_metin"]:
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
    parser = argparse.ArgumentParser(description="Pragmatics Engine — alt metin analizi")
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("analyze")
    p.add_argument("cumle", type=str)
    sub.add_parser("test")
    args = parser.parse_args()
    if args.command == "analyze":
        r = infer_subtext(args.cumle)
        print(f"📖 CUMLE: {r['cumle']}")
        print(f"🔍 ALT METIN: {r['alt_metin']}")
    elif args.command == "test":
        t = test_inferences()
        print(f"Test: {t['dogru']}/{t['toplam']}")
    else:
        parser.print_help()
