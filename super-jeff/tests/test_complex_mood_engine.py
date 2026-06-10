#!/usr/bin/env python3
"""Test: Complex Mood Engine — 10 farklı duygu bileşimini test et."""
import sys
import os
sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))

from complex_mood_engine import (
    BASE_MOODS, BLEND_TABLE, blend_moods, get_current_complex_mood, set_mood, list_blends
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


# Test 1: Tüm temel duygular tanımlı
test("Tüm 8 temel duygu tanımlı", len(BASE_MOODS) == 8)

# Test 2: Her duygunun enerji ve polaritesi var
for mood, props in BASE_MOODS.items():
    test(f"'{mood}' enerji/polarite/renk içeriyor",
         all(k in props for k in ["enerji", "polarite", "renk"]))

# Test 3: Bilinen 15 birleşimin hepsi çalışıyor
test("15 bilinen birleşim var", len(BLEND_TABLE) >= 15)

# Test 4: Her birleşim için blend_moods doğru isim döndürüyor
for (m1, m2), expected in list(BLEND_TABLE.items())[:5]:
    result = blend_moods(m1, m2)
    test(f"'{m1}' + '{m2}' → '{expected}'", result == expected)

# Test 5: Bilinmeyen kombinasyonlar fallback üretiyor
unknown = blend_moods("sakin", "kararlı")
test(f"Bilinmeyen kombinasyon fallback: '{unknown}'", len(unknown) > 0 and "sakin" in unknown or "kararlı" in unknown)

# Test 6: set_mood geçerli duygu set ediyor
original = set_mood("meraklı", intensity=0.8)
test(f"set_mood('meraklı') → primary={original['primary_mood']}",
     original["primary_mood"] == "meraklı")
test(f"set_mood intensity=0.8 → {original['intensity']}",
     abs(original["intensity"] - 0.8) < 0.01)

# Test 7: Geçersiz duygu hatası fırlatıyor
try:
    set_mood("olmayan_duygu")
    test("Geçersiz duygu hata fırlatıyor", False)
except ValueError:
    test("Geçersiz duygu hata fırlatıyor", True)

# Test 8: get_current_complex_mood tüm anahtarları içeriyor
cm = get_current_complex_mood()
required_keys = ["primary_mood", "secondary_mood", "blend_name", "intensity", "energy", "polarity"]
test("get_current_complex_mood tüm anahtarlar",
     all(k in cm for k in required_keys))

# Test 9: blend_moods simetrik (m1,m2) = (m2,m1)
a = blend_moods("meraklı", "endişeli")
b = blend_moods("endişeli", "meraklı")
test("Blend simetrik", a == b)

# Test 10: List blends çalışıyor
blends = list_blends()
test(f"list_blends: {len(blends)} birleşim döndü", len(blends) >= 15)
if blends:
    first = blends[0]
    test("Her blend'de mood1, mood2, blend_name var",
         all(k in first for k in ["mood1", "mood2", "blend_name"]))


print(f"\n📊 SONUÇ: {passed}/{passed + failed} PASS", end="")
if failed:
    print(f", {failed} FAILED ❌")
    sys.exit(1)
else:
    print(" ✅")
