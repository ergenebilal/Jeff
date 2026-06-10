#!/usr/bin/env python3
"""Test: Level 4 — Öğrenme Hızlandırıcı (Meta-Learning)
15 test: meta_learner + accelerated_learning
"""

import sys
import os
sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))

import random
random.seed(42)

from meta_learner import create_learning_plan, compare_learning_speed
from accelerated_learning import simulate_accelerated_learning, execute_plan

TEST_PASS = 0
TEST_FAIL = 0
TEST_TOTAL = 0


def test(name: str, condition: bool):
    global TEST_PASS, TEST_FAIL, TEST_TOTAL
    TEST_TOTAL += 1
    if condition:
        TEST_PASS += 1
        print(f"  ✅ {name}")
    else:
        TEST_FAIL += 1
        print(f"  ❌ {name}")


print("🧪 TEST: Level 4 — Öğrenme Hızlandırıcı\n")

# === meta_learner ===
print("📚 meta_learner.py:")

# 1. API skill planı oluştur
plan1 = create_learning_plan("Instagram API")
test("Instagram API planı oluştu", plan1 is not None)
test("Plan ID var", "plan_id" in plan1)
test("Adım sayısı > 5", len(plan1["adimlar"]) > 5)
test("Analiz var", "analiz" in plan1)
test("Tahmini süre > 0", plan1["tahmini_toplam_sure_dk"] > 0)
test("Adımlarda tamamlandi alanı var",
     all("tamamlandi" in a for a in plan1["adimlar"]))

# 2. Farklı skill türleri için plan
plan2 = create_learning_plan("Gumroad satış API")
test("Gumroad planı oluştu", plan2 is not None)
test("Gumroad spesifik adımlar var",
     any("API" in a["aciklama"] for a in plan2["adimlar"]))

plan3 = create_learning_plan("Twitter X API")
test("Twitter planı oluştu", plan3 is not None)
test("Twitter spesifik adımlar var",
     any("OAuth" in a["aciklama"] for a in plan3["adimlar"]))

# 3. Hız karşılaştırması
comp = compare_learning_speed("Instagram API")
test("Karşılaştırma sonucu var", comp is not None)
test("Kazanım yüzdesi hesaplanabiliyor", comp["kazanim_yuzde"] >= 0)
test("Eski süre > yeni süre (genelde)", comp["eski_sure_dk"] >= comp["yeni_sure_dk"])
test("Analiz metni var", len(comp["analiz"]) > 20)

# === accelerated_learning ===
print("\n🚀 accelerated_learning.py:")

# 4. Simülasyon
sim = simulate_accelerated_learning("Instagram API")
test("Simülasyon sonucu var", sim is not None)
test("Skill adı doğru", sim["skill"] == "Instagram API")
test("Kazanım yüzdesi > 0", sim["kazanim_yuzde"] > 0)
test("Yeni süre < eski süre", sim["yeni_sure_dk"] < sim["eski_sure_dk"])
test("Adım detayında basarili_adim var", sim["adim_detay"]["basarili_adim"] > 0)
test("Analiz metni var", len(sim["analiz"]) > 30)
test("Timestamp var", "timestamp" in sim)

# 5. Execute plan
exec_result = execute_plan("Test API", simulate=True)
test("Execute sonucu var", exec_result is not None)
test("Başarılı adım sayısı > 0", exec_result["basarili_adim"] > 0)
test("Başarı oranı bilgisi var", "basari_orani" in exec_result)
test("Simülasyon modu doğru", exec_result["simulate"] is True)

print(f"\n📊 SONUÇ: {TEST_PASS}/{TEST_TOTAL} PASS {'✅' if TEST_FAIL == 0 else '❌'}")
if TEST_FAIL > 0:
    print(f"  BAŞARISIZ: {TEST_FAIL}")
    sys.exit(1)
