#!/usr/bin/env python3
"""Session Memory Cron — Her gece son 24 saatteki konuşmaları özetler
ve önemli bilgileri Memory'e kaydeder.

Çalışma: Her gece 03:00 TR
"""
import json, os, subprocess, sys
from datetime import datetime

MEMORY_LOG = os.path.expanduser("~/.hermes/memory_cron_log.json")
SKILLS_DIR = os.path.expanduser("~/.hermes/skills")

def main():
    print(f"🧠 Session Memory Cron — {datetime.now().isoformat()}")
    
    # 1. Skill audit — 60 gündür güncellenmemiş skill var mı?
    now = datetime.now()
    old_skills = []
    for root, dirs, files in os.walk(SKILLS_DIR):
        for f in files:
            if f == "SKILL.md":
                path = os.path.join(root, f)
                mtime = os.path.getmtime(path)
                age_days = (now - datetime.fromtimestamp(mtime)).days
                if age_days > 60:
                    old_skills.append((path, age_days))
    
    if old_skills:
        print(f"⚠️ Eski skill'ler ({len(old_skills)} adet):")
        for path, age in old_skills[:5]:
            print(f"  - {path} ({age} gün)")
    else:
        print("✅ Tüm skill'ler güncel")
    
    # 2. Cron audit — cron.json dosyasından oku
    cron_file = os.path.expanduser("~/.hermes/cron.json")
    cron_count = 0
    if os.path.exists(cron_file):
        with open(cron_file) as f:
            try:
                cron_data = json.load(f)
                if isinstance(cron_data, list):
                    cron_count = len(cron_data)
                elif isinstance(cron_data, dict):
                    cron_count = len(cron_data.get("jobs", cron_data))
            except:
                pass
    print(f"⏰ Aktif cron sayısı: {cron_count}")
    
    # 3. Disk kontrol
    disk = subprocess.run(
        ["df", "-h", "/", "--output=pcent"],
        capture_output=True, text=True, timeout=5
    )
    disk_pct = disk.stdout.strip().split('\n')[-1].strip()
    print(f"💾 Disk kullanımı: {disk_pct}")
    
    # 4. Memory durumu — dosya bazlı kontrol
    mem_file = os.path.expanduser("~/.hermes/MEMORY.md")
    user_file = os.path.expanduser("~/.hermes/USER.md")
    if os.path.exists(mem_file):
        mem_size = os.path.getsize(mem_file)
        print(f"📝 MEMORY.md: {mem_size} byte")
    if os.path.exists(user_file):
        user_size = os.path.getsize(user_file)
        print(f"👤 USER.md: {user_size} byte")
    
    print("✅ Memory cron tamamlandı")

if __name__ == "__main__":
    main()
