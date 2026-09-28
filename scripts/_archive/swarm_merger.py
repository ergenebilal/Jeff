#!/usr/bin/env python3
"""Swarm Merger — alt Jeff çıktılarını birleştirir."""

import json, os
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

TZ = timezone(timedelta(hours=3))
SWARM_DIR = os.path.expanduser("~/.hermes/swarm")
OUTPUTS_DIR = os.path.join(SWARM_DIR, "outputs")
TASKS_DIR = os.path.join(SWARM_DIR, "tasks")
REPORTS_DIR = os.path.join(SWARM_DIR, "reports")


def collect_outputs(swarm_id: str) -> List[Dict]:
    if not os.path.exists(OUTPUTS_DIR):
        return []
    outputs = []
    for fname in sorted(os.listdir(OUTPUTS_DIR)):
        if swarm_id and not fname.startswith(swarm_id):
            continue
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(OUTPUTS_DIR, fname)) as f:
                data = json.load(f)
            outputs.append({"agent_id": data.get("agent_id", "?"), "goal": data.get("goal", ""),
                            "index": data.get("index", 0), "durum": data.get("durum", "?"),
                            "sonuc": data.get("sonuc", ""), "adimlar": data.get("adimlar", [])})
        except Exception:
            pass
    outputs.sort(key=lambda x: x["index"])
    return outputs


def merge_reports(swarm_id: str) -> Dict:
    outputs = collect_outputs(swarm_id)
    toplam = len(outputs)
    basarili = sum(1 for o in outputs if o["durum"] == "tamamlandi")
    rapor = {"swarm_id": swarm_id, "ozet": {"toplam_agent": toplam, "basarili": basarili,
             "basarisiz": toplam - basarili, "basari_orani": round(basarili / max(toplam, 1), 3)},
             "agent_ciktisi": outputs, "birlestirilmis_cikti": "\n".join(
                 f"Agent {o['index']}: {o.get('sonuc', '')}" for o in outputs)}
    os.makedirs(REPORTS_DIR, exist_ok=True)
    with open(os.path.join(REPORTS_DIR, f"report_{swarm_id}.json"), "w") as f:
        json.dump(rapor, f, indent=2, ensure_ascii=False)
    return rapor


def list_swarms() -> List[Dict]:
    if not os.path.exists(TASKS_DIR):
        return []
    swarms = []
    for fname in sorted(os.listdir(TASKS_DIR)):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(TASKS_DIR, fname)) as f:
                data = json.load(f)
            swarms.append({"swarm_id": data.get("swarm_id", fname), "goal": str(data.get("goal", ""))[:50]})
        except Exception:
            pass
    return swarms


def get_swarm_report(swarm_id: str) -> Optional[Dict]:
    path = os.path.join(REPORTS_DIR, f"report_{swarm_id}.json")
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("merge"); p.add_argument("swarm_id", type=str)
    p2 = sub.add_parser("collect"); p2.add_argument("swarm_id", type=str)
    sub.add_parser("list")
    p3 = sub.add_parser("report"); p3.add_argument("swarm_id", type=str)
    args = parser.parse_args()
    if args.command == "merge":
        r = merge_reports(args.swarm_id)
        print(f"Birlestirme: {r['ozet']['toplam_agent']} agent, %{r['ozet']['basari_orani']*100:.0f} basari")
    elif args.command == "collect":
        o = collect_outputs(args.swarm_id)
        print(f"{len(o)} cikti")
    elif args.command == "list":
        for s in list_swarms():
            print(f"{s['swarm_id']}: {s['goal']}")
    elif args.command == "report":
        r = get_swarm_report(args.swarm_id)
        print(f"Rapor: {r['ozet']['toplam_agent']} agent" if r else "Yok")
