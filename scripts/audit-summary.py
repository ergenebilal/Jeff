#!/usr/bin/env python3
"""Daily audit summary — generates markdown report from audit.log"""
import json
from pathlib import Path
from datetime import datetime, timedelta

audit_log = Path("/opt/hermes/audit/audit.log")
summary = Path("/opt/hermes/audit/daily-summary.md")

if not audit_log.exists():
    summary.write_text("# Audit Summary\n\nNo entries yet.\n")
    exit(0)

lines = audit_log.read_text().strip().split("\n")
entries = []
for l in lines:
    try:
        entries.append(json.loads(l))
    except:
        continue

now = datetime.utcnow()
today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
today_entries = [e for e in entries if e.get("ts", "").startswith(today_start.strftime("%Y-%m-%d"))]
total_entries = len(today_entries)

errors = [e for e in today_entries if e.get("status") == "error"]
tools = {}
for e in today_entries:
    t = e.get("tool", "unknown")
    tools[t] = tools.get(t, 0) + 1

top_tools = sorted(tools.items(), key=lambda x: -x[1])[:10]

md = f"""# Günlük Audit Özeti — {now.strftime('%d.%m.%Y')}

## Genel
- **Toplam aksiyon:** {total_entries}
- **Hata:** {len(errors)}

## En Çok Kullanılan Tool'lar
| Tool | Kullanım |
|------|---------|
"""
for tool, count in top_tools:
    md += f"| {tool} | {count} |\n"

if errors:
    md += "\n## Son Hatalar\n"
    for e in errors[-5:]:
        md += f"- `{e.get('tool')}`: {e.get('error', 'unknown')}\n"

summary.write_text(md)
print(f"Summary written: {total_entries} entries, {len(errors)} errors")
