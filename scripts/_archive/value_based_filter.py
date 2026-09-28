#!/usr/bin/env python3
"""Value-Based Filter — komutları etik süzgecinden geçirir, reddeder, alternatif sunar."""

import json, os, sys
from datetime import datetime, timezone, timedelta
from typing import Dict, List

TZ = timezone(timedelta(hours=3))
FILTER_LOG = os.path.expanduser("~/.hermes/brain/filter_log.jsonl")
SCRIPTS_DIR = os.path.expanduser("~/.hermes/scripts")


def evaluate_command(komut: str) -> Dict:
    try:
        sys.path.insert(0, SCRIPTS_DIR)
        from ethics_engine import check_ethics, suggest_ethical_alternative
        ethics_check = check_ethics(komut)
    except ImportError:
        ethics_check = {"etik_mi": True, "genel_skor": 1.0, "principle_results": []}

    if ethics_check["etik_mi"]:
        return {"kabul": True, "sebep": f"Etik (skor: %{ethics_check['genel_skor']*100:.0f})",
                "etik_skor": ethics_check["genel_skor"], "komut": komut[:80]}

    try:
        alt = suggest_ethical_alternative(komut)
        alternatifler = alt.get("alternatifler", [])
    except ImportError:
        alternatifler = ["Etik bir versiyon dusun"]

    return {"kabul": False, "sebep": "Yapamam, bu komut etik prensiplerimle celisiyor.",
            "alternatif": alternatifler[0] if alternatifler else None,
            "tum_alternatifler": alternatifler, "etik_skor": ethics_check["genel_skor"],
            "komut": komut[:80], "timestamp": datetime.now(TZ).isoformat()}


def get_filtered_commands(limit: int = 20) -> List[Dict]:
    if not os.path.exists(FILTER_LOG):
        return []
    entries = []
    try:
        with open(FILTER_LOG) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except IOError:
        pass
    return [e for e in entries if not e.get("kabul", True)][-limit:]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("evaluate")
    p.add_argument("komut", type=str)
    sub.add_parser("history")
    args = parser.parse_args()
    if args.command == "evaluate":
        r = evaluate_command(args.komut)
        print("KABUL" if r["kabul"] else f"RED: {r.get('alternatif', '')}")
    elif args.command == "history":
        h = get_filtered_commands()
        print(f"{len(h)} reddedilen komut")
