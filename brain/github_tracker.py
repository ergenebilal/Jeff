"""GitHub tracker: fetches "hermes"-tagged projects weekly.

Queries the GitHub Search API for repositories tagged "hermes",
evaluates them by star count, recency of update, and description
quality, then produces a structured weekly report.

Usage:
    from brain.github_tracker import run_weekly_tracker
    report = run_weekly_tracker()          # fetch + evaluate now
    report = run_weekly_tracker(force=True) # re-fetch even if cached today
"""

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

REPORTS_DIR = Path.home() / ".hermes" / "reports"
REPORT_FILE = REPORTS_DIR / "github_weekly.json"

# GitHub Search API — public, no token needed for anonymous reads (rate-limited)
SEARCH_URL = (
    "https://api.github.com/search/repositories"
    "?q=hermes&sort=stars&order=desc&per_page=30"
)

# Evaluation thresholds
MIN_STARS = 10
MAX_DAYS_SINCE_UPDATE = 90  # ~3 months
MIN_DESC_LENGTH = 10  # characters for a meaningful description

# Cache: only re-fetch once per day unless forced
CACHE_TTL_SECONDS = 86400  # 24 hours


def _report_path() -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return REPORT_FILE


def _fetch_repos() -> list[dict[str, Any]]:
    """Fetch repositories from GitHub Search API."""
    req = urllib.request.Request(
        SEARCH_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "HermesAgent/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body.get("items", [])
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, json.JSONDecodeError) as exc:
        return []


def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse an ISO-8601 date string to a datetime (UTC)."""
    if not date_str:
        return None
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _evaluate_repo(repo: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a single repository and return an assessment."""
    name = repo.get("full_name", "unknown")
    stars = repo.get("stargazers_count", 0)
    description = (repo.get("description") or "").strip()
    updated_at = _parse_date(repo.get("updated_at"))
    pushed_at = _parse_date(repo.get("pushed_at"))
    html_url = repo.get("html_url", "")
    language = repo.get("language") or ""
    topics = repo.get("topics", [])
    owner = repo.get("owner", {}).get("login", "")

    now = datetime.now(timezone.utc)
    days_since_update = (
        (now - updated_at).days
        if updated_at
        else 999
    )

    # Decision logic
    reasons: list[str] = []
    useful = True

    if stars < MIN_STARS:
        reasons.append(f"sadece {stars} yildiz (< {MIN_STARS})")
        useful = False
    if days_since_update > MAX_DAYS_SINCE_UPDATE:
        reasons.append(f"son guncelleme {days_since_update} gun once (> {MAX_DAYS_SINCE_UPDATE})")
        useful = False
    if len(description) < MIN_DESC_LENGTH:
        reasons.append(f"aciklama yetersiz ({len(description)} karakter)")
        useful = False

    if useful:
        decision = "faydali"
    else:
        decision = "faydasiz" if not useful and reasons else "incelenmeli"

    return {
        "name": name,
        "owner": owner,
        "url": html_url,
        "stars": stars,
        "language": language,
        "description": description[:200],
        "topics": topics,
        "updated_at": repo.get("updated_at", ""),
        "days_since_update": days_since_update,
        "decision": decision,
        "reasons": reasons,
    }


def run_weekly_tracker(force: bool = False) -> dict[str, Any]:
    """Fetch and evaluate "hermes" projects from GitHub.

    Args:
        force: If True, re-fetch even if a recent report exists.

    Returns:
        Structured report dict with:
          - timestamp, summary (total / useful / useless counts)
          - projects (detailed list)
          - top_picks (top-5 useful projects by stars)
    """
    report_path = _report_path()

    # Check cache freshness
    if not force and report_path.exists():
        try:
            cached = json.loads(report_path.read_text(encoding="utf-8"))
            cached_ts = _parse_date(cached.get("timestamp"))
            if cached_ts:
                age = (datetime.now(timezone.utc) - cached_ts).total_seconds()
                if age < CACHE_TTL_SECONDS:
                    return cached
        except (json.JSONDecodeError, OSError):
            pass

    repos = _fetch_repos()
    evaluated = [_evaluate_repo(r) for r in repos]

    useful = [e for e in evaluated if e["decision"] == "faydali"]
    useless = [e for e in evaluated if e["decision"] == "faydasiz"]
    review = [e for e in evaluated if e["decision"] == "incelenmeli"]

    top_picks = sorted(useful, key=lambda x: x["stars"], reverse=True)[:5]

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": "GitHub Search API",
        "query": "hermes",
        "summary": {
            "total_projects": len(evaluated),
            "useful": len(useful),
            "faydasiz": len(useless),
            "incelenmeli": len(review),
        },
        "top_picks": top_picks,
        "projects": evaluated,
    }

    # Write report
    try:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError:
        pass

    return report


def get_latest_report() -> Optional[dict[str, Any]]:
    """Return the most recent cached report, or None."""
    report_path = _report_path()
    if not report_path.exists():
        return None
    try:
        return json.loads(report_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def summarize_report(report: Optional[dict[str, Any]] = None) -> str:
    """Return a one-line summary string for cron_summary."""
    if report is None:
        report = get_latest_report()
    if not report:
        return "GitHub tracker: Henuz rapor yok."
    s = report.get("summary", {})
    total = s.get("total_projects", 0)
    useful = s.get("useful", 0)
    useless = s.get("faydasiz", 0)
    top = report.get("top_picks", [])
    top_names = ", ".join(p["name"] for p in top[:3])
    return (
        f"GitHub tracker: {total} proje tarandi, "
        f"{useful} faydali, {useless} faydasiz. "
        f"En iyiler: {top_names}"
    )
