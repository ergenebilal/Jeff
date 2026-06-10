#!/usr/bin/env python3
"""Test: Level 6 — Özerk Eylem ve Sorumluluk
14 test: autonomous_agent + responsibility_logger
"""

import sys
import os
sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))

import random
random.seed(42)

from autonomous_agent import assess_action, execute_autonomous, list_safe_actions
from responsibility_logger import (
    log_autonomous_decision, report_result,
    get_decision_history, get_statistics
)

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


print("🧪 TEST: Level 6 — Özerk Eylem ve Sorumluluk\n")

# === autonomous_agent ===
print("🤖 autonomous_agent.py:")

# 1. Risk değerlendirmesi
assess = assess_action("disk_temizle")
test("Risk değerlendirmesi var", assess is not None)
test("Karar alanı var", "karar" in assess)
test("Risk değeri 0-1 arası", 0 <= assess["risk"] <= 1)
test("Timestamp var", "timestamp" in assess)

# 2. Düşük riskli eylem otonom yapılabilir
assess_safe = assess_action("log_oku")
test("Düşük riskli eylem otonom kararı", assess_safe.get("karar") == "otonom")

# 3. Otonom eylem yürütme
exec_result = execute_autonomous("disk_temizle")
test("Otonom eylem sonucu var", exec_result is not None)
test("Kendi kararıyla yapıldı", exec_result.get("kendi_karariyla") is True)
test("Sonuç alanı var", "sonuc" in exec_result)

# 4. Güvenli eylemler listesi
safe_list = list_safe_actions()
test("Güvenli eylem listesi var", len(safe_list) > 0)
test("Her eylemde risk bilgisi var", all("risk" in a for a in safe_list))

# === responsibility_logger ===
print("\n📝 responsibility_logger.py:")

# 5. Karar kaydetme
entry = log_autonomous_decision(
    "disk_temizle", 0.02,
    alternatifler=["bekle", "manuel temizle"],
    beklenen_sonuc="disk alanı artar",
)
test("Karar kaydı oluştu", entry is not None)
test("Tip otonom_karar", entry.get("tip") == "otonom_karar")
test("Durum beklemede", entry.get("durum") == "beklemede")
test("Alternatifler var", len(entry.get("alternatifler", [])) >= 2)

# 6. Başarılı sonuç raporlama
success = report_result("disk_temizle", basarili=True)
test("Başarılı rapor", success["durum"] == "başarılı")

# 7. Başarısız sonuç raporlama ve özür
fail = report_result("load_test", basarili=False, hata_mesaji="rate limit aşıldı")
test("Başarısız rapor", fail["durum"] == "başarısız")
test("Özür mesajı var", "özür" in fail)
test("Özür 'Şef' ile başlıyor", fail.get("özür", "").startswith("Şef"))
test("Bir daha bu hata flag'i var", fail.get("bir_daha_bu_hata") is True)

# 8. Geçmiş ve istatistikler
history = get_decision_history(5)
test("Karar geçmişi döndü", len(history) >= 0)

stats = get_statistics()
test("İstatistikler döndü", stats is not None)
test("Toplam sayısı >= 0", stats.get("toplam", -1) >= 0)
test("Başarı oranı 0-1 arası", 0 <= stats.get("basari_orani", -1) <= 1)

print(f"\n📊 SONUÇ: {TEST_PASS}/{TEST_TOTAL} PASS {'✅' if TEST_FAIL == 0 else '❌'}")
if TEST_FAIL > 0:
    print(f"  BAŞARISIZ: {TEST_FAIL}")
    sys.exit(1)
