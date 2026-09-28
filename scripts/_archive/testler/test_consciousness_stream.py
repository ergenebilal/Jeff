#!/usr/bin/env python3
"""Test: Consciousness Stream — 9 test, 9/9 PASS şart."""
import sys
import os
import json
sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))

from consciousness_stream import (
    _load_episodic, _load_semantic, _load_mood,
    _generate_insight, produce_insight, get_recent_insights
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

# Test 1: Episodic yükleme (son 1 saat) — en az 1 olay var mı?
events = _load_episodic(24)  # son 24 saat
test("_load_episodic >= 1 olay döndürüyor", len(events) >= 1)

# Test 2: Episodic olaylar geçerli formatta
if events:
    first = events[0]
    test("Episodic olay timestamp içeriyor", "timestamp" in first)
    test("Episodic olay ozet içeriyor", "ozet" in first)

# Test 3: Semantic yükleme
concepts = _load_semantic(["memory", "hafıza", "bellek"])
test("_load_semantic çalışıyor (en azından boş liste döndürebilir)",
     isinstance(concepts, list))

# Test 4: Mood yükleme
mood = _load_mood()
test("_load_mood primary_mood içeriyor", "primary_mood" in mood)
test("_load_mood blend_name veya mood içeriyor",
     "blend_name" in mood or "mood" in mood)

# Test 5: _generate_insight olaysız çalışıyor
insight_empty = _generate_insight([], [], mood)
test("_generate_insight olaysız string döndürüyor",
     isinstance(insight_empty, str) and len(insight_empty) > 10)

# Test 6: _generate_insight olaylı çalışıyor
sample_events = [{"timestamp": "2026-06-10T22:41:18.670179+03:00",
                   "ozet": "Test olayı: sistem başlatıldı",
                   "olay_tipi": "sistem", "sonuc": "başarılı"}]
insight_with = _generate_insight(sample_events, ["sistem"], mood)
test("_generate_insight olaylı string döndürüyor",
     isinstance(insight_with, str) and len(insight_with) > 10)
test("_generate_insight olay özetini içeriyor",
     "Test olayı" in insight_with)

# Test 7: produce_insight çalışıyor ve log'a yazıyor
log_path = os.path.expanduser("~/.hermes/consciousness.log")
if os.path.exists(log_path):
    os.remove(log_path)
insight = produce_insight(24)
test("produce_insight string döndürüyor",
     isinstance(insight, str) and len(insight) > 10)
test("consciousness.log oluştu", os.path.exists(log_path))

# Test 8: get_recent_insights çalışıyor
if os.path.exists(log_path):
    # Bir tane daha ekleyelim
    produce_insight(24)
    recent = get_recent_insights(1)
    test("get_recent_insights en az 1 sonuç döndürüyor", len(recent) >= 1)
    if recent:
        test("Her insight timestamp ve insight anahtarlarını içeriyor",
             all(k in recent[0] for k in ["timestamp", "insight"]))

# Test 9: Mood intensity 0-1 arasında
test("Mood intensity 0-1 arasında",
     0.0 <= mood.get("intensity", 0) <= 1.0)

print(f"\n📊 SONUÇ: {passed}/{passed + failed} PASS", end="")
if failed:
    print(f", {failed} FAILED ❌")
    sys.exit(1)
else:
    print(" ✅")
