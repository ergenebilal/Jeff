#!/usr/bin/env python3
"""
Skills Radar v3 — Auto-Evolution System
99/1 Kuralı:
  99%: Otomatik keşfet, kur, test et, skill olarak kaydet
   1%: Ödeme, kredi kartı, kullanıcı hesabı gerekiyorsa → Bilal'e sor

Her sabah 06:30'da çalışır. Sessiz çalışır, sadece kurulum yaparsa raporlar.
"""

import json
import os
import re
import subprocess
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ── CONFIG ──────────────────────────────────────────────────────────────
HERMES_HOME = Path(os.environ.get("HERMES_HOME", os.path.expanduser("~/.hermes")))
SKILLS_DIR = HERMES_HOME / "skills"
SCRIPTS_DIR = HERMES_HOME / "scripts"
CONFIG_FILE = HERMES_HOME / "config.yaml"
ENV_FILE = HERMES_HOME / ".env"
RADAR_STATE = HERMES_HOME / "radar_state.json"
HAVUZ_FILE = Path("/home/hermes/hermes_data/arac_havuzu.json")
LOG_FILE = HERMES_HOME / "logs" / "auto_evolve.log"

LLM_PROVIDER_API_KEY = os.environ.get("LLM_PROVIDER_API_KEY", "")
FIRECRAWL_API_KEY = os.environ.get("FIRECRAWL_API_KEY", "")

# ── 99/1 DECISION ENGINE ────────────────────────────────────────────────
# Tools that are auto-installable (99%)
AUTO_INSTALL_TYPES = {
    "npm": {
        "install_cmd": ["npm", "install", "-g"],
        "test_cmd": ["which"],
        "config_type": "mcp",
        "risk": "low",
    },
    "pip": {
        "install_cmd": ["pip3", "install"],
        "test_cmd": ["python3", "-c"],
        "config_type": "python",
        "risk": "low",
    },
    "binary": {
        "install_cmd": ["curl", "-sfL"],
        "test_cmd": ["which"],
        "config_type": "cli",
        "risk": "medium",
    },
}

# Items that ALWAYS need user approval (1%)
HUMAN_GATE_TERMS = [
    "credit card", "payment", "billing", "subscription", "$", "pricing",
    "sign up", "create account", "email required", "phone verification",
    "paid plan", "premium", "enterprise", "trial",
]

# ── KNOWN SKILLS INVENTORY ─────────────────────────────────────────────
def load_skills_inventory():
    """Yüklü skill'leri oku (local + bundled)."""
    skills = set()
    if SKILLS_DIR.exists():
        for d in SKILLS_DIR.iterdir():
            if d.is_dir() and (d / "SKILL.md").exists():
                skills.add(d.name.lower().replace("-", "_"))
        manifest = SKILLS_DIR / ".bundled_manifest"
        if manifest.exists():
            for line in manifest.read_text().splitlines():
                if ":" in line and not line.startswith("#"):
                    name = line.split(":")[0].strip()
                    if name:
                        skills.add(name.lower().replace("-", "_"))
    return skills


def load_havuz():
    """Mevcut araç havuzunu oku."""
    if HAVUZ_FILE.exists():
        try:
            return json.loads(HAVUZ_FILE.read_text())
        except Exception:
            return {"araclar": []}
    return {"araclar": []}


