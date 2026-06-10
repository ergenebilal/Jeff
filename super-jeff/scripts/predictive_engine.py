#!/usr/bin/env python3
"""Predictive Engine — geçmiş olaylardan olasılıksal tahmin modelleri oluşturur.
Decision Engine'in MCTS'sini genişletir: geçmiş veri + olasılık modeli."""

import json
import math
import os
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple
from collections import Counter

EPISODIC_PATH = os.path.expanduser("~/.hermes/brain/episodic_memory.jsonl")
SEMANTIC_PATH = os.path.expanduser("~/.hermes/brain/semantic_knowledge.json")
DECISION_LOG_PATH = os.path.expanduser("~/.hermes/brain/decision_log.json")

TZ = timezone(timedelta(hours=3))


def _load_episodic_all() -> List[Dict]:
    """Tüm episodik olayları yükle."""
    if not os.path.exists(EPISODIC_PATH):
        return []
    events = []
    try:
        with open(EPISODIC_PATH) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except IOError:
        return []
    return events


def _load_decision_log() -> List[Dict]:
    """Karar logunu yükle."""
    if not os.path.exists(DECISION_LOG_PATH):
        return []
    try:
        with open(DECISION_LOG_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _save_decision_log(entries: List[Dict]) -> None:
    """Karar logunu kaydet."""
    os.makedirs(os.path.dirname(DECISION_LOG_PATH), exist_ok=True)
    with open(DECISION_LOG_PATH, "w") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def analyze_patterns() -> Dict:
    """Geçmiş olaylardan örüntü çıkar.
    Dönüş: {'olay_tipi_istatistik': {...}, 'basari_oranlari': {...}, 'sik_kavramlar': [...]}
    """
    events = _load_episodic_all()
    if not events:
        return {"olay_tipi_istatistik": {}, "basari_oranlari": {}, "sik_kavramlar": []}

    # Olay tipi istatistiği
    tip_sayaci = Counter(ev.get("olay_tipi", "bilinmiyor") for ev in events)

    # Başarı oranları
    sonuc_sayaci = Counter(ev.get("sonuc", "") for ev in events)
    toplam = sum(sonuc_sayaci.values())
    basari_oran = sonuc_sayaci.get("başarılı", 0) / max(toplam, 1)

    # Sık geçen kavramlar
    kelimeler = []
    for ev in events:
        ozet = ev.get("ozet", "")
        for w in ozet.lower().split():
            if len(w) > 4 and w.isalpha():
                kelimeler.append(w)
    sik_kelimeler = [w for w, c in Counter(kelimeler).most_common(10)]

    return {
        "toplam_olay": len(events),
        "olay_tipi_dagilimi": dict(tip_sayaci.most_common()),
        "basari_orani": round(basari_oran, 3),
        "sik_kelimeler": sik_kelimeler,
    }


def predict_outcome(action: str, context: Optional[Dict] = None) -> Dict:
    """Bir aksiyon için olasılık tahmini yap.
    
    Args:
        action: Yapılacak aksiyon (örn: "fiyat değiştir", "yeni workflow kur")
        context: Bağlam bilgisi (örn: {"token": 5.0, "acil": True})
    
    Returns:
        {'tahmin': str, 'olasilik': float, 'guven': float, 'analiz': str}
    """
    patterns = analyze_patterns()
    events = _load_episodic_all()

    # Geçmişte benzer aksiyonları ara
    action_keywords = action.lower().split()
    benzer_olaylar = []
    for ev in events:
        ozet = ev.get("ozet", "").lower()
        eslesme = sum(1 for k in action_keywords if k in ozet)
        if eslesme >= 1:  # En az 1 kelime eşleşmesi
            benzer_olaylar.append(ev)

    # Benzer olaylardan başarı oranı çıkar
    basari_sayisi = 0
    for ev in benzer_olaylar:
        sonuc = ev.get("sonuc", "").lower()
        if "başarı" in sonuc or "başarılı" in sonuc or "çalışıyor" in sonuc or "tamam" in sonuc:
            basari_sayisi += 1

    # Olasılık hesapla
    toplam_benzer = len(benzer_olaylar)
    if toplam_benzer >= 3:
        # İstatistiksel: yeterli veri var
        base_olasilik = basari_sayisi / toplam_benzer
        guven = min(0.9, 0.3 + (toplam_benzer - 3) * 0.1)
    elif toplam_benzer > 0:
        # Az veri: düşük güven
        base_olasilik = basari_sayisi / toplam_benzer
        guven = 0.2 + toplam_benzer * 0.1
    else:
        # Hiç benzer olay yok: genel başarı oranını kullan
        base_olasilik = patterns.get("basari_orani", 0.5)
        guven = 0.2

    # Bağlam düzeltmesi
    context_boost = 0.0
    if context:
        if context.get("acil"):
            context_boost -= 0.1  # Acil kararlar daha riskli
        if context.get("token", 0) > 3:
            context_boost += 0.05  # Bol token = daha rahat

    olasilik = max(0.1, min(0.95, base_olasilik + context_boost))

    # Analiz metni
    if toplam_benzer >= 3:
        analiz = (f"'{action}' için {toplam_benzer} benzer geçmiş olay bulundu. "
                  f"{basari_sayisi}/{toplam_benzer} başarılı.")
    elif toplam_benzer > 0:
        analiz = (f"'{action}' için sadece {toplam_benzer} benzer olay var. "
                  f"Düşük güvenli tahmin.")
    else:
        analiz = (f"'{action}' için hiç benzer geçmiş olay bulunamadı. "
                  f"Genel sistem başarı oranı kullanıldı: %{patterns.get('basari_orani', 0.5)*100:.0f}")

    if olasilik > 0.7:
        tahmin = f"Başarılı olma ihtimali yüksek"
    elif olasilik > 0.4:
        tahmin = f"Orta düzeyde başarı ihtimali"
    else:
        tahmin = f"Düşük başarı ihtimali, alternatif değerlendirilmeli"

    return {
        "action": action,
        "tahmin": tahmin,
        "olasilik": round(olasilik, 3),
        "guven": round(guven, 3),
        "benzer_olay_sayisi": toplam_benzer,
        "analiz": analiz,
        "timestamp": datetime.now(TZ).isoformat(),
    }


def simulate_with_mcts(action: str, context: Optional[Dict] = None,
                        simulations: int = 100) -> Dict:
    """MCTS genişletmesi: Monte Carlo simülasyonu ile tahmin.
    Her simülasyon, geçmiş veriye dayalı olasılıklarla bir 'oyun' oynar."""
    
    base = predict_outcome(action, context)
    base_olasilik = base["olasilik"]

    # Simülasyon
    basari_sayisi = 0
    for _ in range(simulations):
        # Her simülasyonda hafif varyasyon
        noise = random.gauss(0, 0.1)  # Normal dağılım gürültüsü
        sim_olasilik = max(0.05, min(0.95, base_olasilik + noise))
        if random.random() < sim_olasilik:
            basari_sayisi += 1

    sim_olasilik = basari_sayisi / simulations
    # Simülasyon güveni: daha fazla simülasyon = daha yüksek güven
    sim_guven = min(0.95, base["guven"] + simulations / 1000)

    # 1 hafta sonrası tahmini (basit: aynı olasılıkla haftalık başarı)
    haftalik_olasilik = sim_olasilik ** 7  # 7 gün üst üste başarı

    return {
        "action": action,
        "tahmin": base["tahmin"],
        "simulasyon_sonucu": round(sim_olasilik, 3),
        "haftalik_olasilik": round(haftalik_olasilik, 3),
        "guven": round(sim_guven, 3),
        "simulasyon_sayisi": simulations,
        "benzer_olay_sayisi": base["benzer_olay_sayisi"],
        "analiz": (f"MCTS simülasyonu ({simulations} tekrar): "
                   f"%{sim_olasilik*100:.0f} başarı olasılığı. "
                   f"1 hafta sürdürülebilirlik: %{haftalik_olasilik*100:.0f}"),
        "timestamp": datetime.now(TZ).isoformat(),
    }


def early_warning(system_metrics: Optional[Dict] = None) -> Optional[str]:
    """Sistem metriklerinden erken uyarı üret.
    reality_check ve auto_tuner verilerini kullanır.
    
    Args:
        system_metrics: {
            'ram_kullanim': float (0-1),
            'disk_kullanim': float (0-1),
            'token_kalan': float,
            'cron_basarisizlik': float (0-1),
            'uptime_gun': int
        }
    Returns:
        Uyarı mesajı veya None
    """
    if not system_metrics:
        return None

    uyarilar = []

    # RAM anomalisi
    ram = system_metrics.get("ram_kullanim", 0)
    if ram > 0.9:
        uyarilar.append(f"🚨 KRİTİK: RAM %{ram*100:.0f} — 30 dk içinde OOM riski yüksek")
    elif ram > 0.8:
        uyarilar.append(f"⚠️ RAM %{ram*100:.0f} — 1 saat içinde kritik seviyeye ulaşabilir")

    # Disk anomalisi
    disk = system_metrics.get("disk_kullanim", 0)
    if disk > 0.95:
        uyarilar.append(f"🚨 KRİTİK: Disk %{disk*100:.0f} — yazma hatası yakın")
    elif disk > 0.85:
        uyarilar.append(f"⚠️ Disk %{disk*100:.0f} — 1 gün içinde dolabilir")

    # Token azalması
    token = system_metrics.get("token_kalan", 5)
    if token < 0.5:
        uyarilar.append(f"🚨 Token: ${token:.2f} — 1 saat içinde tükenme riski")
    elif token < 1:
        uyarilar.append(f"⚠️ Token: ${token:.2f} — 2 saat içinde bitebilir")

    # Cron başarısızlık
    cron_fail = system_metrics.get("cron_basarisizlik", 0)
    if cron_fail > 0.3:
        uyarilar.append(f"⚠️ Cron başarısızlık: %{cron_fail*100:.0f} — sistem bakımı gerek")

    if not uyarilar:
        return None

    return "\n".join(uyarilar)


def log_decision_prediction(action: str, prediction: Dict,
                            actual_result: Optional[str] = None) -> None:
    """Tahmin edilen kararı log'a kaydet (doğruluk ölçümü için)."""
    entries = _load_decision_log()
    entries.append({
        "timestamp": datetime.now(TZ).isoformat(),
        "action": action,
        "prediction": prediction,
        "actual_result": actual_result,
        "validated": actual_result is not None,
    })
    _save_decision_log(entries)


def validate_predictions() -> Dict:
    """Geçmiş tahminlerin doğruluğunu ölç.
    
    Returns:
        {'toplam': N, 'dogru': N, 'yanlis': N, 'dogruluk': float}
    """
    entries = _load_decision_log()
    validated = [e for e in entries if e.get("validated")]
    if not validated:
        return {"toplam": 0, "dogru": 0, "yanlis": 0, "dogruluk": 0.0}
    
    dogru = sum(1 for e in validated if _prediction_was_correct(e))
    return {
        "toplam": len(validated),
        "dogru": dogru,
        "yanlis": len(validated) - dogru,
        "dogruluk": round(dogru / len(validated), 3),
    }


def _prediction_was_correct(entry: Dict) -> bool:
    """Bir tahmin kaydının doğru olup olmadığını kontrol et."""
    pred = entry.get("prediction", {})
    actual = entry.get("actual_result", "")
    if not pred or not actual:
        return False
    # Basit kontrol: tahmin olasılığı >0.5 ve sonuç "başarılı" ise
    olasilik = pred.get("olasilik", 0)
    if olasilik > 0.5 and "başarı" in actual.lower():
        return True
    if olasilik <= 0.5 and "başarı" not in actual.lower():
        return True
    return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "patterns":
        p = analyze_patterns()
        print(f"Toplam olay: {p['toplam_olay']}")
        print(f"Başarı oranı: %{p['basari_orani']*100:.1f}")
        print(f"Sık kavramlar: {', '.join(p['sik_kelimeler'][:5])}")
    
    elif len(sys.argv) > 1 and sys.argv[1] == "predict" and len(sys.argv) > 2:
        action = " ".join(sys.argv[2:])
        result = simulate_with_mcts(action)
        print(f"Action: {result['action']}")
        print(f"Tahmin: {result['tahmin']}")
        print(f"Olasılık: %{result['simulasyon_sonucu']*100:.0f}")
        print(f"Güven: %{result['guven']*100:.0f}")
        print(f"1 hafta: %{result['haftalik_olasilik']*100:.0f}")
        print(f"Analiz: {result['analiz']}")
    
    elif len(sys.argv) > 1 and sys.argv[1] == "validate":
        v = validate_predictions()
        print(f"Doğruluk: {v['dogru']}/{v['toplam']} = %{v['dogruluk']*100:.0f}")
    
    else:
        print("Kullanım:")
        print("  patterns              — Geçmiş örüntüleri analiz et")
        print("  predict <action>      — Bir aksiyon için tahmin yap")
        print("  validate              — Tahmin doğruluğunu ölç")
