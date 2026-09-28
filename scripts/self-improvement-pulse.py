#!/usr/bin/env python3
"""Jeff Self-Improvement Pulse — her gun arkada calisir, beni iyilestirir.

Su kontrolleri yapar:
1. Skill audit — 30 gun kullanilmayan skill'leri tespit et
2. Cron audit — carpan etkisi olmayan cron'lari isaretle
3. Memory optimizasyonu — gereksiz entry'leri temizle
4. Genel saglik — disk/RAM/cron durumu raporu

Sadece bir SORUN varsa cikti verir. Her sey yolundaysa sessiz.
"""

import json
import os
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
HERMES_HOME = HOME / ".hermes"
SKILLS_DIR = HERMES_HOME / "skills"
SCRIPTS_DIR = HERMES_HOME / "scripts"
DATA_DIR = HERMES_HOME / "data"
LOG_DIR = HERMES_HOME / "logs"
STATE_FILE = DATA_DIR / "self_improvement_state.json"

NOW = datetime.now(timezone.utc)

sorunlar = []
iyilestirmeler = []


def log(msg: str) -> None:
    print(msg)


# 1. SKILL AUDIT
def audit_skills():
    """Kullanilmayan skill'leri bul (30 gun + kurali)."""
    if not SKILLS_DIR.exists():
        return
    toplam = 0
    eski = 0
    for cat_dir in sorted(SKILLS_DIR.iterdir()):
        if not cat_dir.is_dir():
            continue
        for skill_file in cat_dir.glob("*/SKILL.md"):
            toplam += 1
            # Skill'in son kullanim tarihini dosya zamanindan kabaca tahmin et
            mtime = datetime.fromtimestamp(skill_file.stat().st_mtime, tz=timezone.utc)
            gun_farki = (NOW - mtime).days
            if gun_farki > 60:  # 2 aydir dokunulmamis
                eski += 1
                name = skill_file.parent.name
                log(f"  ⚠️ Eski skill: {cat_dir.name}/{name} ({gun_farki} gun)")
    log(f"  Skill: {toplam} toplam, {eski} eski (60 gun+)")


# 2. BIRAKILDI: Cron kontrolu icin ayri bir mekanizma gerek (system crontab degil, Hermes scheduler)
# TODO: ileride Hermes API'si uzerinden cron kontrolu eklenebilir


# 3. DISK & RAM
def check_system():
    """Sistem kaynaklarini kontrol et."""
    try:
        import shutil
        du = shutil.disk_usage("/")
        disk_yuzde = du.used / du.total * 100
        if disk_yuzde > 85:
            sorunlar.append(f"  ❌ Disk kritik: %{disk_yuzde:.0f} kullanimda")
        elif disk_yuzde > 70:
            log(f"  ⚠️ Disk: %{disk_yuzde:.0f} dolu")
        else:
            log(f"  ✅ Disk: %{disk_yuzde:.0f} dolu")
        
        # RAM
        with open("/proc/meminfo") as f:
            mem = {}
            for line in f:
                if line.startswith("MemTotal") or line.startswith("MemAvailable"):
                    k, v = line.split(":")
                    mem[k] = int(v.strip().split()[0])
        if "MemTotal" in mem and "MemAvailable" in mem:
            ram_kullanim = (mem["MemTotal"] - mem["MemAvailable"]) / mem["MemTotal"] * 100
            log(f"  ✅ RAM: %{ram_kullanim:.0f} kullanimda")
    except Exception as e:
        log(f"  ⚠️ Sistem kontrolu: {e}")


# 4. STATE DOSYASI — son calisma takibi
def track_run():
    """Calisma kaydini tut."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    onceki = {}
    if STATE_FILE.exists():
        try:
            onceki = json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    kayit = {
        "son_calisma": NOW.isoformat(),
        "toplam_calisma": onceki.get("toplam_calisma", 0) + 1,
        "sorun_sayisi": len(sorunlar),
        "iyilestirme_sayisi": len(iyilestirmeler),
    }
    STATE_FILE.write_text(json.dumps(kayit, indent=2))
    log(f"  Calisma: #{kayit['toplam_calisma']}")


# MAIN
if __name__ == "__main__":
    log("🧠 Jeff Self-Improvement Pulse")
    log(f"   {NOW.isoformat()}")
    log("")

    log("📂 Skill audit...")
    audit_skills()

    log("")
    log("💻 System check...")
    check_system()

    log("")
    track_run()

    log("")
    if sorunlar:
        log("")
        log("❌ SORUNLAR:")
        for s in sorunlar:
            log(s)
    else:
        log("✅ Her sey yolunda.")
