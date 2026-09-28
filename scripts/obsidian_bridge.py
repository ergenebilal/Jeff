#!/usr/bin/env python3
"""Brain v3 ↔ Obsidian Vault Bridge
Session sonunda memory'leri Obsidian formatına senkronize eder.
Haftalık distillation yapar (MEMORY.md → Obsidian Memory/).
"""

import os
import json
import datetime
import subprocess
from pathlib import Path

VAULT = Path.home() / ".hermes" / "obsidian"
MEMORY_SRC = Path.home() / ".hermes" / "memory"

def run(cmd: str) -> str:
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

def log_session():
    """Session log'unu Obsidian Journal'a yaz."""
    today = datetime.datetime.now()
    daily_dir = VAULT / "Journal" / "daily"
    daily_dir.mkdir(parents=True, exist_ok=True)

    date_str = today.strftime("%Y-%m-%d")
    daily_file = daily_dir / f"{date_str}.md"

    # Session'dan önemli satırları topla
    entries = []
    # Memory'den bugün eklenenleri bul
    mem_file = MEMORY_SRC / "memory.md"
    if mem_file.exists():
        content = mem_file.read_text()
        entries.append(f"## Memory\n\n```\n{content[-1000:]}\n```")

    # Cron çıktılarını tara
    cron_dir = Path.home() / ".hermes" / "cron" / "output"
    if cron_dir.exists():
        for f in sorted(cron_dir.glob("*.log"), key=os.path.getmtime, reverse=True)[:3]:
            mtime = datetime.datetime.fromtimestamp(os.path.getmtime(f))
            if mtime.date() == today.date():
                entries.append(f"## Cron: {f.stem}\n\n```\n{Path(f).read_text()[-500:]}\n```")

    with open(daily_file, "a") as f:
        f.write(f"# {date_str}\n\n")
        f.write("\n---\n".join(entries))
        f.write("\n\n")

    return daily_file

def sync_memory_to_obsidian():
    """Hermes memory → Obsidian Memory/ senkronizasyonu."""
    mem_file = MEMORY_SRC / "memory.md"
    if not mem_file.exists():
        return

    obs_mem = VAULT / "Memory" / "agent-memory.md"
    content = mem_file.read_text()
    obs_mem.write_text(content)
    print(f"Synced: memory.md → Memory/agent-memory.md")

def distill_weekly():
    """Haftalık distillation: Memory'leri temizle, önemlileri sakla."""
    weekly_dir = VAULT / "Journal" / "weekly"
    weekly_dir.mkdir(parents=True, exist_ok=True)

    week_num = datetime.datetime.now().isocalendar()[1]
    weekly_file = weekly_dir / f"week-{week_num}.md"

    # Önemli pattern'leri topla
    summary = []
    summary.append(f"# Hafta {week_num} Özeti\n")
    summary.append(f"Tarih: {datetime.datetime.now().strftime('%Y-%m-%d')}\n")

    # Brain v3 decision journal'dan bu haftayı al
    decisions_dir = VAULT / "Memory" / "decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)
    dec_files = sorted(decisions_dir.glob("*.md"), key=os.path.getmtime, reverse=True)
    if dec_files:
        summary.append("## Bu Haftanın Kararları\n")
        for f in dec_files[:5]:
            summary.append(f"- [[decisions/{f.stem}]]")

    weekly_file.write_text("\n".join(summary))
    return weekly_file

def health_check():
    """Vault sağlık kontrolü: kırık wiki-link'leri ve orphan notları bul."""
    import re
    all_files = list(VAULT.rglob("*.md"))
    all_names = {f.stem for f in all_files}
    broken_links = []

    for f in all_files:
        content = f.read_text()
        links = re.findall(r'\[\[([^\]|#]+)', content)
        for link in links:
            if link not in all_names and not (VAULT / f"{link}.md").exists():
                broken_links.append(f"  {f.name} → [[{link}]]")

    if broken_links:
        print("⚠️  Broken wiki-links:")
        for bl in broken_links:
            print(bl)
    else:
        print("✅ All wiki-links valid")

    return len(broken_links) == 0

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sync"

    if cmd == "sync":
        log_session()
        sync_memory_to_obsidian()
        print("✅ Obsidian sync complete")
    elif cmd == "weekly":
        distill_weekly()
        print("✅ Weekly distillation complete")
    elif cmd == "health":
        ok = health_check()
        if not ok:
            sys.exit(1)
    elif cmd == "all":
        log_session()
        sync_memory_to_obsidian()
        distill_weekly()
        health_check()
        print("✅ Full sync complete")
    else:
        print(f"Usage: {sys.argv[0]} [sync|weekly|health|all]")
