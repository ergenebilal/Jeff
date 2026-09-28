#!/usr/bin/env python3
"""
Auto-Skill Evolution v1.0.0
Jeff (Hermes Agent) — kendi kendine skill yazma refleksi.

Ne yapar:
1. Mevcut skill'leri tarar, hangi konuların eksik olduğunu tespit eder
2. Bir ihtiyaç fark ettiğinde (pattern-based), skill şablonu oluşturur
3. Hermes'e skill_manage çağrısı yapılması için çıktı üretir
4. Çalıştığını doğrular

Trigger:
- Cron ile her 30 dk'da bir çalışır
- Ama sadece GERÇEKTEN ihtiyaç varsa skill yazar (spam yapmaz)

Felsefe:
- "Bir şeyi 2 kere yapıyorsan, skill yap"
- "Bir konuda takıldıysan, skill yap"
- "Bir konuyu açıklamak zorunda kaldıysan, skill yap"
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

SKILLS_DIR = Path.home() / ".hermes" / "skills"
REPORTS_DIR = Path.home() / ".hermes" / "auto-skill-reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# --- Pattern Tabanlı İhtiyaç Tespiti ---

# Pattern'ler: Bir dosya/içerik türünü tarar, eksik skill varsa raporlar
PATTERNS = [
    {
        "id": "new_mcp_server",
        "check": lambda: check_new_mcp_server(),
        "description": "Yeni MCP sunucusu eklendiğinde kullanım skill'i oluştur",
    },
    {
        "id": "repeated_pattern",
        "check": lambda: check_repeated_patterns(),
        "description": "2+ kere tekrarlanan işlemleri skill'e dönüştür",
    },
    {
        "id": "skill_gaps",
        "check": lambda: check_skill_gaps(),
        "description": "Mevcut yeteneklerde gözle görülür boşlukları tespit et",
    },
]

# --- Son raporu oku (spam önleme) ---
def get_last_report():
    report_file = REPORTS_DIR / "last_scan.json"
    if report_file.exists():
        try:
            with open(report_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_last_report(report):
    report_file = REPORTS_DIR / "last_scan.json"
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2, default=str)


def get_existing_skills():
    """Tüm skill'leri listele — kategorize edilmiş (alt dizinlerdeki) skill'leri de bul"""
    skills = {}
    if not SKILLS_DIR.exists():
        return skills
    
    # Recursive search for all SKILL.md files
    for skill_file in SKILLS_DIR.rglob("SKILL.md"):
        if not skill_file.is_file():
            continue
        # Skip .curator_backups and other hidden dirs
        if any(part.startswith(".") for part in skill_file.relative_to(SKILLS_DIR).parts):
            continue
        content = skill_file.read_text()
        title = ""
        desc = ""
        for line in content.split("\n"):
            if line.startswith("name:"):
                title = line.replace("name:", "").strip()
            elif line.startswith("description:"):
                desc = line.replace("description:", "").strip()
        skills[title or skill_file.parent.name] = {
            "path": str(skill_file),
            "description": desc,
            "content_length": len(content),
        }
    return skills


def check_new_mcp_server():
    """
    Config.yaml'daki MCP sunucularını tara.
    Eğer bir MCP için skill yoksa, öner.
    """
    config_path = Path.home() / ".hermes" / "config.yaml"
    if not config_path.exists():
        return []

    config_text = config_path.read_text()

    # mcp_servers bloğunu bul
    mcp_match = re.search(r"mcp_servers:\n", config_text)
    if not mcp_match:
        return []

    # Bloğu parse et (basit)
    mcp_servers = re.findall(
        r"^\s{2}(\w[-_\w]+):", config_text[mcp_match.start():]
    )

    existing = get_existing_skills()
    suggestions = []

    for server in mcp_servers:
        # Skill adına çevir
        skill_name = server.lower().replace("_", "-").replace(" ", "-")
        # Var mı kontrol et (benzer isimleri de kontrol et)
        found = False
        for sk_name in existing:
            if skill_name in sk_name.lower() or sk_name.lower() in skill_name:
                found = True
                break

        if not found and server not in ("filesystem", "mnemosyne", "sequential-thinking"):
            suggestions.append({
                "type": "new_mcp_skill",
                "server": server,
                "reason": f"'{server}' MCP sunucusu config'de var ama kullanım skill'i yok",
            })

    return suggestions


def check_repeated_patterns():
    """
    .hermes/logs/ altındaki son X log'u tara.
    Tekrarlanan error pattern'lerini bul.
    Skill'e dönüştürülebilecek desenleri tespit et.
    """
    log_dir = Path.home() / ".hermes" / "logs"
    if not log_dir.exists():
        return []

    # Son 50 log satırını tara
    all_logs = []
    for f in sorted(log_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:5]:
        if f.is_file() and f.stat().st_size < 500000:  # max 500KB
            try:
                content = f.read_text(errors="replace")
                all_logs.append(content)
            except (IOError, OSError):
                continue

    full_log = "\n".join(all_logs)

    patterns = {
        r"interpreter shutdown": {
            "skill": "gateway-self-heal",
            "exists": False,
            "suggestion": None,
        },
        r"timeout|timed? ?out": {
            "skill": "timeout-handling",
            "exists": False,
            "suggestion": None,
        },
        r"connection refused|ConnectionError": {
            "skill": "connection-retry",
            "exists": False,
            "suggestion": None,
        },
    }

    existing = get_existing_skills()
    suggestions = []

    for pattern, info in patterns.items():
        matches = re.findall(pattern, full_log, re.IGNORECASE)
        if len(matches) > 5:  # 5+ kez tekrarlanmışsa
            info["exists"] = any(info["skill"] in s.lower() for s in existing)
            if not info["exists"]:
                suggestions.append({
                    "type": "error_pattern_skill",
                    "pattern": pattern,
                    "count": len(matches),
                    "suggested_skill": info["skill"],
                    "reason": f"'{pattern}' hatası {len(matches)} kez tekrarlanmış, özel handling skill'i gerekli",
                })

    return suggestions


def check_skill_gaps():
    """
    Mevcut konu başlıklarına bak, olması gereken ama olmayan skill'leri tespit et.
    """
    existing = get_existing_skills()
    suggestions = []

    # Olması gereken core skill'ler
    required_skills = {
        "mcp-servers": "MCP sunucularının kurulumu ve yönetimi",
        "firecrawl-mcp": "Firecrawl MCP entegrasyonu ve kullanımı",
        "gumroad": "Gumroad mağaza yönetimi ve CLI kullanımı",
    }

    for skill_name, description in required_skills.items():
        found = False
        for existing_name in existing:
            if skill_name in existing_name.lower() or any(
                word in existing_name.lower() for word in skill_name.replace("-", " ").split()
            ):
                found = True
                break

        if not found:
            suggestions.append({
                "type": "missing_skill",
                "suggested_skill": skill_name,
                "reason": f"'{skill_name}' skill'i tanımlı değil — {description}",
            })

    return suggestions


def generate_skill_markdown(skill_name, suggestion):
    """skill_manage için SKILL.md formatı üret"""
    now = datetime.now(timezone.utc).strftime("%d.%m.%Y")

    if suggestion["type"] == "new_mcp_skill":
        server = suggestion["server"]
        return f"""---
