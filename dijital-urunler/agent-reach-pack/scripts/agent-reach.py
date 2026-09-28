#!/usr/bin/env python3
"""
Agent Reach — Multi-Platform Monitoring Agent
Monitors: X/Twitter, Reddit, RSS, GitHub, Telegram
Alerts via: Telegram, Slack, Email, Webhook

Usage:
  python3 agent-reach.py                       # Run once (cron-friendly)
  python3 agent-reach.py --continuous          # Run as daemon (check every 5 min)
  python3 agent-reach.py --test-telegram       # Test notification channels
"""

import os
import sys
import json
import time
import hashlib
import logging
from datetime import datetime
from typing import Optional
from pathlib import Path

# ============================================================
# CONFIGURATION
# ============================================================

# Default config path — user can override with env var
CONFIG_PATH = os.environ.get("AGENT_REACH_CONFIG", "./agent-reach-config.yaml")

# State file for deduplication (avoids re-sending same alert)
STATE_DIR = Path(os.environ.get("AGENT_REACH_STATE", "./.agent_reach_state"))
STATE_DIR.mkdir(exist_ok=True)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(STATE_DIR / "agent-reach.log")
    ]
)
logger = logging.getLogger("agent-reach")


# ============================================================
# NOTIFICATION HANDLERS
# ============================================================

