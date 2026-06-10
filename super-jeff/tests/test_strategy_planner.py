#!/usr/bin/env python3
"""Test: Strategy Planner — plan oluşturma, sorgulama, güncelleme."""
import sys
import os
sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))

from strategy_planner import (
    create_plan, get_weekly_plan, update_progress, list_active_plans
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

# Test 1: create_plan Gumroad hedefiyle
plan = create_plan("Bu ay Gumroad'dan $500 kazan", deadline_days=30)
test("create_plan dict döndürüyor", isinstance(plan, dict))
test("plan_id var", "id" in plan)
test("hedef doğru", plan["hedef"] == "Bu ay Gumroad'dan $500 kazan")
test("gun_sayisi 30", plan["gun_sayisi"] == 30)

# Test 2: Haftalık planlar oluştu
weeks = plan.get("haftalik_plan", [])
test("haftalik_plan en az 4 hafta", len(weeks) >= 4)
test("Her haftada aksiyon var", all(len(h.get("aksiyonlar", [])) > 0 for h in weeks))

# Test 3: İlk hafta aksiyonları kritik mi
first_week = weeks[0]
kritik_sayisi = sum(1 for a in first_week["aksiyonlar"] if a.get("kritik"))
test("İlk haftada en az 1 kritik aksiyon", kritik_sayisi >= 1)

# Test 4: Farklı hedef türleri
plan_kod = create_plan("Yeni bir Python kütüphanesi yaz", deadline_days=21)
test("Kod hedefi planı oluşuyor", "id" in plan_kod)
test("Kod planı 3 hafta", len(plan_kod["haftalik_plan"]) == 3)

plan_social = create_plan("Instagram'da 1000 takipçi", deadline_days=28)
test("Sosyal medya planı oluşuyor", "id" in plan_social)

# Test 5: get_weekly_plan
weekly = get_weekly_plan()
test("get_weekly_plan dict veya None", weekly is None or isinstance(weekly, dict))
if weekly:
    test("weekly'de hedef var", "hedef" in weekly)
    test("weekly'de aksiyonlar var", "aksiyonlar" in weekly)

# Test 6: update_progress
p_id = plan["id"]
test("update_progress 50", update_progress(p_id, 50))
test("update_progress 100 (tamamla)", update_progress(p_id, 100))

# Test 7: Tamamlanan plan aktif değil
active = list_active_plans()
test("list_active_plans liste", isinstance(active, list))
# Tamamlanan plan listede olmamalı
for p in active:
    test("Aktif plan 100% değil", p.get("tamamlanma_yuzde", 0) < 100)

# Test 8: Varsayılan hedef
plan_default = create_plan("Genel bir hedef belirle", deadline_days=14)
test("Genel hedef planı 2 hafta", len(plan_default["haftalik_plan"]) == 2)
test("Her haftada aksiyon var genel planda",
     all(len(h.get("aksiyonlar", [])) > 0 for h in plan_default["haftalik_plan"]))

# Test 9: Hedef yüzdeleri sıralı
for plan in [plan, plan_kod, plan_social]:
    yuzdeler = [h["hedef_yuzde"] for h in plan["haftalik_plan"]]
    test(f"Yüzdeler artan sırada ({yuzdeler})",
         all(yuzdeler[i] <= yuzdeler[i+1] for i in range(len(yuzdeler)-1)))

print(f"\n📊 SONUÇ: {passed}/{passed + failed} PASS", end="")
if failed:
    print(f", {failed} FAILED ❌")
    sys.exit(1)
else:
    print(" ✅")
