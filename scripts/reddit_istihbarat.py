#!/usr/bin/env python3
"""Reddit Pazar Istihbarati — Firecrawl ile gunluk Reddit taramasi.

Her sabah 07:30'da calisir. Sessiz mod: sadece onemli firsat varsa raporlar.
"""

import os, sys, json, urllib.request, urllib.error
from datetime import datetime, timezone
from pathlib import Path

FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")
HERMES_HOME = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")))
STATE_FILE = HERMES_HOME / "reddit_state.json"


def load_state():
    if STATE_FILE.exists():
        try: return json.loads(STATE_FILE.read_text())
        except: return {}
    return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def search_reddit(query, limit=5):
    """Firecrawl ile Reddit'te ara."""
    if not FIRECRAWL_API_KEY:
        return []
    data = json.dumps({"query": f"site:reddit.com {query}", "limit": limit}).encode()
    req = urllib.request.Request(
        "https://api.firecrawl.dev/v1/search",
        data=data,
        headers={
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            r = json.loads(resp.read())
            return r.get("data", [])
    except Exception as e:
        return []


def main():
    searches = [
        ("AI customer support small business tool recommendation", "SMB"),
        ("Zendesk Intercom alternative expensive pricing", "rakip kacisi"),
        ("solopreneur AI automation replace hire", "solopreneur"),
        ("AI agent customer service build vs buy", "build-vs-buy"),
        ("best AI tool customer service 2026 worth", "arastirma"),
    ]
    
    state = load_state()
    seen_urls = set(state.get("seen", []))
    
    all_results = []
    for q, tag in searches:
        results = search_reddit(q, limit=3)
        for r in results:
            url = r.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                all_results.append({**r, "tag": tag})
    
    # Save updated state
    state["seen"] = list(seen_urls)[-200:]  # keep last 200
    state["last_run"] = datetime.now(timezone.utc).isoformat()
    save_state(state)
    
    if not all_results:
        print("[SILENT]")
        return
    
    # Group by tag
    by_tag = {}
    for r in all_results:
        tag = r.get("tag", "diger")
        if tag not in by_tag:
            by_tag[tag] = []
        by_tag[tag].append(r)
    
    # Build report
    parts = ["📡 *Reddit Pazar İstihbaratı*\n"]
    
    for tag, items in by_tag.items():
        tag_emoji = {"SMB": "🏪", "rakip kacisi": "💰", "solopreneur": "🧑‍💻", 
                     "build-vs-buy": "🔧", "arastirma": "📊"}.get(tag, "🔍")
        parts.append(f"{tag_emoji} **{tag.upper()}** ({len(items)} yeni):")
        for item in items[:3]:
            title = item.get("title", "?")
            url = item.get("url", "")
            desc = item.get("description", "")[:120]
            parts.append(f"• [{title}]({url})")
            if desc:
                parts.append(f"  _{desc}_")
        parts.append("")
    
    n = len(all_results)
    parts.append(f"📊 Toplam {n} yeni konusma bulundu")
    
    print("\n".join(parts))


if __name__ == "__main__":
    main()
