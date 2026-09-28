#!/usr/bin/env python3
"""Meta Learner — daha önce öğrenilen skill'leri analiz edip yeni bir
skill için optimize öğrenme planı oluşturur.
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

TZ = timezone(timedelta(hours=3))
SCRIPTS_DIR = os.path.expanduser("~/.hermes/scripts")
LESSONS_PATH = os.path.expanduser("~/.hermes/learning/lessons.jsonl")
EPISODIC_PATH = os.path.expanduser("~/.hermes/brain/episodic_memory.jsonl")
SEMANTIC_PATH = os.path.expanduser("~/.hermes/brain/semantic_knowledge.json")
ANALYSIS_PATH = os.path.expanduser("~/.hermes/brain/meta_analysis.json")


def _load_lessons() -> List[Dict]:
    if not os.path.exists(LESSONS_PATH):
        return []
    lessons = []
    try:
        with open(LESSONS_PATH) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    lessons.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except IOError:
        pass
    return lessons


def _load_episodic_all() -> List[Dict]:
    if not os.path.exists(EPISODIC_PATH):
        return []
    events = []
    try:
        with open(EPISODIC_PATH) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except IOError:
        pass
    return events


def _load_semantic() -> Dict:
    if not os.path.exists(SEMANTIC_PATH):
        return {"kavramlar": []}
    try:
        with open(SEMANTIC_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"kavramlar": []}


def _save_analysis(data: Dict) -> None:
    os.makedirs(os.path.dirname(ANALYSIS_PATH), exist_ok=True)
    with open(ANALYSIS_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _analyze_learning_pattern(skill_name: str) -> Dict:
    lessons = _load_lessons()
    events = _load_episodic_all()
    keywords = [w.lower() for w in skill_name.split() if len(w) > 2 and w.isalpha()]
    benzer_lessons = [d for d in lessons
                      if any(k in d.get("trigger", "").lower() or k in d.get("lesson", "").lower() for k in keywords)]
    benzer_events = [ev for ev in events
                     if any(k in ev.get("ozet", "").lower() for k in keywords)]

    ortalama_sure = 30
    total_lessons = len(lessons)
    if total_lessons > 20:
        hizlanma = 0.6
    elif total_lessons > 10:
        hizlanma = 0.75
    elif total_lessons > 5:
        hizlanma = 0.85
    else:
        hizlanma = 1.0

    ortak_basamaklar = [
        "1. Ortam hazirligi",
        "2. Temel kavramlar",
        "3. Ilk deneme",
        "4. Entegrasyon",
        "5. Test et",
        "6. Otomasyon",
    ]
    tahmini_sure = max(5, int(ortalama_sure * hizlanma))
    return {
        "skill_name": skill_name,
        "tahmini_sure_dk": tahmini_sure,
        "normal_sure_dk": ortalama_sure,
        "hizlanma_faktoru": round(hizlanma, 2),
        "basamaklar": ortak_basamaklar,
        "benzer_olay_sayisi": len(benzer_events),
        "toplam_gecmis_ders": total_lessons,
    }


def create_learning_plan(skill_name: str) -> Dict:
    analysis = _analyze_learning_pattern(skill_name)
    skill_lower = skill_name.lower()
    if "instagram" in skill_lower or "twitter" in skill_lower:
        specific_steps = [
            "OAuth kurulumu", "Graph API yapisi", "Medya yukleme",
            "DM/comment okuma", "Analytics", "Cron otomasyon",
        ]
    elif "gumroad" in skill_lower or "satis" in skill_lower:
        specific_steps = [
            "API token", "Urun CRUD", "Sales/refund", "Raporlama", "Webhook",
        ]
    elif "api" in skill_lower:
        specific_steps = [
            "API key", "Endpoint dokuman", "HTTP GET", "POST/PUT/DELETE",
            "Hata yonetimi", "Rate limiting",
        ]
    else:
        specific_steps = [
            "Pre-nsipleri", "Kurulum", "Minimal ornek", "Entegrasyon",
            "Test", "Dokuman",
        ]

    plan = {
        "plan_id": f"learn_{datetime.now(TZ).strftime('%Y%m%d_%H%M%S')}",
        "skill": skill_name,
        "analiz": analysis,
        "adimlar": [],
        "tahmini_toplam_sure_dk": analysis["tahmini_sure_dk"] + len(specific_steps) * 5,
    }
    for i, step in enumerate(analysis["basamaklar"]):
        plan["adimlar"].append({"adim_no": i + 1, "aciklama": step, "tamamlandi": False})
    offset = len(analysis["basamaklar"])
    for i, step in enumerate(specific_steps):
        plan["adimlar"].append({"adim_no": offset + i + 1, "aciklama": step, "tamamlandi": False})
    _save_analysis(analysis)
    return plan


def compare_learning_speed(skill_name: str) -> Dict:
    plan = create_learning_plan(skill_name)
    analysis = plan["analiz"]
    eski_sure = analysis["normal_sure_dk"]
    yeni_sure = analysis["tahmini_sure_dk"]
    kazanim = round((1 - yeni_sure / max(eski_sure, 1)) * 100, 1) if eski_sure > 0 else 0.0
    return {
        "skill_name": skill_name,
        "eski_sure_dk": eski_sure,
        "yeni_sure_dk": yeni_sure,
        "kazanim_yuzde": kazanim,
        "hizlanma_faktoru": analysis["hizlanma_faktoru"],
        "analiz": f"'{skill_name}' icin %{kazanim} daha hizli",
        "timestamp": datetime.now(TZ).isoformat(),
    }

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Meta Learner")
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("plan")
    p.add_argument("skill", type=str)
    p2 = sub.add_parser("compare")
    p2.add_argument("skill", type=str)
    args = parser.parse_args()
    if args.command == "plan":
        plan = create_learning_plan(args.skill)
        a = plan["analiz"]
        print(f"📚 OGRENME PLANI: {plan['skill']}")
        print(f"⏱️  Sure: {a['tahmini_sure_dk']}dk")
    elif args.command == "compare":
        r = compare_learning_speed(args.skill)
        print(f"📊 KARSILASTIRMA: %{r['kazanim_yuzde']} kazanim")
    else:
        parser.print_help()
