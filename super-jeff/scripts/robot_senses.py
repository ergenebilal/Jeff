#!/usr/bin/env python3
"""Robot Senses — sanal robot duyusal algılama modülü.
Sensör verilerini işler, consciousness_stream'a besler."""

import json
import os
import sys
from typing import Dict, Optional

SENSES_LOG_PATH = os.path.expanduser("~/.hermes/robot_senses.log")


def _log(entry: Dict) -> None:
    """Duyusal veriyi log'a kaydet."""
    os.makedirs(os.path.dirname(SENSES_LOG_PATH), exist_ok=True)
    with open(SENSES_LOG_PATH, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def perceive_environment() -> Dict:
    """Çevreyi tüm sensörlerle algıla.
    
    Returns:
        {'kamera': ..., 'mesafe': ..., 'mikrofon': ..., 'ozet': str}
    """
    from robot_bridge import simulate_sensor, process_sensor_data
    
    kamera = process_sensor_data(simulate_sensor("kamera"))
    mesafe = process_sensor_data(simulate_sensor("mesafe"))
    mikrofon = process_sensor_data(simulate_sensor("mikrofon"))
    
    # Özet çıkar
    kritik_durumlar = []
    for kaynak, veri in [("kamera", kamera), ("mesafe", mesafe), ("mikrofon", mikrofon)]:
        if veri.get("kritik"):
            kritik_durumlar.append(f"{kaynak}: {veri['anlam']}")
    
    if kritik_durumlar:
        ozet = "KRİTİK: " + " | ".join(kritik_durumlar)
    else:
        ozet = f"Normal: {kamera['anlam']} {mesafe['anlam']} {mikrofon['anlam']}"
    
    result = {
        "kamera": kamera,
        "mesafe": mesafe,
        "mikrofon": mikrofon,
        "ozet": ozet,
        "kritik_var": len(kritik_durumlar) > 0,
    }
    
    _log(result)
    return result


def analyze_scene(gorsel_veri: Dict) -> Dict:
    """Görsel veriyi reality_check ile doğrula ve anlamlandır.
    
    Args:
        gorsel_veri: Kamera sensöründen gelen veri
    
    Returns:
        {'nesne_var_mi': bool, 'nesne_turu': str, 'guven': float}
    """
    # Simülasyon: görüntüdeki nesneleri analiz et
    engel = gorsel_veri.get("ham_veri", {}).get("engel_tespiti", False)
    mesafe = gorsel_veri.get("ham_veri", {}).get("engel_mesafe")
    
    if engel and mesafe:
        if mesafe < 1.0:
            return {
                "nesne_var_mi": True,
                "nesne_turu": "engel (yakın)",
                "guven": 0.85,
                "aksiyon": "dur",
            }
        else:
            return {
                "nesne_var_mi": True,
                "nesne_turu": "engel (uzak)",
                "guven": 0.70,
                "aksiyon": "yavasla",
            }
    
    return {
        "nesne_var_mi": False,
        "nesne_turu": "yok",
        "guven": 0.90,
        "aksiyon": "ilerle",
    }


def decide_action(cevre: Dict) -> str:
    """Çevre algısına göre aksiyon kararı üret.
    
    decision_engine ile entegre: kritik durumda hemen karar ver.
    
    Returns:
        Komut stringi: "dur", "ilerle", "yavasla", "bekle"
    """
    if cevre.get("kritik_var"):
        return "dur"
    
    # Kamera analizi
    kamera = cevre.get("kamera", {})
    scene = analyze_scene(kamera)
    return scene.get("aksiyon", "ilerle")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "perceive":
        env = perceive_environment()
        print(env["ozet"])
        print(f"Önerilen aksiyon: {decide_action(env)}")
    
    else:
        print("Kullanım: perceive")
