"""Daily eval job: reads real agent_runs logs, produces category-based scores.

Triggered by cron, outputs to eval_daily.jsonl for dashboard consumption.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

EVAL_DAILY_LOG = Path.home() / ".hermes" / "logs" / "eval_daily.jsonl"
AGENT_RUNS_LOG = Path.home() / ".hermes" / "logs" / "agent_runs.jsonl"

CATEGORIES = [
    "log_analysis", "root_cause", "retrieval", "skill_reuse",
    "policy_compliance", "cron", "token_budget", "recovery",
]

DEFAULT_EXECUTORS = {
    "log_analysis": lambda runs: {
        "success": True,
        "metrics": {
            "total_runs": len(runs),
            "error_rate": sum(1 for r in runs if r.get("error")) / max(len(runs), 1),
        },
    },
    "root_cause": lambda runs: {
        "success": len(runs) > 0,
        "metrics": {"causes_found": sum(1 for r in runs if r.get("error"))},
    },
    "retrieval": lambda runs: {
        "success": True,
        "metrics": {"retrieval_hit": any(r.get("retrieved") for r in runs)},
    },
    "skill_reuse": lambda runs: {
        "success": True,
        "metrics": {"reuse_count": sum(1 for r in runs if r.get("skill_used"))},
    },
    "policy_compliance": lambda runs: {
        "success": True,
        "metrics": {"compliant": all(r.get("policy_ok", True) for r in runs)},
    },
    "cron": lambda runs: {
        "success": any(r.get("source") == "cron" for r in runs),
        "metrics": {"cron_jobs": sum(1 for r in runs if r.get("source") == "cron")},
    },
    "token_budget": lambda runs: {
        "success": True,
        "metrics": {
            "total_tokens": sum(r.get("tokens", 0) for r in runs),
        },
    },
    "recovery": lambda runs: {
        "success": any(r.get("recovered") for r in runs),
        "metrics": {"recoveries": sum(1 for r in runs if r.get("recovered"))},
    },
}


def _read_agent_runs(hours: int = 24) -> list:
    """Read agent_runs from the last N hours."""
    if not AGENT_RUNS_LOG.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    runs = []
    try:
        for line in AGENT_RUNS_LOG.read_text(encoding="utf-8").strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            ts = entry.get("timestamp", "")
            try:
                entry_dt = datetime.fromisoformat(ts)
                if entry_dt.tzinfo is None:
                    entry_dt = entry_dt.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                entry_dt = datetime.now(timezone.utc)
            if entry_dt >= cutoff:
                runs.append(entry)
    except (json.JSONDecodeError, OSError):
        pass
    return runs


def _read_agent_runs_unfiltered() -> list:
    """Read agent_runs without the time filter for explicit custom evals."""
    if not AGENT_RUNS_LOG.exists():
        return []
    runs = []
    try:
        for line in AGENT_RUNS_LOG.read_text(encoding="utf-8").strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if isinstance(entry, dict):
                runs.append(entry)
    except (json.JSONDecodeError, OSError):
        pass
    return runs


def _append_entry(entry: dict):
    """Append a result to the daily eval log."""
    try:
        EVAL_DAILY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with EVAL_DAILY_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


def run_daily_eval(hours: int = 24, executors: dict = None) -> list:
    """Run daily evaluation across all categories.

    Args:
        hours: How many hours of agent_runs to analyze.
        executors: Optional custom executors per category (overrides defaults).

    Returns:
        List of result dicts with category, score, and metrics.
    """
    runs = _read_agent_runs(hours)
    if not runs and executors:
        runs = _read_agent_runs_unfiltered()
    if not runs:
        return _empty_report()

    results = []
    resolved = {**DEFAULT_EXECUTORS, **(executors or {})}
    timestamp = datetime.now(timezone.utc).isoformat()

    for category in CATEGORIES:
        executor = resolved.get(category)
        if not executor:
            continue
        try:
            result = executor(runs)
            entry = {
                "timestamp": timestamp,
                "category": category,
                "success": result.get("success", False),
                "metrics": result.get("metrics", {}),
                "run_count": len(runs),
                "period_hours": hours,
            }
        except Exception as e:
            entry = {
                "timestamp": timestamp,
                "category": category,
                "success": False,
                "error": str(e),
                "run_count": len(runs),
                "period_hours": hours,
            }
        _append_entry(entry)
        results.append(entry)

    return results


def _empty_report() -> list:
    """Return a zeroed report when no agent runs are found."""
    timestamp = datetime.now(timezone.utc).isoformat()
    results = []
    for category in CATEGORIES:
        entry = {
            "timestamp": timestamp,
            "category": category,
            "success": False,
            "metrics": {},
            "run_count": 0,
            "period_hours": 24,
            "error": "No agent runs found in period",
        }
        _append_entry(entry)
        results.append(entry)
    return results


def get_latest_scores() -> dict:
    """Get the most recent eval scores per category."""
    if not EVAL_DAILY_LOG.exists():
        return {}
    scores = {}
    try:
        for line in EVAL_DAILY_LOG.read_text(encoding="utf-8").strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            cat = entry.get("category")
            if cat:
                scores[cat] = entry
    except (json.JSONDecodeError, OSError):
        pass
    # Return only the last entry per category
    # (lines are chronological, last wins)
    return scores
