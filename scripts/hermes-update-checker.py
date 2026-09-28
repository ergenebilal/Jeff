#!/usr/bin/env python3
"""Hermes güncelleme denetleyici — her gün çalışır, güncelleme varsa bildirir."""
import subprocess, json, os, sys
from datetime import datetime, timezone, timedelta

TURKIYE_TZ = timezone(timedelta(hours=3))
NOW = datetime.now(TURKIYE_TZ)

HERMES_DIR = "/opt/hermes"
RESULTS_FILE = os.path.expanduser("~/.hermes/cron/output/hermes-update-checker/")

def log(msg):
    ts = NOW.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}")

try:
    # Fetch latest
    r = subprocess.run(
        ["git", "fetch", "origin"],
        cwd=HERMES_DIR, capture_output=True, text=True, timeout=30
    )
    if r.returncode != 0:
        log(f"Git fetch failed: {r.stderr.strip()}")
        sys.exit(1)

    # Count commits behind
    r2 = subprocess.run(
        ["git", "rev-list", "--count", "HEAD..origin/main"],
        cwd=HERMES_DIR, capture_output=True, text=True, timeout=15
    )
    behind = int(r2.stdout.strip())

    # Current version
    r3 = subprocess.run(
        ["hermes", "--version"],
        capture_output=True, text=True, timeout=15
    )
    version_line = r3.stdout.strip().split("\n")[0] if r3.stdout else "?"

    if behind > 0:
        log(f"GUNCELLEME VAR! {behind} commit geridesin.")
        log(f"Mevcut: {version_line}")
        log(f"Son commit: {r2.stderr[:100] if r2.stderr else 'N/A'}")

        # Otomatik güncelle
        log("Otomatik güncelleme başlatılıyor...")
        
        # Önce checkpoint
        backup_dir = os.path.expanduser(f"~/backups/auto-update-{NOW.strftime('%Y%m%d_%H%M')}")
        os.makedirs(backup_dir, exist_ok=True)
        subprocess.run(["cp", "-r", os.path.expanduser("~/.hermes/config.yaml"), backup_dir], capture_output=True)
        subprocess.run(["cp", "-r", os.path.expanduser("~/.hermes/skills"), f"{backup_dir}/skills"], capture_output=True)
        subprocess.run(["crontab", "-l"], capture_output=True, text=True)

        # Git pull
        r4 = subprocess.run(
            ["git", "pull", "--ff-only", "origin", "main"],
            cwd=HERMES_DIR, capture_output=True, text=True, timeout=60
        )
        if r4.returncode == 0:
            # Reinstall
            subprocess.run(
                ["pip3", "install", "-e", "."],
                cwd=HERMES_DIR, capture_output=True, text=True, timeout=120
            )
            # Restart Hermes
            subprocess.run(["hermes", "restart"], capture_output=True, timeout=30)
            log(f"✅ Güncelleme başarılı! Checkpoint: {backup_dir}")
            
            # Yeni versiyonu oku
            r5 = subprocess.run(["hermes", "--version"], capture_output=True, text=True, timeout=15)
            log(f"Yeni versiyon: {r5.stdout.strip().split(chr(10))[0]}")
            
            print(f"\n[SUMMARY] Hermes güncellendi: {behind} commit ileri alındı. Versiyon: {r5.stdout.strip().split(chr(10))[0]}")
        else:
            log(f"❌ Git pull başarısız: {r4.stderr[:200]}")
            print(f"\n[SUMMARY] Güncelleme var ({behind} commit) ama otomatik merge yapılamadı. Manuel müdahale gerekli.")
    else:
        log("Güncel. Güncelleme yok.")
        print("[SILENT]")

except Exception as e:
    log(f"HATA: {str(e)[:200]}")
    print(f"[SILENT]")
