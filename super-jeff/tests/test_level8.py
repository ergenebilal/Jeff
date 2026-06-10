#!/usr/bin/env python3
"""Test: Level 8 — Çoklu Jeff Kolonisi (Swarm Intelligence)
14 test: swarm_orchestrator + swarm_communicator + swarm_merger
"""

import sys
import os
sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))

import shutil

from swarm_orchestrator import decompose_task, run_swarm
from swarm_communicator import send_message, read_messages, get_conversation_history, broadcast_status
from swarm_merger import collect_outputs, merge_reports, list_swarms

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


print("🧪 TEST: Level 8 — Çoklu Jeff Kolonisi\n")

# === swarm_orchestrator ===
print("🐝 swarm_orchestrator.py:")

# 1. Görev parçalama
plan = decompose_task("E-ticaret mağazasını analiz et, fiyatları optimize et")
test("Görev parçalandı", plan is not None)
test("Swarm ID var", "swarm_id" in plan)
test("3 alt görev oluştu", len(plan["alt_gorevler"]) == 3)
test("Her alt görevin task_id'si var",
     all(t.get("task_id") for t in plan["alt_gorevler"]))
test("Her alt görevin output_path'i var",
     all(t.get("output_path") for t in plan["alt_gorevler"]))

# 2. Swarm çalıştırma
r = run_swarm("Test görevi: veri topla, işle, raporla",
              sub_goals=["Veri topla", "Veriyi işle", "Rapor hazırla"])
test("Swarm çalıştırıldı", r is not None)
test("3 alt agent spawn edildi", r["alt_gorev_sayisi"] == 3)
test("Tüm agent'lar başarılı", r["basarili"] == 3)
test("Her agent için çıktı var",
     all("output_path" in a for a in r["agentler"]))

# === swarm_communicator ===
print("\n📨 swarm_communicator.py:")

# 3. İletişim testleri
msg1 = send_message("jeff_kopya_1", "jeff_kopya_2",
                     "Lead DM'lerini bitirdim, sen içerik üretimine başlayabilirsin")
test("Mesaj gönderildi", msg1 is not None)
test("Message ID var", "message_id" in msg1)
test("Gönderen doğru", msg1["from"] == "jeff_kopya_1")
test("Alan doğru", msg1["to"] == "jeff_kopya_2")

msg2 = send_message("jeff_kopya_2", "jeff_kopya_3",
                     "İçerik hazır, görsel üretimine başlayabilirsin")
test("2. mesaj gönderildi", msg2 is not None)
test("2 farklı mesajlaşma var",
     len(get_conversation_history()) >= 2)

# 4. Mesaj okuma
inbox = read_messages("jeff_kopya_2")
test("Alıcının inbox'ında mesaj var", len(inbox) >= 1)
test("Mesaj içeriği doğru", "Lead DM" in inbox[0]["message"])

# 5. Broadcast
bc = broadcast_status("jeff_kopya_1", "tamam", "Tüm lead işlemleri bitti")
test("Broadcast gönderildi", bc is not None)
test("Broadcast 'tümü'ne gitti", bc["to"] == "tümü")

# === swarm_merger ===
print("\n🔗 swarm_merger.py:")

# 6. Çıktı toplama ve birleştirme
swarm_id = r["swarm_id"]
outputs = collect_outputs(swarm_id)
test("Çıktılar toplandı", len(outputs) == 3)
test("Her çıktıda sonuç var", all(o.get("sonuc") for o in outputs))

merged = merge_reports(swarm_id)
test("Birleştirme raporu oluştu", merged is not None)
test("Özet bilgisi var", "ozet" in merged)
test("3 agent çıktısı birleşti",
     merged["ozet"]["toplam_agent"] == 3)
test("Başarı oranı %100",
     merged["ozet"]["basari_orani"] == 1.0)
test("Birleştirilmiş çıktı metni var",
     len(merged.get("birlestirilmis_cikti", "")) > 50)

# 7. Swarm listesi
swarms = list_swarms()
test("Swarm listesi döndü", len(swarms) >= 0)

print(f"\n📊 SONUÇ: {TEST_PASS}/{TEST_TOTAL} PASS {'✅' if TEST_FAIL == 0 else '❌'}")
if TEST_FAIL > 0:
    print(f"  BAŞARISIZ: {TEST_FAIL}")
    sys.exit(1)
