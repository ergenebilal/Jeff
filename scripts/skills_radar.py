#!/usr/bin/env python3
"""
Skills Radar v2 — Hermes'in kendini modifiye etme sistemi.
X'te, GitHub'da sürekli tarar, mevcut yeteneklerle karşılaştırır,
eksik/üstün alternatif bulursa raporlar.

Her sabah 06:30'da çalışır. Sadece değişiklik varsa rapor verir.
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# --- CONFIG ---
HERMES_HOME = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")))
SKILLS_DIR = HERMES_HOME / "skills"
RADAR_STATE_FILE = HERMES_HOME / "radar_state.json"
LLM_PROVIDER_API_KEY = os.environ.get("LLM_PROVIDER_API_KEY", "")

# Known platforms/skills we already have (to avoid false positives)
KNOWN_CAPABILITIES = {
    "mcp": ["time", "fetch", "filesystem", "git", "sequential-thinking", "mnemosyne"],
    "memory": ["mnemosyne", "postgresql-memory", "chromadb"],
    "search": ["web_search", "web_extract", "tavily", "exa"],
    "code_exec": ["terminal", "execute_code", "python", "browser"],
    "browser": ["browser_navigate", "browser_click", "browser_vision", "playwright"],
    "media": ["fal-ai", "nanoclaw", "manim", "remotion"],
    "communication": ["telegram", "send_message", "x-api", "gmail", "google"],
    "monitoring": ["beszel", "cronjob", "dashboard"],
    "framework": ["gsd", "prism", "agentic-os", "ecc", "skill_manage"],
    "data": ["crawl4ai", "scraper", "document", "postgresql"],
}

# Skip these mega-repos (not gaps, just well-known platforms)
SKIP_LIST = {
    "n8n-io/n8n", "Significant-Gravitas/AutoGPT", "langchain-ai/langchain",
    "langchain-ai/langgraph", "run-llama/llama_index", "microsoft/autogen",
    "comfyanonymous/ComfyUI", "AUTOMATIC1111/stable-diffusion-webui",
    "openai/whisper", "deepseek-ai/DeepSeek-V3", "deepseek-ai/DeepSeek-R1",
    "meta-llama/llama-models", "huggingface/transformers",
    "tensorflow/tensorflow", "pytorch/pytorch",
    "home-assistant/core", "yt-dlp/yt-dlp",
    "public-apis/public-apis",
    "ggml-org/llama.cpp", "open-webui/open-webui",
    "All-Hands-AI/OpenHands", "langgenius/dify",
    "getcursor/cursor", "anthropics/anthropic-cookbook",
    "n8n-io/n8n-hadron", "makeplane/plane",
    "supabase/supabase", "appwrite/appwrite",
    "nocodb/nocodb", "directus/directus",
    "calcom/cal.com", "twentyhq/twenty",
    "appsmithorg/appsmith", "tabler/tabler",
    "wg-easy/wg-easy", "jellyfin/jellyfin",
}

# High-priority keywords — these directly match Hermes improvement areas
PRIORITY_KEYWORDS = {
    "mcp-server": "MCP Server",
    "claude-code": "Claude Code Plugin",
    "claude-plugin": "Claude Code Plugin",
    "ai-agent": "AI Agent Framework",
    "autonomous-agent": "Otonom Agent",
    "agent-framework": "Agent Framework",
    "tool-calling": "Tool Calling",
    "code-execution": "Kod Çalıştırma",
    "sandbox": "Kod Sandbox",
    "browser-agent": "Browser Agent",
    "web-agent": "Web Agent",
    "llm-tool": "LLM Tool",
    "memory-system": "Hafıza Sistemi",
    "rag": "RAG/Knowledge",
    "vector-database": "Vektör DB",
    "knowledge-graph": "Knowledge Graph",
    "image-generation": "Görsel Üretim",
    "video-generation": "Video Üretim",
    "voice-cloning": "Ses Klonlama",
    "tts": "Text-to-Speech",
    "stt": "Speech-to-Text",
    "whatsapp-bot": "WhatsApp Bot",
    "telegram-bot": "Telegram Bot",
    "discord-bot": "Discord Bot",
    "slack-bot": "Slack Bot",
    "data-scraper": "Veri Kazıma",
    "document-parser": "Doküman İşleme",
    "monitoring": "İzleme",
    "observability": "Gözlemlenebilirlik",
    "cost-tracking": "Maliyet Takibi",
    "prompt-engineering": "Prompt Mühendisliği",
    "prompt-injection": "Prompt Injection",
    "security-scan": "Güvenlik Tarama",
    "code-review": "Kod İnceleme",
}


def get_skills_inventory():
    """Read available skills from local dirs + bundled manifest."""
    local_skills = {}
    
    # 1. Local SKILL.md files
    if SKILLS_DIR.exists():
        for skill_dir in SKILLS_DIR.iterdir():
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    content = skill_file.read_text(errors="replace")
                    desc = ""
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 2:
                            for line in parts[1].strip().split("\n"):
                                if line.startswith("description:"):
                                    desc = line.split(":", 1)[1].strip().strip('"')
                                    break
                    local_skills[skill_dir.name] = desc
    
    # 2. Bundled manifest (hub skills)
    manifest_file = SKILLS_DIR / ".bundled_manifest"
    if manifest_file.exists():
        try:
            content = manifest_file.read_text(errors="replace")
            for line in content.strip().split("\n"):
                if ":" in line and not line.startswith("#"):
                    parts = line.split(":", 1)
                    name = parts[0].strip()
                    if name and name not in local_skills:
                        local_skills[name] = "(hub)"
        except Exception:
            pass
    
    return local_skills


def load_radar_state():
    """Load previous radar state for change detection."""
    if RADAR_STATE_FILE.exists():
        try:
            return json.loads(RADAR_STATE_FILE.read_text())
        except Exception:
            return {}
    return {}


def save_radar_state(state):
    """Save radar state."""
    RADAR_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def call_grok(prompt, system="Sen bir teknoloji dedektifisin."):
    """Call Grok via harici LLM provider for trend analysis."""
    if not LLM_PROVIDER_API_KEY:
        return None
    
    import urllib.request
    import urllib.error

    data = json.dumps({
        "model": "x-ai/grok-4.20",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 1200,
        "temperature": 0.3,
    }).encode()

    req = urllib.request.Request(
        "https://harici-provider.ai/api/v1/chat/completions",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LLM_PROVIDER_API_KEY}",
            "HTTP-Referer": "https://ergeneai.xyz",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            result = json.loads(resp.read())
            if "choices" in result:
                return result["choices"][0]["message"]["content"]
    except Exception:
        return None
    return None


def scan_github_trending():
    """Scan GitHub for trending repos in AI/tool space."""
    findings = []
    
    queries = [
        # MCP & Agent tools
        ("topic:mcp-server", "mcp-server"),
        ("topic:ai-agent+language:python", "ai-agent"),
        ("topic:autonomous-agent", "autonomous-agent"),
        ("topic:claude-code", "claude-code"),
        ("topic:tool-calling", "tool-calling"),
        # Memory & Knowledge
        ("topic:rag+sort:stars", "rag"),
        ("topic:vector-database+sort:stars", "vector-database"),
        ("topic:knowledge-graph+sort:stars", "knowledge-graph"),
        # Browser & Web
        ("topic:browser-automation+sort:stars", "browser-automation"),
        ("topic:web-scraper+sort:stars", "web-scraper"),
        # Media
        ("topic:image-generation+sort:stars", "image-generation"),
        ("topic:video-generation+sort:stars", "video-generation"),
        # Communication
        ("topic:whatsapp-bot+sort:stars", "whatsapp-bot"),
        ("topic:telegram-bot+sort:stars", "telegram-bot"),
        # Security
        ("topic:prompt-injection+sort:stars", "prompt-injection"),
        # Code
        ("topic:sandbox+sort:stars", "sandbox"),
        ("topic:code-execution+sort:stars", "code-execution"),
    ]

    for query, tag in queries:
        try:
            result = subprocess.run(
                ["curl", "-s",
                 f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=3",
                 "-H", "Accept: application/vnd.github.v3+json",
                 "--max-time", "8"],
                capture_output=True, text=True, timeout=12
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if "items" in data:
                    for repo in data["items"][:3]:
                        findings.append({
                            "tag": tag,
                            "name": repo.get("full_name", ""),
                            "description": (repo.get("description") or "")[:200],
                            "stars": repo.get("stargazers_count", 0),
                            "url": repo.get("html_url", ""),
                            "language": repo.get("language", ""),
                        })
        except Exception:
            continue

    return findings


def analyze_x_trends():
    """Use Grok to analyze X trends for new tools in our space."""
    prompt = """Son 30 günde AI agent, MCP server, LLM tool, coding assistant kategorilerinde:

