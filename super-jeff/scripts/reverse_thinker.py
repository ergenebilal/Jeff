#!/usr/bin/env python3
"""Reverse Thinker — ters düşünme ve pre-mortem analizi."""

import json, os, sys, random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

TZ = timezone(timedelta(hours=3))
ANALYSIS_LOG = os.path.expanduser("~/.hermes/brain/reverse_analysis_log.jsonl")

RISK_CATEGORIES = {
    "finansal": {"riskler": ["Butceyi asmak", "Fiyatlandirma hatasi", "Maliyet kontrolsuzlugu"], "siddet": 0.8},
    "teknik": {"riskler": ["Over-engineering", "Testsiz deploy", "Guvenlik acigi", "Olceksiz mimari"], "siddet": 0.9},
    "operasyonel": {"riskler": ["Prosedur atlama", "Dokumansiz", "Iletisimsizlik"], "siddet": 0.7},
    "stratejik": {"riskler": ["Rakip analizi yok", "Pazar hatasi", "Erken olceklenme"], "siddet": 0.85},
}


def reverse_simulate(goal: str, domain: Optional[str] = None) -> Dict:
    goal_lower = goal.lower()
    hedef_riskler = []
    if "gumroad" in goal_lower or "satis" in goal_lower:
        hedef_riskler = ["Urunleri guncellememek", "Fiyat optimizasyonu yapmamak", "Marketing yapmamak"]
    elif "twitter" in goal_lower or "x" in goal_lower:
        hedef_riskler = ["Spam tweet", "Tutarsiz icerik", "Etkilesime girmemek"]
    else:
        hedef_riskler = ["Plansiz baslamak", "Ilerlemeyi takip etmemek", "Vazgecmek"]

    tum_riskler = list(hedef_riskler)
    if domain and domain in RISK_CATEGORIES:
        tum_riskler.extend(RISK_CATEGORIES[domain]["riskler"])
    else:
        for cat in RISK_CATEGORIES.values():
            tum_riskler.extend(cat["riskler"])

    random.seed(hash(goal) % (2**32))
    degerlendirilen = []
    for risk in tum_riskler:
        degerlendirilen.append({"risk": risk, "olasilik": round(random.uniform(0.3, 0.95), 2),
                                "etki": random.choice(["kritik", "yuksek", "orta"])})
    degerlendirilen.sort(key=lambda r: r["olasilik"], reverse=True)
    kritik = [r for r in degerlendirilen if r["olasilik"] > 0.5]
    return {"hedef": goal, "toplam_risk": len(degerlendirilen), "kritik_risk_sayisi": len(kritik),
            "kritik_uyarilar": kritik[:5], "tum_riskler": degerlendirilen,
            "analiz": f"'{goal}' icin {len(kritik)} kritik risk tespit edildi"}


def pre_mortem_analysis(project: str) -> Dict:
    return {"proje": project, "varsayim": f"'{project}' basarisiz oldu. Neden?",
            "sebepler": ["Yetersiz planlama", "Kapsam sismesi", "Kaynak yetersizligi",
                         "Testsiz canli", "Geri bildirim yok", "Dokumansiz"],
            "tavsiyeler": ["Kesif yap", "MVP'yi sinirla", "Her adimda test et", "Gunluk log tut"]}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("reverse")
    p.add_argument("goal", type=str)
    p2 = sub.add_parser("premortem")
    p2.add_argument("project", type=str)
    args = parser.parse_args()
    if args.command == "reverse":
        r = reverse_simulate(args.goal)
        print(f"Ters simulasyon: {r['toplam_risk']} risk, {r['kritik_risk_sayisi']} kritik")
    elif args.command == "premortem":
        pm = pre_mortem_analysis(args.project)
        print(f"Premortem: {len(pm['sebepler'])} basarisizlik sebebi")
