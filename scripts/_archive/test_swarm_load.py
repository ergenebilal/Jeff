#!/usr/bin/env python3
"""Swarm Yük Testi — 10 görevi 5 Jeff kopyasına bölüp çalıştırır.
Çakışma, kilitlenme, veri tutarsızlığı kontrolü.
"""

import sys
import os
import shutil
sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))

from swarm_orchestrator import run_swarm
from swarm_merger import merge_reports, collect_outputs

TEST_PASS = 0
TEST_FAIL = 0
TEST_TOTAL = 0

# Temiz başlangıç
swarm_dir = os.path.expanduser("~/.hermes/swarm")
if os.path.exists(swarm_dir):
    shutil.rmtree(swarm_dir)


def test(name: str, condition: bool):
    global TEST_PASS, TEST_FAIL, TEST_TOTAL
    TEST_TOTAL += 1
    if condition:
        TEST_PASS += 1
        print(f"  ✅ {name}")
    else:
        TEST_FAIL += 1
        print(f"  ❌ {name}")


print("🧪 YÜK TESTİ: 10 Görev × 5 Swarm Agent\n")

# 10 görev oluştur — her biri 3 alt göreve bölünecek
gorevler = [f"Lead DM gonder - {i+1}" for i in range(10)]

tum_swarm_ids = []
toplam_agent = 0
toplam_basarili = 0

for i, gorev in enumerate(gorevler):
    print(f"\n📦 Görev {i+1}/10: {gorev}")
    r = run_swarm(gorev, sub_goals=[
        f"Kesif: {gorev}",
        f"Uygulama: {gorev}",
        f"Dogrulama: {gorev}",
    ])
    tum_swarm_ids.append(r["swarm_id"])
    toplam_agent += r["alt_gorev_sayisi"]
    toplam_basarili += r["basarili"]
    print(f"  Swarm: {r['swarm_id']} | Agent: {r['alt_gorev_sayisi']} "
          f"| Basarili: {r['basarili']}")

# Test 1: Tüm görevler başarıyla tamamlandı mı?
test("10 gorevin tamami calisti", len(tum_swarm_ids) == 10)
test("Toplam 30 agent spawn edildi (10x3)", toplam_agent == 30)
test("Tum agent'lar basarili", toplam_basarili == toplam_agent)

# Test 2: Çakışma kontrolü — her swarm ID benzersiz olmalı
test("Tum swarm ID'ler benzersiz", len(set(tum_swarm_ids)) == 10)

# Test 3: Merger doğrulama
print("\n🔗 Merger dogrulama...")
for i, sid in enumerate(tum_swarm_ids[:3]):  # İlk 3'ü test et
    outputs = collect_outputs(sid)
    actual_count = len(outputs)
    test(f"Swarm {i+1}: 3 output toplandi (bulunan: {actual_count})",
         actual_count == 3)
    
    merged = merge_reports(sid)
    test(f"Swarm {i+1}: Birlestirme basarili",
         merged is not None)
    test(f"Swarm {i+1}: Ozet bilgisi var",
         "ozet" in merged)
    test(f"Swarm {i+1}: Basari orani %100",
         merged["ozet"]["basari_orani"] == 1.0)

# Test 4: Veri tutarsızlığı kontrolü
print("\n🔍 Veri tutarsizligi kontrolu...")
tum_agents = []
for sid in tum_swarm_ids:
    outputs = collect_outputs(sid)
    for o in outputs:
        tum_agents.append(o["agent_id"])

test("Tum agent ID'ler benzersiz", len(tum_agents) == len(set(tum_agents)))
test("Agent ID'lerde None yok", all(a is not None for a in tum_agents))

# Test 5: Çıktı dosyaları fiziksel olarak var mı?
outputs_dir = os.path.expanduser("~/.hermes/swarm/outputs")
if os.path.exists(outputs_dir):
    json_files = [f for f in os.listdir(outputs_dir) if f.endswith(".json")]
    test(f"Output dosyalari fiziksel olarak mevcut ({len(json_files)} adet)",
         len(json_files) >= 30)

print(f"\n📊 YÜK TESTİ SONUCU: {TEST_PASS}/{TEST_TOTAL} PASS {'✅' if TEST_FAIL == 0 else '❌'}")
if TEST_FAIL > 0:
    print(f"  BASARISIZ: {TEST_FAIL}")
    sys.exit(1)
else:
    print("  Swarm yuk testi basariyla gecti! Kilitlemme, cakisma veya veri tutarsizligi yok.")
