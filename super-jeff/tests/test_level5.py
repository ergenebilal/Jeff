#!/usr/bin/env python3
"""Test: Level 5 — Yaratıcılık Motoru
12 test: creativity_engine + reverse_thinker
"""

import sys
import os
sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))

from creativity_engine import generate_ideas, generate_marketing_strategy, generate_workflow_idea
from reverse_thinker import reverse_simulate, pre_mortem_analysis

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


print("🧪 TEST: Level 5 — Yaratıcılık Motoru\n")

# === creativity_engine ===
print("💡 creativity_engine.py:")

# 1. Fikir üretme (varsayılan: 3 fikir)
ideas = generate_ideas(count=3)
test("3 fikir üretildi", len(ideas) == 3)
test("Her fikirde isim var", all(i.get("isim") for i in ideas))
test("Her fikirde konsept var", all(i.get("konsept") for i in ideas))
test("Her fikirde puan var", all(i.get("puan", 0) > 0 for i in ideas))
test("Her fikirde timestamp var", all(i.get("timestamp") for i in ideas))

# 2. Domain filtresi
domain_ideas = generate_ideas(domain="tech", count=2)
test("Domain filtresi ile 2 fikir", len(domain_ideas) == 2)

# 3. Pazarlama stratejisi
strat = generate_marketing_strategy()
test("Pazarlama stratejisi üretildi", strat is not None)
test("Aktif projeler listesi var", len(strat.get("aktif_projeler", [])) > 0)
test("Stratejiler listesi var", len(strat.get("stratejiler", [])) > 0)

# 4. İş akışı fikri
wf = generate_workflow_idea()
test("İş akışı fikri üretildi", wf is not None)
test("İş akışı adı var", len(wf.get("isim", "")) > 5)
test("İş akışı adımları var", len(wf.get("adimlar", [])) > 0)
test("Tahmini süre > 0", wf.get("tahmini_sure_saat", 0) > 0)

# === reverse_thinker ===
print("\n🔄 reverse_thinker.py:")

# 5. Ters simülasyon
rev = reverse_simulate("Gumroad satışlarını artırmak")
test("Ters simülasyon sonucu var", rev is not None)
test("Hedef adı doğru", "Gumroad" in rev.get("hedef", ""))
test("Kritik uyarı sayısı > 0", rev.get("kritik_risk_sayisi", 0) > 0)
test("En az 2 risk tespiti", len(rev.get("tum_riskler", [])) >= 2)
test("Analiz metni var", len(rev.get("analiz", "")) > 20)

# 6. Pre-mortem
pm = pre_mortem_analysis("Twitter bot")
test("Pre-mortem sonucu var", pm is not None)
test("Proje adı doğru", pm.get("proje") == "Twitter bot")
test("Başarısızlık sebepleri var", len(pm.get("sebepler", [])) > 0)
test("Tavsiyeler var", len(pm.get("tavsiyeler", [])) > 0)

print(f"\n📊 SONUÇ: {TEST_PASS}/{TEST_TOTAL} PASS {'✅' if TEST_FAIL == 0 else '❌'}")
if TEST_FAIL > 0:
    print(f"  BAŞARISIZ: {TEST_FAIL}")
    sys.exit(1)