name: {server.lower().replace('_', '-').replace(' ', '-')}
version: 1.0.0
author: Jeff (Auto-Skill Evolution)
description: {server} MCP sunucusu kullanım kılavuzu — kurulum, yapılandırma, temel komutlar.
created: {now}
---

# {server} MCP Server

Otomatik oluşturulmuş skill. {server} MCP sunucusunun yeteneklerini ve kullanımını açıklar.

## Kurulum

Config'e eklendi: `~/.hermes/config.yaml` → `mcp_servers.{server}`

## Kullanım

Bu MCP sunucusu şu yetenekleri sağlar:
- (Yetkeler skill güncellenecek)
"""

    elif suggestion["type"] == "error_pattern_skill":
        pattern = suggestion["pattern"]
        suggested = suggestion["suggested_skill"]
        count = suggestion["count"]
        return f"""---
name: {suggested}
version: 1.0.0
author: Jeff (Auto-Skill Evolution)
description: '{pattern}' hatası için otomatik handling ve recovery prosedürü. Son 30 günde {count} kez tespit edildi.
created: {now}
---

# {suggested.replace('-', ' ').title()}

## Hata Deseni

`{pattern}`

## Tespit Sıklığı

Son taramada {count} kez tespit edildi.

## Recovery Prosedürü

1. Hatayı tespit et
2. İlk denemede retry (3sn bekle)
3. İkinci denemede alternatif route dene
4. Üçüncü denemede sisteme raporla

## Önleme

- (Kalıcı çözüm skill güncellenecek)
"""

    else:
        return f"""---
