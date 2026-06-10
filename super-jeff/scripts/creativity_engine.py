#!/usr/bin/env python3
"""Creativity Engine — mevcut bilgileri birleştirip yeni fikirler üretir."""

import json, os, sys, random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

TZ = timezone(timedelta(hours=3))
SEMANTIC_PATH = os.path.expanduser("~/.hermes/brain/semantic_knowledge.json")
CREATIVITY_LOG = os.path.expanduser("~/.hermes/brain/creativity_log.jsonl")

CONCEPT_POOL = {
    "ai": ["yapay zeka", "doğal dil", "görüntü işleme", "ses tanıma", "öneri sistemi", "chatbot"],
    "business": ["restoran", "e-ticaret", "pazarlama", "müşteri hizmetleri", "abonelik"],
    "tech": ["API", "webhook", "cron", "veritabanı", "bulut", "mobil uygulama", "dashboard"],
    "social": ["sosyal medya", "mesajlaşma", "topluluk", "paylaşım", "influencer", "içerik"],
}

INNOVATION_PATTERNS = ["[K1] + [K2] = Yeni hizmet", "[K1]'yi [K2] ile otomatikleştir", "[K2] destekli [K1] asistanı"]


def _load_semantic() -> Dict:
    if not os.path.exists(SEMANTIC_PATH):
        return {"kavramlar": []}
    try:
        with open(SEMANTIC_PATH) as f:
            return json.load(f)
    except Exception:
        return {"kavramlar": []}


def _get_concepts(domain: Optional[str] = None, count: int = 2) -> List[str]:
    pool = []
    if domain and domain in CONCEPT_POOL:
        pool = list(CONCEPT_POOL[domain])
    else:
        for cat in CONCEPT_POOL.values():
            pool.extend(cat)
    semantic = _load_semantic()
    for k in semantic.get("kavramlar", []):
        name = k.get("kavram", "").strip()
        if name and name not in pool:
            pool.append(name)
    random.shuffle(pool)
    return pool[:count]


def generate_ideas(domain: Optional[str] = None, count: int = 3) -> List[Dict]:
    ideas = []
    for _ in range(count * 2):
        concepts = _get_concepts(domain, 2)
        c1, c2 = concepts[0], concepts[1] if len(concepts) > 1 else concepts[0]
        pattern = random.choice(INNOVATION_PATTERNS)
        idea = {
            "isim": f"{c1.title()}-{c2.title()}",
            "konsept": pattern.replace("[K1]", c1).replace("[K2]", c2),
            "puan": random.randint(5, 9),
            "zorluk": random.choice(["kolay", "orta", "zor"]),
            "timestamp": datetime.now(TZ).isoformat(),
        }
        ideas.append(idea)
        if len(ideas) >= count:
            break
    return ideas


def generate_marketing_strategy() -> Dict:
    return {
        "analiz_ani": datetime.now(TZ).isoformat(),
        "aktif_projeler": ["gumroad", "twitter", "instagram"],
        "stratejiler": [
            {"proje": "gumroad", "strateji": "Sosyal medya + pazarlama ile büyütme",
             "adimlar": ["Haftalık içerik planla", "Lead topla", "A/B test"]}
        ],
    }


def generate_workflow_idea() -> Dict:
    c1, c2 = random.choice(CONCEPT_POOL["tech"]), random.choice(CONCEPT_POOL["ai"])
    return {
        "isim": f"{c1.title()} + {c2.title()} Otomasyonu",
        "aciklama": f"{c1} ile {c2} birleştiren iş akışı",
        "adimlar": [f"{c1} entegrasyonu", f"{c2} modeli", "Test", "Otomasyon"],
        "tahmini_sure_saat": random.randint(2, 8),
        "timestamp": datetime.now(TZ).isoformat(),
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("ideas")
    p.add_argument("-d", "--domain", choices=list(CONCEPT_POOL.keys()))
    p.add_argument("-c", "--count", type=int, default=3)
    sub.add_parser("marketing")
    sub.add_parser("workflow")
    args = parser.parse_args()
    if args.command == "ideas":
        for i, idea in enumerate(generate_ideas(args.domain, args.count), 1):
            print(f"{i}. {idea['isim']} - Puan: {idea['puan']}/10")
    elif args.command == "marketing":
        s = generate_marketing_strategy()
        print(f"Aktif: {', '.join(s['aktif_projeler'])}")
        for st in s['stratejiler']:
            print(f"{st['proje']}: {st['strateji']}")
    elif args.command == "workflow":
        w = generate_workflow_idea()
        print(f"Is Akisi: {w['isim']} ({w['tahmini_sure_saat']}s)")
