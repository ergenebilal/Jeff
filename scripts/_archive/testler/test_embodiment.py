#!/usr/bin/env python3
"""Test: Embodiment — robot + duygu + bilinç + karar entegrasyonu.
Senaryo: Sanal robot ilerler, engel görür, durur."""

import sys
import os
sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))

from robot_bridge import (
    send_command, get_status, simulate_sensor, process_sensor_data
)
from robot_senses import perceive_environment, analyze_scene, decide_action

passed = 0
failed = 0

def test(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✅ {name}")
    else:
        failed += 1
        print(f"  ❌ {name}")

# === SENARYO: Robot engel görür ve durur ===

# Önce robot durumunu sıfırla
from robot_bridge import _get_default_state, _save_robot_state
_save_robot_state(_get_default_state())

# 1. Robot başlangıç durumu
status = get_status()
test("Robot aktif", status.get("aktif"))
test("Başlangıç konumu (0,0)", abs(status["konum"]["x"]) < 0.1 and abs(status["konum"]["y"]) < 0.1)
test("Pil 100%", status["pil"] > 90)

# 2. Robot ilerlesin
r1 = send_command("ilerle", {"hiz": 0.8})
test("İlerle komutu başarılı", r1["sonuc"] == "başarılı")
test("İlerle sonrası x değişti", r1["yeni_konum"]["x"] > 0)

# 3. Kamera sensöründen engel tespiti
kamera_verisi = process_sensor_data({
    "tip": "kamera",
    "goruntu": "simule_edilmis",
    "engel_tespiti": True,
    "engel_mesafe": 0.8,
    "nesne_sayisi": 1,
    "konum": {"x": 2.5, "y": 0.0},
})
test("Kamera engel tespit etti", kamera_verisi["kritik"])
test("Engel mesafe bilgisi var", "0.8" in kamera_verisi.get("anlam", ""))

# 4. Mesafe sensörü
mesafe_verisi = process_sensor_data({
    "tip": "mesafe",
    "on": 0.3, "arka": 3.0, "sag": 2.0, "sol": 1.5,
})
test("Mesafe sensörü yakın mesafeyi tespit etti", mesafe_verisi["kritik"])
test("En yakın yön 'on'", "0.3" in mesafe_verisi.get("anlam", ""))

# 5. Görsel analiz
scene = analyze_scene(kamera_verisi)
test("analyze_scene nesne_var_mi True", scene.get("nesne_var_mi"))
test("analyze_scene aksiyon 'dur'", scene.get("aksiyon") == "dur")

# 6. Çevre algısı
cevre = perceive_environment()
test("perceive_environment ozet içeriyor", len(cevre.get("ozet", "")) > 10)
test("perceive_environment kritik_var bool",
     isinstance(cevre.get("kritik_var"), bool))

# 7. Karar mekanizması
karar = decide_action({"kritik_var": True, "kamera": kamera_verisi})
test("Kritik durumda karar 'dur'", karar == "dur")

karar2 = decide_action({"kritik_var": False, "kamera": {
    "ham_veri": {"engel_tespiti": False}}})
test("Normal durumda karar 'ilerle'", karar2 == "ilerle" or karar2 == "yavasla")

# 8. Robot durma komutu
r2 = send_command("dur")
test("Dur komutu başarılı", r2["sonuc"] == "başarılı")
test("Durduktan sonra hiz 0", "durdu" in r2.get("mesaj", "").lower())

# 9. Robot sola dönüş
r3 = send_command("sola_don", {"aci": 90})
test("Sola dönüş başarılı", r3["sonuc"] == "başarılı")
yeni_aci = r3["yeni_konum"]["theta"]
test(f"Yön değişti: {yeni_aci}°", yeni_aci != 0)

# 10. Kameraya bak komutu
r4 = send_command("kameraya_bak", {"hedef": "sol"})
test("Kamera yönlendirme başarılı", r4["sonuc"] == "başarılı")

# 11. Bilinmeyen komut
r5 = send_command("uc")
test("Bilinmeyen komut hata döndürür", r5["sonuc"] == "hata")

# 12. simulate_sensor tüm tipler
for tip in ["kamera", "mesafe", "mikrofon"]:
    v = simulate_sensor(tip)
    test(f"Sensör '{tip}' çalışıyor", v.get("tip") == tip)

# 13. Nihai durum kontrolü
son = get_status()
test("Nihai konum x > 0", son["konum"]["x"] > 0)
test("Nihai pil azaldı", son["pil"] < 100)

# 14. Robot log dosyası oluştu
test("Robot log dosyası var", os.path.exists(os.path.expanduser("~/.hermes/robot_console.log")))

# 15. Robot state dosyası güncellendi
state_path = os.path.expanduser("~/.hermes/brain/robot_state.json")
test("Robot state dosyası güncellendi", os.path.exists(state_path))
if os.path.exists(state_path):
    import json
    with open(state_path) as f:
        s = json.load(f)
    test("State dosyası geçerli JSON", isinstance(s, dict))
    test("State konum kaydedilmiş", "konum" in s)
    test("State pil kaydedilmiş", "pil" in s)

print(f"\n📊 SONUÇ: {passed}/{passed + failed} PASS", end="")
if failed:
    print(f", {failed} FAILED ❌")
    sys.exit(1)
else:
    print(" ✅")
