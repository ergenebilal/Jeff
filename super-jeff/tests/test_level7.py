#!/usr/bin/env python3
"""Test: Level 7 — Dil ve Anlam Derinliği
20 test: pragmatics_engine + humor_detector
"""

import sys
import os
sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))

from pragmatics_engine import infer_subtext, test_inferences
from humor_detector import detect_humor, test_humor_detection

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


print("🧪 TEST: Level 7 — Dil ve Anlam Derinliği\n")

# === pragmatics_engine ===
print("📖 pragmatics_engine.py:")

# 1. Alt metin analizi (10 farklı imalı cümle test edilecek)
t = test_inferences()
test("Test havuzu 10 cümle", t["toplam"] == 10)
test("10 cümleden 10'u doğru", t["dogru"] == 10)

# 2. Bireysel cümle testleri
r1 = infer_subtext("Şef, bu iş biraz karışık geldi bana")
test("Yardım isteme tespiti", r1["alt_metin"] == "yardım_isteme")
test("Alt metin analizinde guven var", "guven" in r1)
test("Alternatif yorum var", len(r1.get("alternatif_yorum", "")) > 5)

r2 = infer_subtext("Üç saattir cevap bekliyorum hâlâ")
test("Sitem tespiti", r2["alt_metin"] == "sitem")

r3 = infer_subtext("Bu raporu akşama kadar bitirelim sence?")
test("Onay bekleme tespiti", r3["alt_metin"] == "onay_bekleme")

r4 = infer_subtext("Bu kadar işin arasında kahve bile içemedim")
test("Normal cümle - doğrudan_ifade tespiti",
     r4["alt_metin"] in ("doğrudan_ifade", "memnuniyetsizlik"))

# === humor_detector ===
print("\n🎭 humor_detector.py:")

# 3. Mizah tespiti (5 farklı mizah türü)
h = test_humor_detection()
test("Mizah test havuzu 5 cümle", h["toplam"] == 5)
test("5 cümleden 5'i doğru", h["dogru"] == 5)

# 4. Bireysel mizah tespiti
h1 = detect_humor("Tabii ki yine her şey harika, API yine değişmiş")
test("İroni tespiti", h1["mizah_turu"] == "ironi")

h2 = detect_humor("Bravo, bir satır kod yazdın, tüm sistemi çökerttin")
test("Alay tespiti", h2["mizah_turu"] == "alay")

h3 = detect_humor("Bu iş hiç bitmeyecek, dünyanın en uzun projesi bu")
test("Abartı tespiti", h3["mizah_turu"] == "abarti")

h4 = detect_humor("Yazılımcılar ikiye ayrılır: test yazanlar ve test yazdığını sananlar")
test("Kelime oyunu tespiti", h4["mizah_turu"] == "kelime_oyunu")

h5 = detect_humor("Bugün hiçbir şey yapmadım, yarına erteledim. Yarın da yapmam")
test("Kuru mizah tespiti", h5["mizah_turu"] == "kuru_mizah")

# 5. Genel kontroller
test("Mizah tespitinde guven var", "guven" in h1)
test("Duygusal tepki var", len(h1.get("duygusal_tepki", "")) > 5)
test("Mood önerisi var", "mood_onerisi" in h1)

# 6. Mizah olmayan cümle
h6 = detect_humor("Merhaba, bugün hava güzel")
test("Mizah olmayan cümle - mizah_değil",
     h6["mizah_turu"] == "mizah_değil")

print(f"\n📊 SONUÇ: {TEST_PASS}/{TEST_TOTAL} PASS {'✅' if TEST_FAIL == 0 else '❌'}")
if TEST_FAIL > 0:
    print(f"  BAŞARISIZ: {TEST_FAIL}")
    sys.exit(1)