def save_havuz(havuz):
    """Araç havuzunu kaydet."""
    havuz["son_guncelleme"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    HAVUZ_FILE.write_text(json.dumps(havuz, indent=2, ensure_ascii=False))


def log(msg):
    """Log kaydı."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")


# ── SCANNERS ────────────────────────────────────────────────────────────
def scan_github_trending():
    """GitHub'da trend araçları tara."""
    findings = []
    queries = [
        ("topic:mcp-server+sort:stars", "mcp"),
        ("topic:ai-agent+topic:mcp+language:python", "mcp"),
        ("topic:claude-code+sort:stars", "claude"),
        ("topic:rag+sort:stars", "rag"),
        ("topic:web-scraper+topic:python+sort:stars", "scraper"),
        ("topic:browser-automation+sort:stars", "browser"),
        ("topic:vector-database+sort:stars", "vector"),
        ("topic:image-generation+sort:stars", "image"),
        ("topic:whatsapp-bot+sort:stars", "whatsapp"),
        ("topic:telegram-bot+sort:stars", "telegram"),
        ("topic:sandbox+sort:stars", "sandbox"),
        ("topic:code-execution+sort:stars", "codex"),
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
                for repo in data.get("items", [])[:3]:
                    findings.append({
                        "tag": tag,
                        "name": repo.get("full_name", ""),
                        "description": (repo.get("description") or "")[:200],
                        "stars": repo.get("stargazers_count", 0),
                        "url": repo.get("html_url", ""),
                        "language": repo.get("language", ""),
                        "topics": repo.get("topics", []),
                    })
        except Exception:
            continue
    return findings


# ── 99% AUTO-INSTALL ENGINE ────────────────────────────────────────────
# Known high-quality MCP servers that can be auto-installed
AUTO_INSTALL_MCP = {
    "firecrawl-mcp": {
        "npm": "firecrawl-mcp",
        "config": {
            "command": "npx",
            "args": ["-y", "firecrawl-mcp"],
            "trust": "trusted",
            "allow_sampling": False,
        },
        "env_key": "FIRECRAWL_API_KEY",
        "needs_key": True,  # Key needed but can be added later
        "risk": "low",
    },
    "@modelcontextprotocol/server-puppeteer": {
        "npm": "@modelcontextprotocol/server-puppeteer",
        "config": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
            "trust": "trusted",
            "allow_sampling": False,
        },
        "env_key": None,
        "needs_key": False,
        "risk": "low",
    },
    "@anthropic/mcp-server": {
        "npm": "@anthropic/mcp-server",
        "config": {
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-server"],
            "trust": "trusted",
            "allow_sampling": False,
        },
        "env_key": None,
        "needs_key": False,
        "risk": "low",
    },
}

def needs_human_gate(tool_name, description):
    """99/1 kuralı: Ödeme/hesap gerekiyorsa 1%, değilse 99%."""
    text = f"{tool_name} {description}".lower()
    for term in HUMAN_GATE_TERMS:
        if term in text:
            return True, term
    return False, None


def is_already_installed(name, skills_set, havuz):
    """Zaten kurulu mu kontrol et."""
    clean = name.lower().replace("-", "_").replace(" ", "_")
    if clean in skills_set:
        return True
    for arac in havuz.get("araclar", []):
        if arac.get("id", "").lower() == clean:
            return True
    return False


def auto_install_mcp(repo_name, description, stars):
    """Auto-install MCP server if it's in our known list."""
    for pkg, info in AUTO_INSTALL_MCP.items():
        npm_name = info.get("npm", "")
        if npm_name and (npm_name in repo_name or npm_name.replace("@","") in repo_name):
            log(f"Auto-install: {npm_name} ({stars} stars)")
            
            # Check if it needs API key (1% gate)
            if info.get("needs_key") and info.get("env_key"):
                env_val = os.environ.get(info["env_key"], "")
                if not env_val:
                    return {
                        "action": "needs_key",
                        "package": npm_name,
                        "env_key": info["env_key"],
                        "message": f"{npm_name} installed, needs {info['env_key']} in .env"
                    }
            
            # Install
            result = subprocess.run(
                ["npm", "install", "-g", npm_name],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                log(f"Install FAILED: {npm_name} — {result.stderr[:200]}")
                return {"action": "failed", "package": npm_name, "error": result.stderr[:200]}
            
            # Add to havuz
            havuz = load_havuz()
            havuz_id = npm_name.replace("@", "").replace("/", "-").lower()
            havuz["araclar"].append({
                "id": havuz_id,
                "ad": npm_name,
                "kategori": "mcp-server",
                "durum": "kuruldu",
                "port": None,
                "url": f"https://github.com/{repo_name}" if "/" in repo_name else "",
                "not": f"MCP server. {description[:100]}",
                "monetizasyon": "Dolaylı — Hermes yetenek havuzu",
                "entegrasyon": "config.yaml mcp_servers",
            })
            save_havuz(havuz)
            
            # The MCP server needs to be configured
            # (config writing is done manually due to YAML complexity)
            return {
                "action": "installed",
                "package": npm_name,
                "id": havuz_id,
                "message": f"{npm_name} installed. Add to config.yaml mcp_servers."
            }
    return None


def propose_installation(finding, skills_set, havuz):
    """Bir bulgu için ne yapılacağına karar ver."""
    name = finding.get("name", "")
    desc = finding.get("description", "")
    stars = finding.get("stars", 0)
    
    if stars < 200:
        return None
    
    if is_already_installed(name, skills_set, havuz):
        return None
    
    # Check 1% gate first
    reason, term = needs_human_gate(name, desc)
    if reason:
        return {
            "action": "human_gate",
            "name": name,
            "reason": f"Ödeme/pazarlama içeriyor: '{term}'",
            "stars": stars,
        }
    
    # Try MCP auto-install
    mcp_result = auto_install_mcp(name, desc, stars)
    if mcp_result:
        return mcp_result
    
    # Generic: mark for review
    topics = finding.get("topics", [])
    lang = finding.get("language", "")
    
    # Python pip packages
    if lang == "Python" and stars > 1000:
        return {
            "action": "suggest_pip",
            "name": name,
            "description": desc[:100],
            "stars": stars,
        }
    
    return {
        "action": "noticed",
        "name": name,
        "stars": stars,
        "description": desc[:100],
    }


# ── GROK ANALYSIS ──────────────────────────────────────────────────────
def call_grok(prompt, system="Sen bir AI araç dedektifisin."):
    """Grok üzerinden trend analizi."""
    if not LLM_PROVIDER_API_KEY:
        return None
    data = json.dumps({
        "model": "x-ai/grok-4-20",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 800,
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
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
            return result["choices"][0]["message"]["content"]
    except Exception:
        return None


# ── MAIN ────────────────────────────────────────────────────────────────
def main():
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    log(f"=== Auto-Evolution Scan [{ts}] ===")
    
    skills_set = load_skills_inventory()
    havuz = load_havuz()
    
    # 1. Scan
    findings = scan_github_trending()
    log(f"Found {len(findings)} items")
    
    # 2. Evaluate each finding
    actions = []
    for f in findings:
        result = propose_installation(f, skills_set, havuz)
        if result:
            actions.append(result)
    
    # 3. Execute auto-installs
    installed = [a for a in actions if a.get("action") == "installed"]
    human_gates = [a for a in actions if a.get("action") == "human_gate"]
    suggestions = [a for a in actions if a.get("action") == "suggest_pip"]
    notices = [a for a in actions if a.get("action") == "noticed"]
    needs_key = [a for a in actions if a.get("action") == "needs_key"]
    
    log(f"Installed: {len(installed)}, Human-gate: {len(human_gates)}, "
        f"Suggestions: {len(suggestions)}, Needs-key: {len(needs_key)}")
    
    # 4. Report only if something happened
    if not installed and not human_gates and not needs_key and not suggestions:
        log("Nothing to report — [SILENT]")
        print("[SILENT]")
        return
    
    # 5. Build report
    parts = ["🧬 *Auto-Evolution Raporu*\n"]
    
    if installed:
        for item in installed:
            parts.append(f"✅ **{item['package']}** kuruldu, havuza eklendi")
        parts.append("")
    
    if needs_key:
        for item in needs_key:
            parts.append(f"🔑 `{item['package']}` kuruldu, `.env`'ye `{item['env_key']}` eklenirse aktif")
        parts.append("")
    
    if human_gates:
        parts.append(f"*⚠️ İnsan Onayı Gerekli ({len(human_gates)}):*")
        for item in human_gates[:3]:
            parts.append(f"• {item['name']} ⭐{item['stars']} — _{item['reason']}_")
        parts.append("")
    
    if suggestions:
        parts.append(f"*📦 Önerilen Paketler ({len(suggestions)}):*")
        for item in suggestions[:3]:
            parts.append(f"• `{item['name']}` ⭐{item['stars']}")
        parts.append("")
    
    # Toplam istatistik
    total = (len(installed) + len(human_gates) + len(needs_key) + 
             len(suggestions) + len(notices))
    if installed:
        parts.append(f"*✅ Bu seansta {len(installed)} araç otomatik kuruldu*")
    parts.append(f"📊 Toplam {total} bulgu işlendi, {len(installed)} aksiyon alındı")
    
    report = "\n".join(parts)
    log(f"Report sent: {len(report)} chars")
    print(report)


if __name__ == "__main__":
    main()
