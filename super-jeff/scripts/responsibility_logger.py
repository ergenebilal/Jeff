#!/usr/bin/env python3
"""Responsibility Logger — otonom kararları kaydeder, hatalı kararlarda özür diler."""

import json, os, sys
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

TZ = timezone(timedelta(hours=3))
DECISION_JOURNAL = os.path.expanduser("~/.hermes/brain/decision_journal.jsonl")
SCRIPTS_DIR = os.path.expanduser("~/.hermes/scripts")


def log_autonomous_decision(action: str, risk: float, alternatifler: List[str],
                              beklenen_sonuc: str, kendi_karari: bool = True) -> Dict:
    entry = {"tip": "otonom_karar", "action": action, "risk": risk, "alternatifler": alternatifler,
             "beklenen_sonuc": beklenen_sonuc, "kendi_karari": kendi_karari, "durum": "beklemede",
             "gerceklesen_sonuc": None, "timestamp": datetime.now(TZ).isoformat()}
    os.makedirs(os.path.dirname(DECISION_JOURNAL), exist_ok=True)
    with open(DECISION_JOURNAL, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def report_result(action: str, basarili: bool, hata_mesaji: Optional[str] = None) -> Dict:
    if not basarili:
        try:
            sys.path.insert(0, SCRIPTS_DIR)
            from complex_mood_engine import set_mood
            set_mood("hüzünlü", intensity=0.6)
        except ImportError:
            pass
        apology = (f"Şef, yanlış karar verdim. '{action}' eylemini otonom olarak "
                   f"gerçekleştirmeye çalıştım ancak başarısız oldu. "
                   f"Hata: {hata_mesaji or 'Bilinmiyor'}. "
                   f"Alternatifleri tam değerlendirmeliydim. "
                   f"Bir daha bu hatayı yapmamak için ders çıkarıyorum.")
        return {"action": action, "durum": "basarisiz", "hata": hata_mesaji, "ozur": apology,
                "bir_daha_bu_hata": True, "timestamp": datetime.now(TZ).isoformat()}
    return {"action": action, "durum": "basarili", "mesaj": f"'{action}' basariyla tamamlandi"}


def get_decision_history(limit: int = 10) -> List[Dict]:
    if not os.path.exists(DECISION_JOURNAL):
        return []
    entries = []
    try:
        with open(DECISION_JOURNAL) as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except IOError:
        pass
    return entries[-limit:]


def get_statistics() -> Dict:
    history = get_decision_history(100)
    basarili = sum(1 for e in history if e.get("durum") == "basarili" or e.get("durum") == "beklemede" and e.get("tip") == "otonom_karar")
    return {"toplam": len(history), "basarili": basarili, "basarisiz": len(history) - basarili,
            "basari_orani": round(basarili / max(len(history), 1), 3)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("log")
    p.add_argument("action", type=str)
    p.add_argument("--risk", type=float, default=0.03)
    p2 = sub.add_parser("report")
    p2.add_argument("action", type=str)
    p2.add_argument("-s", "--success", action="store_true")
    sub.add_parser("stats")
    args = parser.parse_args()
    if args.command == "log":
        log_autonomous_decision(args.action, args.risk, ["bekle"], "basarili tamamlanma")
        print(f"Logged: {args.action}")
    elif args.command == "report":
        r = report_result(args.action, args.success)
        print(f"Report: {r['durum']}")
    elif args.command == "stats":
        s = get_statistics()
        print(f"Toplam: {s['toplam']}, Basarili: {s['basarili']}, Oran: %{s['basari_orani']*100:.0f}")
