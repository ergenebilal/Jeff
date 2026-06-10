#!/usr/bin/env python3
"""Robot Bridge — robotik işletim sistemi köprüsü (simülasyon).
ROS benzeri bir API ile sanal robota komut gönderir ve durum alır."""

import json
import os
import random
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

ROBOT_STATE_PATH = os.path.expanduser("~/.hermes/brain/robot_state.json")
ROBOT_LOG_PATH = os.path.expanduser("~/.hermes/robot_console.log")
TZ = timezone(timedelta(hours=3))

# Sanal robot konfigürasyonu
VIRTUAL_ROBOT_CONFIG = {
    "name": "ErgeneBot-1",
    "sensors": ["kamera", "mikrofon", "mesafe", "imu"],
    "actuators": ["tekerlek", "kol"],
    "max_hiz": 1.0,  # m/s
    "pil_kapasite": 100.0,  # %
}


def _get_default_state() -> Dict:
    """Sanal robotun varsayılan durumu."""
    return {
        "robot_adi": VIRTUAL_ROBOT_CONFIG["name"],
        "aktif": True,
        "konum": {"x": 0.0, "y": 0.0, "theta": 0.0},
        "hiz": 0.0,
        "pil": 100.0,
        "son_komut": None,
        "son_komut_zamani": None,
        "sensor_verileri": {},
        "durum_mesaji": "Beklemede",
        "timestamp": datetime.now(TZ).isoformat(),
    }


def _load_robot_state() -> Dict:
    """Robot durumunu yükle."""
    if os.path.exists(ROBOT_STATE_PATH):
        try:
            with open(ROBOT_STATE_PATH) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    state = _get_default_state()
    _save_robot_state(state)
    return state


def _save_robot_state(state: Dict) -> None:
    """Robot durumunu kaydet."""
    os.makedirs(os.path.dirname(ROBOT_STATE_PATH), exist_ok=True)
    state["timestamp"] = datetime.now(TZ).isoformat()
    with open(ROBOT_STATE_PATH, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def _log(message: str) -> None:
    """Robot konsoluna log yaz."""
    ts = datetime.now(TZ).isoformat()
    with open(ROBOT_LOG_PATH, "a") as f:
        f.write(f"[{ts}] {message}\n")


def get_status() -> Dict:
    """Robotun mevcut durumunu döndür."""
    return _load_robot_state()


def send_command(komut: str, parametreler: Optional[Dict] = None) -> Dict:
    """Robota komut gönder.
    
    Desteklenen komutlar:
        "ilerle" — ileri git
        "dur" — dur
        "geri" — geri git
        "saga_don" — sağa dön
        "sola_don" — sola dön
        "kameraya_bak" — kamerayı yönlendir
        "bekle" — bekle
    
    Returns:
        {'komut': ..., 'sonuc': ..., 'yeni_durum': {...}}
    """
    state = _load_robot_state()
    
    if not state.get("aktif"):
        return {"komut": komut, "sonuc": "hata", "mesaj": "Robot aktif değil"}
    
    params = parametreler or {}
    previous_pos = dict(state["konum"])
    
    basarili = True
    mesaj = ""
    
    if komut == "ilerle":
        hiz = params.get("hiz", 0.5)
        state["hiz"] = min(hiz, VIRTUAL_ROBOT_CONFIG["max_hiz"])
        state["konum"]["x"] += state["hiz"] * random.uniform(0.8, 1.2)
        state["konum"]["y"] += state["hiz"] * random.uniform(-0.1, 0.1)
        state["durum_mesaji"] = f"İlerliyor ({state['hiz']:.1f} m/s)"
        mesaj = f"İlerliyor: ({previous_pos['x']:.1f}, {previous_pos['y']:.1f}) → ({state['konum']['x']:.1f}, {state['konum']['y']:.1f})"
    
    elif komut == "dur":
        state["hiz"] = 0.0
        state["durum_mesaji"] = "Durdu"
        mesaj = "Robot durdu"
    
    elif komut == "geri":
        hiz = params.get("hiz", 0.3)
        state["hiz"] = -min(hiz, VIRTUAL_ROBOT_CONFIG["max_hiz"])
        state["konum"]["x"] += state["hiz"] * random.uniform(0.8, 1.2)
        state["durum_mesaji"] = f"Geri gidiyor ({abs(state['hiz']):.1f} m/s)"
        mesaj = f"Geri gidiyor: ({previous_pos['x']:.1f}, {previous_pos['y']:.1f}) → ({state['konum']['x']:.1f}, {state['konum']['y']:.1f})"
    
    elif komut == "saga_don":
        aci = params.get("aci", 45)
        state["konum"]["theta"] = (state["konum"]["theta"] + aci) % 360
        state["durum_mesaji"] = f"{aci}° sağa döndü"
        mesaj = f"Sağa dönüş: {aci}°"
    
    elif komut == "sola_don":
        aci = params.get("aci", 45)
        state["konum"]["theta"] = (state["konum"]["theta"] - aci) % 360
        state["durum_mesaji"] = f"{aci}° sola döndü"
        mesaj = f"Sola dönüş: {aci}°"
    
    elif komut == "kameraya_bak":
        hedef = params.get("hedef", "ön")
        state["sensor_verileri"]["kamera_yonu"] = hedef
        state["durum_mesaji"] = f"Kamera {hedef} yönünde"
        mesaj = f"Kamera {hedef} yönüne çevrildi"
    
    elif komut == "bekle":
        sure = params.get("sure", 5)
        state["hiz"] = 0.0
        state["durum_mesaji"] = f"Bekliyor ({sure}s)"
        mesaj = f"{sure} saniye bekliyor"
    
    else:
        basarili = False
        mesaj = f"Bilinmeyen komut: '{komut}'"
    
    # Pil tüketimi
    state["pil"] = max(0, state["pil"] - random.uniform(0.1, 0.5))
    
    # Log
    if basarili:
        _log(f"KOMUT: {komut} {params} → {mesaj}")
    else:
        _log(f"HATA: {mesaj}")
    
    state["son_komut"] = komut
    state["son_komut_zamani"] = datetime.now(TZ).isoformat()
    _save_robot_state(state)
    
    # Episodic memory'ye kaydet (opsiyonel)
    try:
        sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))
        from episodic_memory import kaydet
        kaydet("robot", f"Robot {komut}: {mesaj}", 
               "başarılı" if basarili else "başarısız")
    except (ImportError, Exception):
        pass
    
    return {
        "komut": komut,
        "sonuc": "başarılı" if basarili else "hata",
        "mesaj": mesaj,
        "yeni_konum": dict(state["konum"]),
        "pil": round(state["pil"], 1),
    }


