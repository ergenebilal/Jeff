#!/usr/bin/env python3
"""Test: Predictive Engine — 9+ testle doğruluk ölçümü."""
import sys
import os
sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))

from predictive_engine import (
    analyze_patterns, predict_outcome, simulate_with_mcts,
    early_warning, log_decision_prediction, validate_predictions
)

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

# Test 1: analyze_patterns çalışıyor
patterns = analyze_patterns()
test("analyze_patterns dict döndürüyor", isinstance(patterns, dict))
test("toplam_olay >= 0", patterns.get("toplam_olay", -1) >= 0)
test("basari_orani 0-1 arası", 0 <= patterns.get("basari_orani", -1) <= 1)

# Test 2: predict_outcome çalışıyor
pred = predict_outcome("yeni workflow kur")
test("predict_outcome dict döndürüyor", isinstance(pred, dict))
test("tahmin var", "tahmin" in pred)
test("olasilik 0-1 arası", 0 <= pred.get("olasilik", -1) <= 1)
test("guven 0-1 arası", 0 <= pred.get("guven", -1) <= 1)

# Test 3: predict_outcome context ile
pred_ctx = predict_outcome("test", {"acil": True, "token": 4.0})
test("predict_outcome context ile çalışıyor", "olasilik" in pred_ctx)

# Test 4: simulate_with_mcts çalışıyor
sim = simulate_with_mcts("yeni workflow kur", simulations=50)
test("simulate_with_mcts dict döndürüyor", isinstance(sim, dict))
test("simulasyon_sonucu 0-1 arası", 0 <= sim.get("simulasyon_sonucu", -1) <= 1)
test("haftalik_olasilik 0-1 arası", 0 <= sim.get("haftalik_olasilik", -1) <= 1)
test("guven 0-1 arası", 0 <= sim.get("guven", -1) <= 1)

# Test 5: simulate_with_mcts yüksek simülasyon
sim2 = simulate_with_mcts("test", simulations=200)
test("200 simülasyon çalışıyor", sim2.get("simulasyon_sayisi") == 200)

# Test 6: early_warning çalışıyor
# Kritik metrikler uyarı üretmeli
uyari = early_warning({"ram_kullanim": 0.95, "disk_kullanim": 0.5, "token_kalan": 4.0, "cron_basarisizlik": 0.1})
test("early_warning kritik RAM'de uyarı üretiyor", uyari is not None and "KRİTİK" in uyari)

# Normal metrikler uyarı üretmemeli
uyari2 = early_warning({"ram_kullanim": 0.5, "disk_kullanim": 0.5, "token_kalan": 4.0, "cron_basarisizlik": 0.0})
test("early_warning normal metriklerde None döndürüyor", uyari2 is None)

# Test 7: Token azalması uyarısı
uyari3 = early_warning({"ram_kullanim": 0.5, "disk_kullanim": 0.5, "token_kalan": 0.3, "cron_basarisizlik": 0.0})
test("early_warning token kritik uyarıyor", uyari3 is not None and "TOKEN" in uyari3.upper())

# Test 8: log_decision_prediction çalışıyor
log_decision_prediction("test_action", {"olasilik": 0.8}, "başarılı")
test("log_decision_prediction çalışıyor", True)

# Test 9: validate_predictions çalışıyor
val = validate_predictions()
test("validate_predictions dict döndürüyor", isinstance(val, dict))
test("toplam >= 0", val.get("toplam", -1) >= 0)

# Test 10: Farklı aksiyonlar predict edilebiliyor
for a in ["fiyat değiştir", "yeni özellik ekle", "sistemi güncelle", "hata düzelt"]:
    p = predict_outcome(a)
    test(f"predict: '{a[:15]}...' çalışıyor", "tahmin" in p)

print(f"\n📊 SONUÇ: {passed}/{passed + failed} PASS", end="")
if failed:
    print(f", {failed} FAILED ❌")
    sys.exit(1)
else:
    print(" ✅")
