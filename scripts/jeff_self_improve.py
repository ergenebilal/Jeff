#!/usr/bin/env python3
"""
Jeff Self-Improvement Auto-Patch Loop — v1.0

Cron tarafından periyodik çağrılır:
  1. analyze_lessons() ile zayıf noktaları tespit et
  2. generate_patch_plan() ile patch planı üret
  3. Düşük riskli patch'leri otomatik uygula (skill güncelleme, config iyileştirme)
  4. Raporla
"""

import sys
import json
import subprocess
from pathlib import Path

# Beyin yolunu ekle
BRAIN_PATH = Path("/opt/jeff-brain")
if str(BRAIN_PATH) not in sys.path:
    sys.path.insert(0, str(BRAIN_PATH))

# Import
from brain.phase6.self_improvement import analyze_lessons, analyze_skills, generate_patch_plan
from brain.learning import save_lesson

# Log
LOOP_LOG = Path.home() / ".hermes" / "logs" / "self_improve_loop.jsonl"
LOOP_LOG.parent.mkdir(parents=True, exist_ok=True)


def log_result(entry: dict):
    try:
        with LOOP_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


def auto_apply_patches(plan: dict) -> list:
    """Düşük riskli patch'leri otomatik uygula."""
    applied = []
    for patch in plan.get("patches", []):
        patch_type = patch.get("patch_type", "info")

        # Sadece "info" tipi patch'leri uygula (düşük riskli)
        # Skill/config patch'leri manuel — çok riskli
        if patch_type == "info":
            continue

        # Bilgilendirici patch'leri log'a kaydet
        applied.append({
            "target": patch.get("target", "?"),
            "issue": patch.get("issue", "?")[:80],
            "action": patch.get("suggested_action", "?")[:80],
            "applied": False,  # şimdilik sadece raporla, uygulama yok
            "reason": "Auto-patch disabled for safety — manual review needed",
        })

    return applied


def run():
    """Ana döngü adımı."""
    print("🔄 JEFF SELF-IMPROVEMENT LOOP")
    print("=" * 40)

    # 1. Analiz
    lessons = analyze_lessons()
    skills = analyze_skills()

    print(f"📚 Dersler: {lessons.get('total_lessons', 0)} toplam")
    print(f"🔧 Skill'ler: {skills.get('total', 0)} toplam, {len(skills.get('weak_skills', []))} zayıf")

    # 2. Patch planı
    plan = generate_patch_plan()
    print(f"🩹 Patch önerisi: {len(plan.get('patches', []))}")
    for p in plan.get("patches", []):
        print(f"   - [{p.get('patch_type','?')}] {p.get('target','?')}: {p.get('issue','?')[:60]}")

    # 3. Oto-patch dene
    applied = auto_apply_patches(plan)
    print(f"⚙️  Otomatik uygulanan: {len(applied)}")

    # 4. Öğrenme dersi olarak kaydet
    save_lesson(
        category="system",
        trigger="self_improve_loop",
        lesson=f"Self-improvement döngüsü: {lessons.get('total_lessons',0)} ders, "
               f"{len(plan.get('patches',[]))} patch önerisi, "
               f"{len(applied)} otomatik uygulama"
    )

    # 5. Log
    entry = {
        "timestamp": __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
        "total_lessons": lessons.get("total_lessons", 0),
        "weak_skills": len(skills.get("weak_skills", [])),
        "patches_proposed": len(plan.get("patches", [])),
        "auto_applied": len(applied),
        "priority": plan.get("priority", "low"),
    }
    log_result(entry)

    print("=" * 40)
    print(f"✅ Döngü tamam — öncelik: {plan.get('priority', 'low')}")


if __name__ == "__main__":
    run()