1. Çıkan YENİ araçlar neler? (isim + kısa açıklama — sadece gerçekten yeni olanlar)
2. Hangi mevcut araçların yerini alacak alternatifler/better alternatifler çıktı?
3. Özellikle Claude Code alternatifleri çıktı mı?
4. Daha iyi code execution/sandbox araçları çıktı mı?
5. Daha iyi memory/knowledge management araçları çıktı mı?

CEVAP FORMATI (sadece JSON, başka metin yok):
{
  "new_tools": [{"name": "...", "description": "..."}],
  "alternatives": [{"old_tool": "...", "new_tool": "...", "why_better": "..."}],
  "claude_alternatives": [{"name": "...", "how": "..."}],
  "notable_mentions": ["..."]
}

Hiçbir şey yoksa: {"empty": true}"""

    result = call_grok(prompt)
    if result and result.strip():
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
    return None


def classify_finding(finding, current_skills_set):
    """Classify a finding: gap, upgrade, or known."""
    name = finding.get("name", "").lower()
    desc = finding.get("description", "").lower()
    stars = finding.get("stars", 0)
    tag = finding.get("tag", "")
    
    # Skip if too obscure
    if stars < 100:
        return None, None
    
    # Skip known mega-projects
    if name in SKIP_LIST:
        return None, None
    
    # Extract short name (after last /)
    short_name = name.split("/")[-1] if "/" in name else name
    short_name_clean = short_name.replace("-", "_").replace(" ", "_")
    
    # Check if we already have this exact tool
    if short_name_clean in current_skills_set:
        return None, None
    
    # Check for partial matches (potential upgrade)
    for skill_name in current_skills_set:
        skill_clean = skill_name.lower().replace("-", "_").replace(" ", "_")
        # Check key overlap
        if len(short_name_clean) > 4 and (short_name_clean in skill_clean or skill_clean in short_name_clean):
            return "upgrade", {
                "current_skill": skill_name,
                "alternative": finding,
                "reason": f"Benzer yetenek, ⭐{stars} yıldızlı alternatif",
            }
    
    # Classify gap by tag/category
    category = "Diğer"
    if tag in PRIORITY_KEYWORDS:
        category = PRIORITY_KEYWORDS[tag]
    else:
        # Try keyword matching from description
        for kw, cat in PRIORITY_KEYWORDS.items():
            if kw in desc or kw in tag:
                category = cat
                break
    
    # Check if really new or just a tool similar to something we have
    for known_list in KNOWN_CAPABILITIES.values():
        for known in known_list:
            if known.lower() in short_name_clean or known.lower() in desc[:80]:
                return None, None
    
    return "gap", {
        "category": category,
        "finding": finding,
        "stars": stars,
    }


def format_report(gaps, upgrades, x_data):
    """Format structured radar report."""
    if not gaps and not upgrades and not x_data:
        return None
    
    parts = ["📡 *Skills Radar — Güncelleme*\n"]
    now = datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")
    parts.append(f"🕐 *{now}*\n")
    
    if gaps:
        # Group by category
        by_cat = {}
        for g in gaps:
            cat = g["category"]
            if cat not in by_cat:
                by_cat[cat] = []
            by_cat[cat].append(g)
        
        parts.append(f"*🔍 Keşfedilen Yeni Araçlar:*\n")
        for cat, items in sorted(by_cat.items()):
            parts.append(f"**{cat}** ({len(items)} tane):")
            for item in items[:3]:
                f = item["finding"]
                parts.append(f"  • [{f['name']}]({f['url']}) ⭐{item['stars']}")
                if f.get("description"):
                    desc = f["description"][:100]
                    parts.append(f"    _{desc}_")
            if len(items) > 3:
                parts.append(f"    +{len(items)-3} daha...")
            parts.append("")
    
    if upgrades:
        parts.append(f"*⚡ Yükseltme Potansiyeli:*\n")
        for up in upgrades[:5]:
            f = up["alternative"]
            parts.append(f"• `{up['current_skill']}` → [{f['name']}]({f['url']}) ⭐{f['stars']}")
            parts.append(f"  _{up['reason']}_")
        parts.append("")
    
    if x_data:
        if "new_tools" in x_data and x_data["new_tools"]:
            parts.append("*📡 X'te Konuşulan Yeni Araçlar:*")
            for tool in x_data["new_tools"][:4]:
                parts.append(f"• **{tool.get('name', '?')}** — {tool.get('description', '')}")
            parts.append("")
        
        if "alternatives" in x_data and x_data["alternatives"]:
            parts.append("*🔄 Alternatif Önerileri:*")
            for alt in x_data["alternatives"][:3]:
                parts.append(f"• `{alt.get('old_tool','?')}` → `{alt.get('new_tool','?')}`")
                parts.append(f"  _{alt.get('why_better', '')}_")
            parts.append("")
        
        if "claude_alternatives" in x_data and x_data["claude_alternatives"]:
            parts.append("*🤖 Claude/Codex Alternatifleri:*")
            for ca in x_data["claude_alternatives"]:
                parts.append(f"• **{ca.get('name', '?')}** — {ca.get('how', '')}")
            parts.append("")
    
    parts.append("*⚙️ Ne yapabilirim:*")
    if gaps:
        parts.append("• 📥 Yeni skill olarak **ekleyebilirim** (onayla)")
    if upgrades:
        parts.append("• 🔄 Mevcut skill'i **güncelleyebilirim** (onayla)")
    if len(gaps) + len(upgrades) == 0:
        parts.append("• Şu an için yeni bir şey yok, takipteyim")
    
    return "\n".join(parts)


def diff_state(old, new):
    """Check if anything important changed between states."""
    if not old:
        return True
    
    old_gaps = {g.get("name", "") for g in old.get("gaps", [])}
    new_gaps = {g.get("name", "") for g in new.get("gaps", [])}
    if new_gaps - old_gaps:
        return True
    
    if len(new.get("upgrades", [])) > len(old.get("upgrades", [])):
        return True
    
    return False


def main():
    """Main radar execution."""
    skills = get_skills_inventory()
    all_skill_names = set(skills.keys())
    current_names_lower = {s.lower().replace("-", "_").replace(" ", "_") for s in all_skill_names}
    
    old_state = load_radar_state()
    
    # Scan GitHub
    findings = scan_github_trending()
    
    # Analyze X trends
    x_data = analyze_x_trends()
    
    # Classify each finding
    gaps = []
    upgrades = []
    seen_names = set()
    
    for f in findings:
        name = f.get("name", "")
        if name in seen_names:
            continue
        seen_names.add(name)
        
        result_type, result_data = classify_finding(f, current_names_lower)
        if result_type == "gap":
            gaps.append(result_data)
        elif result_type == "upgrade":
            upgrades.append(result_data)
    
    # Sort gaps by stars
    gaps.sort(key=lambda x: x["stars"], reverse=True)
    gaps = gaps[:15]
    upgrades = upgrades[:8]
    
    # Build state for comparison
    new_state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "skill_count": len(skills),
        "scan_count": len(findings),
        "gaps": [{"name": g["finding"]["name"], "category": g["category"], "stars": g["stars"]} for g in gaps],
        "upgrades": [{"current": u["current_skill"], "alt": u["alternative"]["name"]} for u in upgrades],
    }
    
    # Only report if something changed
    if not diff_state(old_state, new_state):
        print("[SILENT]")
        save_radar_state(new_state)
        return
    
    save_radar_state(new_state)
    
    report = format_report(gaps, upgrades, x_data)
    if report:
        print(report)
    else:
        print("[SILENT]")


if __name__ == "__main__":
    main()