def simulate_sensor(duygu_tipi: str) -> Dict:
    """Sanal sensör verisi üret.
    
    Args:
        duygu_tipi: "kamera", "mesafe", "mikrofon"
    
    Returns:
        Sensör verisi
    """
    state = _load_robot_state()
    
    if duygu_tipi == "kamera":
        # Sanal kamera: önünde bir engel var mı?
        engel_var = random.random() < 0.3
        return {
            "tip": "kamera",
            "goruntu": "simule_edilmis",
            "engel_tespiti": engel_var,
            "engel_mesafe": round(random.uniform(0.5, 5.0), 2) if engel_var else None,
            "nesne_sayisi": random.randint(0, 5),
            "konum": dict(state["konum"]),
        }
    
    elif duygu_tipi == "mesafe":
        return {
            "tip": "mesafe",
            "on": round(random.uniform(0.3, 8.0), 2),
            "arka": round(random.uniform(0.3, 8.0), 2),
            "sag": round(random.uniform(0.3, 8.0), 2),
            "sol": round(random.uniform(0.3, 8.0), 2),
        }
    
    elif duygu_tipi == "mikrofon":
        ses_seviye = random.uniform(0, 100)
        return {
            "tip": "mikrofon",
            "ses_seviye": round(ses_seviye, 1),
            "ses_var": ses_seviye > 20,
            "ses_tanima": "bilinmeyen" if random.random() < 0.7 else "insan sesi",
        }
    
    return {"tip": duygu_tipi, "hata": "bilinmeyen sensör"}


def process_sensor_data(veri: Dict) -> Dict:
    """Sensör verisini işle ve anlamlı çıktı üret.
    
    reality_check motorunu kullanarak veriyi doğrula.
    
    Returns:
        {'anlam': str, 'kritik': bool, 'ham_veri': ...}
    """
    tip = veri.get("tip", "")
    kritik = False
    anlam = ""
    
    if tip == "kamera":
        if veri.get("engel_tespiti"):
            kritik = True
            anlam = (f"Önde engel tespit edildi! "
                     f"Mesafe: {veri['engel_mesafe']}m. Konum: ({veri['konum']['x']:.1f}, {veri['konum']['y']:.1f})")
        else:
            anlam = f"Ön görüş açık. {veri.get('nesne_sayisi', 0)} nesne görünür."
    
    elif tip == "mesafe":
        mesafeler = {k: v for k, v in veri.items() if k != "tip"}
        en_yakin = min(mesafeler.values())
        if en_yakin < 0.5:
            kritik = True
            anlam = f"Çarpışma tehlikesi! En yakın nesne {en_yakin}m."
        elif en_yakin < 1.5:
            anlam = f"Yakın mesafe uyarısı: {en_yakin}m."
        else:
            anlam = f"Etraf açık. En yakın: {en_yakin}m."
    
    elif tip == "mikrofon":
        if veri.get("ses_var"):
            anlam = f"Ses algılandı ({veri['ses_seviye']}dB). Tanıma: {veri.get('ses_tanima', '?')}"
        else:
            anlam = "Sessiz ortam."
    
    else:
        anlam = "Tanınmayan sensör verisi."
    
    state = _load_robot_state()
    state["sensor_verileri"][tip] = veri
    _save_robot_state(state)
    
    return {
        "anlam": anlam,
        "kritik": kritik,
        "ham_veri": veri,
    }


# Test: import için
import sys


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        s = get_status()
        print(f"Robot: {s['robot_adi']}")
        print(f"Konum: ({s['konum']['x']:.1f}, {s['konum']['y']:.1f}), Yön: {s['konum']['theta']}°")
        print(f"Pil: %{s['pil']:.0f} | Hız: {s['hiz']:.1f}")
        print(f"Durum: {s['durum_mesaji']}")
    
    elif len(sys.argv) > 2 and sys.argv[1] == "komut":
        r = send_command(sys.argv[2])
        print(f"{r['sonuc'].upper()}: {r['mesaj']}")
    
    elif len(sys.argv) > 2 and sys.argv[1] == "sensor":
        r = process_sensor_data(simulate_sensor(sys.argv[2]))
        print(f"{'🚨' if r['kritik'] else 'ℹ️'} {r['anlam']}")
    
    else:
        print("Kullanım:")
        print("  status              — Robot durumu")
        print("  komut <cmd>         — Komut gönder")
        print("  sensor <tip>        — Sensör simülasyonu (kamera/mesafe/mikrofon)")