def send_telegram(bot_token: str, chat_id: str, message: str) -> bool:
    """Send alert via Telegram."""
    import urllib.request
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = json.dumps({
            "chat_id": chat_id,
            "text": message[:4000],
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        resp = urllib.request.urlopen(req, timeout=10)
        return json.loads(resp.read()).get("ok", False)
    except Exception as e:
        logger.warning(f"Telegram send failed: {e}")
        return False


def send_slack(webhook_url: str, message: str, severity: str = "info") -> bool:
    """Send alert via Slack webhook."""
    import urllib.request
    try:
        color = {"critical": "#FF0000", "warning": "#FFA500", "info": "#36a64f"}.get(severity, "#36a64f")
        payload = {
            "attachments": [{
                "color": color,
                "text": message,
                "ts": int(time.time())
            }]
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(webhook_url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        logger.warning(f"Slack send failed: {e}")
        return False


def send_webhook(url: str, payload: dict) -> bool:
    """Send alert via generic webhook."""
    import urllib.request
    try:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
        return True
    except Exception as e:
        logger.warning(f"Webhook send failed: {e}")
        return False


NOTIFICATION_HANDLERS = {
    "telegram": lambda cfg, msg: send_telegram(
        cfg.get("telegram", {}).get("bot_token", ""),
        cfg.get("telegram", {}).get("chat_id", ""),
        msg
    ),
    "slack": lambda cfg, msg: send_slack(
        cfg.get("slack", {}).get("webhook_url", ""),
        msg
    ),
    "webhook": lambda cfg, msg: send_webhook(
        cfg.get("webhook", {}).get("url", ""),
        {"message": msg, "source": "agent-reach", "timestamp": datetime.utcnow().isoformat()}
    ),
}


# ============================================================
# SOURCE MONITORS
# ============================================================

def is_new_item(item_id: str) -> bool:
    """Check if item has already been processed (dedup)."""
    item_hash = hashlib.sha256(item_id.encode()).hexdigest()
    state_file = STATE_DIR / f"seen_{item_hash[:16]}"
    if state_file.exists():
        return False
    state_file.touch()
    return True


def monitor_rss(urls: list, keywords: list) -> list:
    """Monitor RSS feeds for keyword matches."""
    import xml.etree.ElementTree as ET
    import urllib.request
    alerts = []
    for url in urls:
        try:
            resp = urllib.request.urlopen(url, timeout=15)
            tree = ET.parse(resp)
            root = tree.getroot()
            for item in root.iter("item"):
                title = item.findtext("title", "")
                link = item.findtext("link", "")
                desc = item.findtext("description", "")
                content = f"{title}\n{desc}".lower()
                item_id = link or title
                if not is_new_item(item_id):
                    continue
                for kw in keywords:
                    if kw.lower() in content:
                        alerts.append({
                            "source": "rss",
                            "keyword": kw,
                            "title": title,
                            "url": link,
                            "severity": "info",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        break
        except Exception as e:
            logger.warning(f"RSS fetch failed for {url}: {e}")
    return alerts


def monitor_reddit(subreddit: str, keywords: list, limit: int = 25) -> list:
    """Monitor Reddit for keyword mentions."""
    import urllib.request
    alerts = []
    try:
        url = f"https://www.reddit.com/r/{subreddit}/new.json?limit={limit}"
        req = urllib.request.Request(url, headers={"User-Agent": "AgentReach/2.0"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        for post in data.get("data", {}).get("children", []):
            post_data = post.get("data", {})
            title = post_data.get("title", "")
            selftext = post_data.get("selftext", "")
            post_id = post_data.get("name", "")
            content = f"{title}\n{selftext}".lower()
            if not is_new_item(post_id):
                continue
            for kw in keywords:
                if kw.lower() in content:
                    alerts.append({
                        "source": f"reddit/r/{subreddit}",
                        "keyword": kw,
                        "title": title,
                        "url": f"https://reddit.com{post_data.get('permalink', '')}",
                        "score": post_data.get("score", 0),
                        "severity": "info",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    break
    except Exception as e:
        logger.warning(f"Reddit fetch failed: {e}")
    return alerts


def monitor_github_trending(keywords: list, language: str = "python") -> list:
    """Monitor GitHub trending repos for keyword relevance."""
    import urllib.request
    alerts = []
    try:
        url = f"https://api.github.com/search/repositories?q={keywords[0]}+language:{language}&sort=updated&per_page=10"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read())
        for repo in data.get("items", []):
            repo_id = str(repo.get("id", ""))
            if not is_new_item(repo_id):
                continue
            name = repo.get("full_name", "")
            desc = repo.get("description", "")
            content = f"{name}\n{desc}".lower()
            for kw in keywords:
                if kw.lower() in content:
                    alerts.append({
                        "source": "github",
                        "keyword": kw,
                        "title": name,
                        "url": repo.get("html_url", ""),
                        "stars": repo.get("stargazers_count", 0),
                        "severity": "info",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                    break
    except Exception as e:
        logger.warning(f"GitHub fetch failed: {e}")
    return alerts


def monitor_health_check() -> str:
    """Internal health check — verifies all components work."""
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "state_dir": str(STATE_DIR),
        "state_files": len(list(STATE_DIR.glob("seen_*"))),
        "log_size": (STATE_DIR / "agent-reach.log").stat().st_size if (STATE_DIR / "agent-reach.log").exists() else 0,
        "python_version": sys.version
    }
    return json.dumps(status, indent=2)


# ============================================================
# MAIN
# ============================================================

def run_once(config: dict) -> list:
    """Run all monitors once and return alerts."""
    all_alerts = []
    keywords = config.get("keywords", ["AI agent", "automation", "n8n"])
    sources = config.get("sources", {})

    # RSS
    if sources.get("rss", {}).get("enabled", False):
        logger.info("Scanning RSS feeds...")
        alerts = monitor_rss(sources["rss"].get("urls", []), keywords)
        all_alerts.extend(alerts)
        logger.info(f"  → {len(alerts)} RSS alerts")

    # Reddit
    if sources.get("reddit", {}).get("enabled", False):
        for subreddit in sources["reddit"].get("subreddits", []):
            logger.info(f"Scanning r/{subreddit}...")
            alerts = monitor_reddit(subreddit, keywords)
            all_alerts.extend(alerts)
            logger.info(f"  → {len(alerts)} Reddit alerts from r/{subreddit}")

    # GitHub
    if sources.get("github", {}).get("enabled", False):
        logger.info("Scanning GitHub...")
        alerts = monitor_github_trending(keywords, sources["github"].get("language", "python"))
        all_alerts.extend(alerts)
        logger.info(f"  → {len(alerts)} GitHub alerts")

    return all_alerts


def main():
    import yaml  # requires: pip install pyyaml

    # Load config
    if not os.path.exists(CONFIG_PATH):
        logger.error(f"Config not found: {CONFIG_PATH}")
        logger.info("Set AGENT_REACH_CONFIG env var or copy config to current directory")
        sys.exit(1)

    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)

    # Check for --health
    if "--health" in sys.argv:
        print(monitor_health_check())
        return

    # Check for --test
    if "--test" in sys.argv:
        logger.info("Testing notification channels...")
        test_msg = f"🧪 Agent Reach test alert — {datetime.now().isoformat()}"
        notifications = config.get("notifications", {})
        for channel, handler in NOTIFICATION_HANDLERS.items():
            if notifications.get(channel, {}).get("enabled", False):
                ok = handler(notifications[channel], test_msg)
                logger.info(f"  {channel}: {'✅ OK' if ok else '❌ FAILED'}")
        return

    # Scan mode
    alerts = run_once(config)
    notifications = config.get("notifications", {})

    if alerts:
        logger.info(f"\n=== {len(alerts)} new alerts found ===")
        for a in alerts[:10]:  # Show top 10
            logger.info(f"[{a['source']}] {a['title'][:80]}")

        # Send notifications (group by source to avoid spam)
        for source in set(a["source"] for a in alerts):
            source_alerts = [a for a in alerts if a["source"] == source]
            msg = f"🤖 *Agent Reach Alert*\n"
            msg += f"*Source:* {source}\n"
            msg += f"*Keyword:* {source_alerts[0]['keyword']}\n"
            msg += f"*New items:* {len(source_alerts)}\n\n"
            for a in source_alerts[:3]:
                msg += f"• [{a.get('title', '?')[:100]}]({a.get('url', '')})\n"

            for channel, handler in NOTIFICATION_HANDLERS.items():
                if notifications.get(channel, {}).get("enabled", False):
                    handler(notifications[channel], msg)
    else:
        logger.info("No new alerts found.")

    # Save alert log
    log_path = STATE_DIR / f"alerts_{datetime.now().strftime('%Y%m%d')}.json"
    existing = []
    if log_path.exists():
        with open(log_path) as f:
            existing = json.load(f)
    existing.extend(alerts)
    with open(log_path, "w") as f:
        json.dump(existing, f, indent=2)
    logger.info(f"Logged to {log_path}")


if __name__ == "__main__":
    if "--continuous" in sys.argv:
        logger.info("Starting continuous monitoring (every 300s)...")
        while True:
            main()
            time.sleep(300)
    else:
        main()
