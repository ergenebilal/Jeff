#!/usr/bin/env python3
"""Auto-Tuner — sistem metriklerini izle, iyileştirme fırsatı bul.
Kullanılmayan skill'leri pasife çek, başarısız cron'ları raporla, optimize et."""
import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

sys.path.insert(0, os.path.expanduser("~/.hermes/scripts"))

TUNER_PATH: str = os.path.expanduser("~/.hermes/brain/auto_tuner.json")
TZ: timezone = timezone(timedelta(hours=3))


def _load() -> dict[str, Any]:
    if not os.path.exists(TUNER_PATH):
        return {"son_tuning": None, "metrikler": [], "oneri_gecmisi": []}
    try:
        with open(TUNER_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"son_tuning": None, "metrikler": [], "oneri_gecmisi": []}


def _save(data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(TUNER_PATH), exist_ok=True)
    with open(TUNER_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def collect_metrics() -> dict[str, Any]:
    """Sistem metriklerini topla."""
    metrics: dict[str, Any] = {"tarih": datetime.now(TZ).isoformat()}

    # RAM
    try:
        r = subprocess.run(["free", "-m"], capture_output=True, text=True, timeout=5)
        for line in r.stdout.split("\n"):
            if line.startswith("Mem:"):
                parts = line.split()
                metrics["ram_toplam_mb"] = int(parts[1])
                metrics["ram_kullanilan_mb"] = int(parts[2])
                metrics["ram_yuzde"] = round(int(parts[2]) / int(parts[1]) * 100, 1)
    except Exception:
        metrics["ram_yuzde"] = -1

    return metrics


def check_skills() -> list[dict[str, Any]]:
    """Son 7 günde kullanılmayan skill'leri bul."""
    skills_dir: str = os.path.expanduser("~/.hermes/skills")
    unused: list[dict[str, Any]] = []
    now: float = datetime.now().timestamp()
    yedi_gun: float = 7 * 24 * 3600

    # Skill kullanımını episodic memory'den kontrol et
    ep_path: str = os.path.expanduser("~/.hermes/brain/episodic_memory.jsonl")
    used_skills: set[str] = set()
    if os.path.exists(ep_path):
        try:
            with open(ep_path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        e = json.loads(line)
                        skill = e.get("ilgili_skill", "")
                        if skill:
                            used_skills.add(skill.lower())
                    except json.JSONDecodeError:
                        continue
        except (IOError, json.JSONDecodeError):
            pass

    # skills/ altındaki skill'leri tara
    for root, dirs, files in os.walk(skills_dir):
        for f in files:
            if f == "SKILL.md":
                skill_name: str = os.path.basename(root)
                if skill_name.lower() not in used_skills:
                    mtime: float = os.path.getmtime(os.path.join(root, f))
                    if now - mtime > yedi_gun:
                        unused.append({"skill": skill_name, "son_kullanim": datetime.fromtimestamp(mtime).isoformat()})

    return unused


def check_crons() -> list[dict[str, Any]]:
    """Başarısız cron'ları raporla."""
    # CronJob API'sine erişemiyoruz, shell çıktısına bak
    failed: list[dict[str, Any]] = []
    cron_log: str = os.path.expanduser("~/.hermes/logs/cron_error.log")
    if os.path.exists(cron_log):
        try:
            with open(cron_log) as f:
                for line in f.readlines()[-20:]:
                    if "error" in line.lower() or "fail" in line.lower():
                        failed.append({"log": line.strip(), "tarih": datetime.now(TZ).isoformat()})
        except (IOError, OSError):
            pass
    return failed


def recommend() -> list[str]:
    """İyileştirme önerileri üret."""
    oneriler: list[str] = []

    # RAM kontrol
    metrics: dict[str, Any] = collect_metrics()
    if metrics.get("ram_yuzde", 0) > 80:
        oneriler.append(f"RAM %{metrics['ram_yuzde']} — gereksiz process kill önerilir")

    # Skill kontrol
    unused: list[dict[str, Any]] = check_skills()
    if unused:
        oneriler.append(f"{len(unused)} skill 7+ gündür kullanılmıyor: {', '.join(u['skill'] for u in unused[:3])}")

    # Cron kontrol
    failed: list[dict[str, Any]] = check_crons()
    if failed:
        oneriler.append(f"{len(failed)} cron hatası tespit edildi")

    if not oneriler:
        oneriler.append("Sistem sağlıklı, öneri yok")

    data: dict[str, Any] = _load()
    data["oneri_gecmisi"].append({
        "tarih": datetime.now(TZ).isoformat(),
        "oneriler": oneriler,
    })
    data["oneri_gecmisi"] = data["oneri_gecmisi"][-50:]
    _save(data)

    return oneriler


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "recommend":
        for o in recommend():
            print(f"  {o}")
    elif len(sys.argv) > 1 and sys.argv[1] == "metrics":
        m = collect_metrics()
        print(f"RAM: %{m.get('ram_yuzde', '?')}")
    elif len(sys.argv) > 1 and sys.argv[1] == "unused":
        for u in check_skills():
            print(f"  {u['skill']} — son: {u['son_kullanim'][:10]}")
    else:
        print(f"Kullanım: {sys.argv[0]} [recommend|metrics|unused]")
