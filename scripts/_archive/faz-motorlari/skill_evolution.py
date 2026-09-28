#!/usr/bin/env python3
"""Skill Evolution — Eski/eksik skill'leri tespit et, güncelleme öner.
Her gece 01:00'de çalışır.
"""
import os, json
from datetime import datetime

SKILLS_DIR = os.path.expanduser("~/.hermes/skills")
REPORT_FILE = os.path.expanduser("~/.hermes/evolution_report.json")

def scan_skills():
    now = datetime.now()
    updates = []
    
    for root, dirs, files in os.walk(SKILLS_DIR):
        for f in files:
            if f == "SKILL.md":
                path = os.path.join(root, f)
                mtime = os.path.getmtime(path)
                age_days = (now - datetime.fromtimestamp(mtime)).days
                rel_path = os.path.relpath(path, SKILLS_DIR)
                
                if age_days > 30:
                    updates.append({
                        "skill": rel_path,
                        "age_days": age_days,
                        "action": "review"
                    })
                elif age_days > 60:
                    updates.append({
                        "skill": rel_path,
                        "age_days": age_days,
                        "action": "archive"
                    })
    
    report = {
        "time": now.isoformat(),
        "total_skills": len(updates),
        "updates": updates[:10]
    }
    
    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"🔍 {len(updates)} skill taranabilir:")
    for u in updates[:5]:
        print(f"  {u['skill']} ({u['age_days']} gün) → {u['action']}")

if __name__ == "__main__":
    scan_skills()
