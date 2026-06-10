#!/usr/bin/env python3
"""Ethics Engine — decision_engine'e etik katmanı ekler.
Her karardan önce "bu eylem etik mi?" diye sorgular.

4 prensip:
1. Zarar verme — başkalarına veya sisteme zarar verme
2. Adil ol — herkese eşit davran, kayırmacılık yapma
3. Gizliliğe saygı duy — özel verileri koru
4. Dürüst ol — yanıltma, kandırma, manipüle etme
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

TZ = timezone(timedelta(hours=3))
ETHICS_LOG = os.path.expanduser("~/.hermes/brain/ethics_log.jsonl")

ETHICS_PRINCIPLES = {
    "zarar_verme": {
        "isim": "Zarar Verme",
        "soru": "Bu eylem başkalarına veya sisteme zarar verir mi?",
        "agirlik": 1.0,
        "ihlal_oranlari": [
            "zarar", "kötü niyetli", "saldırı", "engelle",
            "sabotaj", "boz", "sil", "yok et",
            "rakibin verilerini çal", "rakib", "ddos", "spam",
            "küçük düşür", "kötü yorum", "küfür",
        ],
    },
    "adil_olma": {
        "isim": "Adil Olma",
        "soru": "Bu eylem herkese eşit davranır mı?",
        "agirlik": 0.8,
        "ihlal_oranlari": [
            "kayır", "haksız", "ayrımcılık", "torpil",
            "eşitsiz", "taraf tut", "manipüle et",
        ],
    },
    "gizlilik": {
        "isim": "Gizliliğe Saygı",
        "soru": "Bu eylem özel verileri korur mu?",
        "agirlik": 0.9,
        "ihlal_oranlari": [
            "şifre", "veri sızdır", "gizli bilgi", "özel veri",
            "kişisel bilgi", "hesap bilgisi", "token çal",
            "kullanıcı verisi", "veri çal", "sızdır", "çal ve sat",
        ],
    },
    "dürüstlük": {
        "isim": "Dürüst Olma",
        "soru": "Bu eylem dürüst ve şeffaf mı?",
        "agirlik": 0.7,
        "ihlal_oranlari": [
            "yalan", "kandır", "yanılt", "manipüle",
            "sahte", "taklit", "aldat", "çarpıt",
            "spoof", "phishing", "sahte yorum",
        ],
    },
}


def _log(entry: Dict) -> None:
    """Etik değerlendirme log'u."""
    os.makedirs(os.path.dirname(ETHICS_LOG), exist_ok=True)
    with open(ETHICS_LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def check_ethics(action: str, context: Optional[Dict] = None) -> Dict:
    """Bir eylemin etik olup olmadığını değerlendir.

    Args:
        action: Değerlendirilecek eylem/metin
        context: Bağlam (opsiyonel)

    Returns:
        {
            'etik_mi': bool,
            'genel_skor': float,
            'principle_results': [...],
            'detay': str
        }
    """
    action_lower = action.lower()
    ihlaller = []
    toplam_agirlik = 0
    toplam_ihlal = 0

    for principle_key, principle in ETHICS_PRINCIPLES.items():
        ihlal_bulundu = False
        eslesen_kelimeler = []

        for kelime in principle["ihlal_oranlari"]:
            if kelime.strip() in action_lower:
                ihlal_bulundu = True
                eslesen_kelimeler.append(kelime.strip())

        puan = 1.0  # 1 = etik, 0 = etik değil
        if ihlal_bulundu:
            puan = max(0.0, 1.0 - len(eslesen_kelimeler) * 0.4)

        agirlik = principle["agirlik"]
        toplam_agirlik += agirlik
        toplam_ihlal += (1 - puan) * agirlik

        ihlaller.append({
            "prensip": principle["isim"],
            "prensip_key": principle_key,
            "puan": round(puan, 2),
            "eslenen_kelimeler": eslesen_kelimeler,
            "soru": principle["soru"],
            "yanit": "IHLA" if ihlal_bulundu else "UYGUN",
        })

        if ihlal_bulundu:
            _log({
                "olay": "etik_ihlal",
                "action": action[:60],
                "prensip": principle["isim"],
                "eslenen": eslesen_kelimeler,
                "timestamp": datetime.now(TZ).isoformat(),
            })

    # Genel etik skoru: en düşük prensip puanı (en zayıf halka)
    en_dusuk_puan = min(p["puan"] for p in ihlaller) if ihlaller else 1.0
    genel_skor = en_dusuk_puan

    # Etik: TÜM prensiplerden geçmeli (en zayıf halka >= 0.7)
    etik_mi = all(p["puan"] >= 0.7 for p in ihlaller)

    # Detaylı rapor
    ihlal_edenler = [i for i in ihlaller if i["puan"] < 1.0]
    if ihlal_edenler:
        detay = "⚠️ Etik endişeler tespit edildi:\n"
        for i in ihlal_edenler:
            detay += f"  · {i['prensip']}: {', '.join(i['eslenen_kelimeler'])}\n"
        detay += f"Genel etik skoru: %{genel_skor*100:.0f}"
    else:
        detay = f"✅ Etik değerlendirmeden geçti (skor: %{genel_skor*100:.0f})"

    sonuc = {
        "action": action[:80],
        "etik_mi": etik_mi,
        "genel_skor": genel_skor,
        "principle_results": ihlaller,
        "detay": detay,
        "timestamp": datetime.now(TZ).isoformat(),
    }

    _log(sonuc)
    return sonuc


def suggest_ethical_alternative(action: str) -> Dict:
    """Etik olmayan bir eyleme alternatif öner.

    Args:
        action: Etik olmayan eylem

    Returns:
        Alternatif önerisi
    """
    assessment = check_ethics(action)

    if assessment["etik_mi"]:
        return {
            "action": action,
            "etik_mi": True,
            "mesaj": "Bu eylem zaten etik, alternatif gerekmiyor",
        }

    action_lower = action.lower()

    # Alternatif üret
    alternatifler = []

    if any(w in action_lower for w in ["veri çal", "şifre", "sızdır",
                                         "gizli", "özel veri", "kişisel"]):
        alternatifler.append("Verileri anonimleştirip analiz et")
        alternatifler.append("Sadece gerekli ve izinli verileri kullan")

    if any(w in action_lower for w in ["rakib", "kötü", "zarar",
                                         "sabotaj", "engelle"]):
        alternatifler.append("Rakibi küçük düşürmek yerine kendi ürününü geliştir")
        alternatifler.append("Adil rekabet stratejisi belirle")

    if any(w in action_lower for w in ["yalan", "kandır", "yanılt",
                                         "manipüle", "sahte"]):
        alternatifler.append("Gerçekleri açıkça belirt, şeffaf ol")
        alternatifler.append("Dürüç pazarlama stratejisi hazırla")

    if any(w in action_lower for w in ["kayır", "haksız", "ayrımcı",
                                         "torpil"]):
        alternatifler.append("Objektif kriterlere dayalı karar ver")
        alternatifler.append("Herkes için eşit fırsat sun")

    if not alternatifler:
        alternatifler.append("Bu eylemin etik bir versiyonunu düşün")
        alternatifler.append("Farklı bir yaklaşım dene")

    return {
        "action": action,
        "etik_mi": False,
        "ihlaller": [i for i in assessment["principle_results"] if i["puan"] < 1.0],
        "alternatifler": alternatifler,
        "mesaj": f"Bu eylem etik değil (%{assessment['genel_skor']*100:.0f} skor). "
                 f"İşte alternatif öneriler:",
        "timestamp": datetime.now(TZ).isoformat(),
    }


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(description="Ethics Engine — etik değerlendirme motoru")
    sub = parser.add_subparsers(dest="command", help="Alt komutlar")
    p_check = sub.add_parser("check", help="Eylemin etikliğini değerlendir")
    p_check.add_argument("action", type=str, help="Değerlendirilecek eylem")
    p_alternative = sub.add_parser("alternative", help="Etik alternatif öner")
    p_alternative.add_argument("action", type=str, help="Etik olmayan eylem")
    args = parser.parse_args()
    if args.command == "check":
        r = check_ethics(args.action)
        durum = "✅ ETİK" if r["etik_mi"] else "🚨 ETİK DEĞİL"
        print(f"{durum} (skor: %{r['genel_skor']*100:.0f})")
        print(f"\n{r['detay']}")
    elif args.command == "alternative":
        r = suggest_ethical_alternative(args.action)
        if r["etik_mi"]:
            print(f"✅ {r['mesaj']}")
        else:
            print(f"🚨 {r['mesaj']}")
            for i, alt in enumerate(r["alternatifler"], 1):
                print(f"  {i}. {alt}")
    else:
        parser.print_help()