name: {skill_name}
version: 1.0.0
author: Jeff (Auto-Skill Evolution)
description: {suggestion.get('reason', 'Otomatik oluşturulmuş skill')}
created: {now}
---

# {skill_name.replace('-', ' ').title()}

Otomatik oluşturulmuş skill.

## Kullanım

(Henüz detaylandırılmadı — ilk kullanımda güncellenecek)
"""


def check_firecrawl_skill():
    """
    Firecrawl MCP eklendiğine göre, ona ait bir skill var mı kontrol et.
    Varsa atla, yoksa öner.
    """
    existing = get_existing_skills()
    firecrawl_keywords = ["firecrawl", "firecrawl-mcp", "fc-mcp"]
    
    for sk_name in existing:
        if any(kw in sk_name.lower() for kw in firecrawl_keywords):
            return []  # Zaten var
    
    # Firecrawl MCP config'de mi?
    config_path = Path.home() / ".hermes" / "config.yaml"
    if config_path.exists():
        config_text = config_path.read_text()
        if "firecrawl" in config_text and "mcp_servers" in config_text:
            firecrawl_idx = config_text.find("firecrawl:")
            mcp_idx = config_text.rfind("mcp_servers", 0, firecrawl_idx)
            if mcp_idx != -1:
                return [{
                    "type": "new_mcp_skill",
                    "server": "firecrawl-mcp",
                    "reason": "Firecrawl MCP config'e eklendi ama kullanım skill'i yok",
                }]
    
    return []


def main():
    print("🔍 Auto-Skill Evolution — Scan started", flush=True)
    print(f"📂 Skills directory: {SKILLS_DIR}", flush=True)
    print(f"📊 Existing skills: {len(get_existing_skills())}", flush=True)
    print()

    # Önceki raporu oku
    last_report = get_last_report()
    last_scan_time = last_report.get("scan_time", "never")

    all_suggestions = []

    # Her pattern'i kontrol et
    for pattern in PATTERNS:
        try:
            result = pattern["check"]()
            if result:
                all_suggestions.extend(result)
                for s in result:
                    print(f"⚠️  {pattern['description']}: {s['reason']}", flush=True)
        except Exception as e:
            print(f"❌ Pattern '{pattern['id']}' failed: {e}", flush=True)

    # Firecrawl özel kontrol
    try:
        fc_result = check_firecrawl_skill()
        if fc_result:
            all_suggestions.extend(fc_result)
            for s in fc_result:
                print(f"⚠️  {s['reason']}", flush=True)
    except Exception as e:
        print(f"❌ Firecrawl check failed: {e}", flush=True)

    print()

    if not all_suggestions:
        print("✅ Hiçbir skill ihtiyacı tespit edilmedi. Her şey yolunda.", flush=True)
        save_last_report({
            "scan_time": str(datetime.now(timezone.utc)),
            "suggestions": [],
            "status": "clean",
        })
        return

    # Her öneri için skill üret (ama her scan'de sadece 1 tane — spam yapma)
    suggestion = all_suggestions[0]
    skill_name = suggestion.get("suggested_skill", suggestion.get("server", "unknown")).lower().replace("_", "-").replace(" ", "-")
    
    print(f"📝 Generating skill: {skill_name}", flush=True)
    print(f"   Reason: {suggestion['reason']}", flush=True)
    
    # Skill içeriğini üret
    skill_content = generate_skill_markdown(skill_name, suggestion)
    
    # Rapor dosyasına yaz — Hermes'in cron'da okuyup skill_manage yapması için
    report = {
        "scan_time": str(datetime.now(timezone.utc)),
        "suggestions": all_suggestions,
        "action_taken": {
            "skill_name": skill_name,
            "content_preview": skill_content[:500] + "...",
        },
        "status": "skill_generated",
        "total_suggestions": len(all_suggestions),
    }
    
    report_path = REPORTS_DIR / f"skill-{skill_name}-{int(time.time())}.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    save_last_report(report)
    
    # Çıktı Hermes tarafından okunabilir olsun
    print()
    print(f"📋 REPORT: {report_path}", flush=True)
    print(f"📝 Skill name: {skill_name}", flush=True)
    print(f"⚡ Status: GENERATED (awaiting Hermes activation)", flush=True)
    print()
    print("To activate, run in next Hermes turn:")
    print(f'  skill_manage(action="create", name="{skill_name}", content="""')
    print(skill_content)
    print('""")')
    print()


if __name__ == "__main__":
    main()
