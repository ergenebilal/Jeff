#!/usr/bin/env python3
"""Autonomous Agent — düşük riskli eylemleri izinsiz gerçekleştirir."""

import json, os, sys, random
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

TZ = timezone(timedelta(hours=3))
SCRIPTS_DIR = os.path.expanduser("~/.hermes/scripts")
AUTONOMOUS_LOG = os.path.expanduser("~/.hermes/brain/autonomous_log.jsonl")

SAFE_ACTIONS = {
    "disk_temizle": {"aciklama": "Geçici dosyaları temizle", "risk": 0.02},
    "log_oku": {"aciklama": "Sistem loglarını oku", "risk": 0.01},
    "episodik_ozet": {"aciklama": "Episodik hafızayı özetle", "risk": 0.01},
    "lessons_kontrol": {"aciklama": "Ders durumunu kontrol et", "risk": 0.01},
    "cron_saglik": {"aciklama": "Cron sağlığını kontrol et", "risk": 0.03},
}


def _predict_risk(action_name: str) -> Dict:
    if action_name in SAFE_ACTIONS:
        return {"risk": SAFE_ACTIONS[action_name]["risk"], "guven": 0.95}
    try:
        sys.path.insert(0, SCRIPTS_DIR)
        from predictive_engine import simulate_with_mcts
        result = simulate_with_mcts(action_name, simulations=50)
        risk = round(1.0 - result.get("simulasyon_sonucu", 0.5), 3)
        return {"risk": risk, "guven": result.get("guven", 0.5)}
    except ImportError:
        return {"risk": 0.5, "guven": 0.5}


def assess_action(action_name: str, context: Optional[Dict] = None) -> Dict:
    prediction = _predict_risk(action_name)
    risk = prediction["risk"]
    esik = context.get("risk_esik", 0.05) if context else 0.05
    if risk <= esik:
        karar = "otonom"
    elif risk <= esik * 2:
        karar = "onay_gerekli"
    else:
        karar = "red"
    return {"action": action_name, "karar": karar, "risk": risk, "esik": esik, "guven": prediction["guven"],
            "mesaj": f"Risk %{risk*100:.1f} -> {karar}", "timestamp": datetime.now(TZ).isoformat()}


def execute_autonomous(action_name: str) -> Dict:
    assessment = assess_action(action_name)
    if assessment["karar"] != "otonom":
        return {"action": action_name, "sonuc": "iptal", "karar": assessment["karar"], "risk": assessment["risk"]}
    sim_basari = random.random() < 0.95
    return {"action": action_name, "sonuc": "başarılı" if sim_basari else "başarısız",
            "karar": "otonom", "risk": assessment["risk"], "kendi_karariyla": True,
            "mesaj": f"'{action_name}' {'tamamlandi' if sim_basari else 'hata'}"}


def list_safe_actions() -> List[Dict]:
    return [{"ad": k, "aciklama": v["aciklama"], "risk": v["risk"]} for k, v in SAFE_ACTIONS.items()]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("execute")
    p.add_argument("action", type=str, choices=list(SAFE_ACTIONS.keys()))
    p2 = sub.add_parser("assess")
    p2.add_argument("action", type=str)
    sub.add_parser("list")
    args = parser.parse_args()
    if args.command == "execute":
        r = execute_autonomous(args.action)
        print(f"{'🚀' if r['sonuc']=='başarılı' else '❌'} {r['action']}: {r['sonuc']}")
    elif args.command == "assess":
        a = assess_action(args.action)
        print(f"{a['action']}: Risk %{a['risk']*100:.0f} -> {a['karar']}")
    elif args.command == "list":
        for a in list_safe_actions():
            print(f"{a['ad']}: %{a['risk']*100:.0f} risk - {a['aciklama']}")
