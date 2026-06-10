#!/usr/bin/env python3
"""Swarm Orchestrator — ana Jeff, bir görevi alt görevlere böler.
Her alt görev için yeni bir Jeff instance'ı (kopya) oluşturup
paralel çalıştırır.

Alt Jeff'ler birbirlerinin işine karışmaz, her biri kendi
output dosyasına yazar.
"""

import json
import os
import sys
import subprocess
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

TZ = timezone(timedelta(hours=3))

SWARM_DIR = os.path.expanduser("~/.hermes/swarm")
ORCHESTRATOR_LOG = os.path.join(SWARM_DIR, "orchestrator_log.jsonl")
TASKS_DIR = os.path.join(SWARM_DIR, "tasks")
OUTPUTS_DIR = os.path.join(SWARM_DIR, "outputs")


def _ensure_dirs():
    """Swarm dizin yapısını oluştur."""
    for d in [SWARM_DIR, TASKS_DIR, OUTPUTS_DIR]:
        os.makedirs(d, exist_ok=True)


def _log(entry: Dict) -> None:
    """Orkestratör log'u."""
    _ensure_dirs()
    with open(ORCHESTRATOR_LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _generate_task_id() -> str:
    """Benzersiz görev ID'si üret."""
    import random
    ts = datetime.now(TZ).strftime("%H%M%S")
    rid = random.randint(1000, 9999)
    return f"task_{ts}_{rid}"


_AGENT_TEMPLATE = r"""#!/usr/bin/env python3
import json, os, time, random
from datetime import datetime, timezone, timedelta

TZ = timezone(timedelta(hours=3))
AGENT_ID = {agent_id!r}
TASK_ID = {task_id!r}
GOAL = {goal!r}
INDEX = {index}
TOTAL = {total}
OUTPUT_PATH = {output_path!r}

output = {{
    "agent_id": AGENT_ID,
    "task_id": TASK_ID,
    "goal": GOAL,
    "index": INDEX,
    "toplam": TOTAL,
    "basladi": datetime.now(TZ).isoformat(),
    "durum": "calisiyor",
    "adimlar": [],
    "sonuc": ""
}}

for adim in ["Veri toplaniyor...", "Isleniyor...", "Rapor hazirlaniyor..."]:
    time.sleep(random.uniform(0.05, 0.15))
    output["adimlar"].append(adim)

output["durum"] = "tamamlandi"
output["sonuc"] = "'{{}}' alt gorevi tamamlandi. Surec: ".format(GOAL) + ", ".join(output["adimlar"])
output["bitti"] = datetime.now(TZ).isoformat()

with open(OUTPUT_PATH, "w") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
print(output["agent_id"] + ": " + output["sonuc"])
"""


def _generate_agent_code(agent_id: str, task_id: str, goal: str,
                          index: int, total: int, output_path: str) -> str:
    """Alt agent Python kodunu üret."""
    return _AGENT_TEMPLATE.format(
        agent_id=agent_id,
        task_id=task_id,
        goal=goal,
        index=index,
        total=total,
        output_path=output_path,
    )


def decompose_task(goal: str, sub_goals: Optional[List[str]] = None) -> Dict:
    """Bir görevi alt görevlere böl.

    Args:
        goal: Ana görev
        sub_goals: Manuel alt görev listesi (yoksa otomatik)

    Returns:
        Parçalanmış görev planı
    """
    goal_lower = goal.lower()

    if not sub_goals:
        if "analiz" in goal_lower or "incele" in goal_lower:
            sub_goals = [
                f"Analiz modulu 1: {goal} — veri toplama",
                f"Analiz modulu 2: {goal} — trend tespiti",
                f"Analiz modulu 3: {goal} — raporlama",
            ]
        elif "sosyal" in goal_lower or "instagram" in goal_lower or "twitter" in goal_lower:
            sub_goals = [
                f"Icerik planlama: {goal}",
                f"Gorsel uretim: {goal}",
                f"Yayin takvimi: {goal}",
            ]
        elif "kod" in goal_lower or "yazilim" in goal_lower or "gelistir" in goal_lower:
            sub_goals = [
                f"Frontend gelistirme: {goal}",
                f"Backend gelistirme: {goal}",
                f"Test ve deploy: {goal}",
            ]
        elif "e-ticaret" in goal_lower or "gumroad" in goal_lower:
            sub_goals = [
                f"Urun analizi: {goal}",
                f"Fiyat optimizasyonu: {goal}",
                f"Pazarlama icerigi: {goal}",
            ]
        else:
            sub_goals = [
                f"Kesif: {goal} — mevcut durumu analiz et",
                f"Uygulama: {goal} — cozumu insa et",
                f"Dogrulama: {goal} — sonuclari dogrula",
            ]

    plan = {
        "swarm_id": _generate_task_id(),
        "goal": goal,
        "olusturulma": datetime.now(TZ).isoformat(),
        "alt_gorevler": [],
    }

    for i, sg in enumerate(sub_goals):
        task_id = f"{plan['swarm_id']}_{i+1}"
        task = {
            "task_id": task_id,
            "alt_goal": sg,
            "index": i + 1,
            "toplam": len(sub_goals),
            "durum": "beklemede",
            "output_path": os.path.join(OUTPUTS_DIR, f"{task_id}.json"),
        }
        plan["alt_gorevler"].append(task)

    _ensure_dirs()
    plan_path = os.path.join(TASKS_DIR, f"{plan['swarm_id']}.json")
    with open(plan_path, "w") as f:
        json.dump(plan, f, indent=2, ensure_ascii=False)

    _log({
        "olay": "gorev_parcalandi",
        "swarm_id": plan["swarm_id"],
        "goal": goal,
        "alt_gorev_sayisi": len(sub_goals),
        "timestamp": datetime.now(TZ).isoformat(),
    })

    return plan


def spawn_sub_agent(task: Dict) -> Dict:
    """Bir alt Jeff instance'ı oluştur ve alt görevi çalıştır.

    Args:
        task: Alt görev dict

    Returns:
        Agent instance bilgisi
    """
    agent_id = f"jeff_kopya_{task['index']}_{task['task_id'][-6:]}"
    output_path = task["output_path"]

    alt_code = _generate_agent_code(
        agent_id=agent_id,
        task_id=task["task_id"],
        goal=task["alt_goal"],
        index=task["index"],
        total=task["toplam"],
        output_path=output_path,
    )

    try:
        proc = subprocess.run(
            [sys.executable, "-c", alt_code],
            capture_output=True, text=True, timeout=30,
        )
        basarili = proc.returncode == 0
        cikti = proc.stdout.strip()
        hata = proc.stderr.strip() if proc.stderr else None
    except subprocess.TimeoutExpired:
        basarili = False
        cikti = ""
        hata = "Timeout"

    agent_info = {
        "agent_id": agent_id,
        "task_id": task["task_id"],
        "basarili": basarili,
        "cikti": cikti,
        "hata": hata,
        "output_path": output_path,
    }
    return agent_info


def run_swarm(goal: str, sub_goals: Optional[List[str]] = None) -> Dict:
    """Tüm swarm'ı çalıştır: parçala, spawn et, sonuçları topla."""
    plan = decompose_task(goal, sub_goals)
    agent_results = []
    for task in plan["alt_gorevler"]:
        task["durum"] = "calisiyor"
        result = spawn_sub_agent(task)
        agent_results.append(result)
        task["durum"] = "tamamlandi" if result["basarili"] else "hata"
    basarili = sum(1 for r in agent_results if r["basarili"])
    return {"swarm_id": plan["swarm_id"], "goal": goal, "alt_gorev_sayisi": len(agent_results),
            "basarili": basarili, "basarisiz": len(agent_results) - basarili, "agentler": agent_results,
            "timestamp": datetime.now(TZ).isoformat()}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Swarm Orchestrator")
    sub = parser.add_subparsers(dest="command")
    p = sub.add_parser("run")
    p.add_argument("goal", type=str)
    p.add_argument("-t", "--tasks", nargs="*")
    p2 = sub.add_parser("decompose")
    p2.add_argument("goal", type=str)
    args = parser.parse_args()
    if args.command == "run":
        r = run_swarm(args.goal, args.tasks)
        print(f"🐝 SWARM CALISTIRILDI: {r['alt_gorev_sayisi']} agent, {r['basarili']} basarili")
    elif args.command == "decompose":
        plan = decompose_task(args.goal)
        print(f"📋 GOREV PARCALAMA: {len(plan['alt_gorevler'])} alt gorev")
    else:
        parser.print_help()
