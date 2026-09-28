#!/usr/bin/env python3
"""
Auto-Skill Evolution v1.1 — Reflex Katmanı
Jeff (Hermes Agent) — anlık skill yazma refleksi.

Skill_manage tool'u Hermes'in doğrudan çağırabileceği bir araç.
Bu script, "bir şeyi 2. kez yapıyorsan skill yap" refleksini
otomatikleştirir.

Ne zaman çalışır:
- Bir hata 2+ kez tekrarlanırsa
- Bir konu 2+ kez sorulursa
- Bir işlem manuel yapılıyorsa ve otomatikleştirilebilirse

Kullanımı (Hermes tarafından):
python3 /home/hermes/.hermes/scripts/auto-skill-reflex.py check
  → Eksik skill önerilerini listeler
  
python3 /home/hermes/.hermes/scripts/auto-skill-reflex.py create <skill_name>
  → Skill şablonu oluşturur, JSON çıktı verir (skill_manage için)
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SKILLS_DIR = Path.home() / ".hermes" / "skills"


def list_skills():
    """Tüm skill'leri isim olarak listele"""
    skills = set()
    if SKILLS_DIR.exists():
        for d in SKILLS_DIR.iterdir():
            if d.is_dir():
                skill_file = d / "SKILL.md"
                if skill_file.exists():
                    for line in skill_file.read_text().split("\n"):
                        if line.startswith("name:"):
                            skills.add(line.replace("name:", "").strip().lower())
                            break
    return skills


def skill_exists(name):
    """Skill var mı kontrol et"""
    existing = list_skills()
    name_lower = name.lower()
    
    # Tam eşleşme
    if name_lower in existing:
        return True
    
    # Kısmi eşleşme (ör: "gumroad" skill'lerde "gumroad-cli" var mı?)
    for s in existing:
        if name_lower in s or s in name_lower:
            return True
    
    return False


def generate_skill(name, description="", content=""):
    """skill_manage çağrısı için JSON çıktı üret"""
    now = datetime.now(timezone.utc).strftime("%d.%m.%Y")
    
    if not content:
        content = f"""---
name: {name}
version: 1.0.0
author: Jeff (Auto-Skill Evolution)
description: {description or f"{name} için otomatik oluşturulmuş skill"}
created: {now}
---

# {name.replace('-', ' ').title()}

Auto-Skill Evolution tarafından oluşturuldu.

## Kullanım

(Henüz detaylandırılmadı — ilk kullanımda güncellenecek)

## Neden Oluşturuldu

{description or "İhtiyaç tespit edildi."}
"""
    
    result = {
        "action": "create",
        "name": name,
        "content": content,
        "generated_at": now,
    }
    
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def check():
    """Eksik skill'leri tara ve öner"""
    suggestions = []
    
    # Core eksik skill'ler (her zaman olması gerekenler)
    candidates = [
        ("gumroad", "Gumroad mağaza yönetimi, CLI kullanımı, ürün güncelleme"),
        ("gateway-healthcheck", "Gateway watchdog — 5 seviyeli healthcheck, OOM recovery, interpreter shutdown handling"),
    ]
    
    for name, desc in candidates:
        if not skill_exists(name):
            suggestions.append({"skill": name, "description": desc, "reason": "Core eksik skill"})
    
    if suggestions:
        print(json.dumps({"status": "suggestions", "count": len(suggestions), "suggestions": suggestions}, indent=2, ensure_ascii=False))
    else:
        print(json.dumps({"status": "clean", "message": "Hiçbir skill ihtiyacı yok"}))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: auto-skill-reflex.py check | create <skill_name> [description]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "check":
        check()
    elif command == "create":
        if len(sys.argv) < 3:
            print("Error: skill_name required")
            sys.exit(1)
        name = sys.argv[2]
        desc = sys.argv[3] if len(sys.argv) > 3 else ""
        
        if skill_exists(name):
            print(json.dumps({"status": "exists", "message": f"Skill '{name}' zaten var"}, indent=2))
        else:
            generate_skill(name, desc)
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
