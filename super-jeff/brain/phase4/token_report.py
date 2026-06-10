"""TokenGuard strategic advisor: weekly reports + self-tuning.

Reads token_budget.jsonl logs and produces:
  - Weekly report (top 10 expensive runs, overflow analysis)
  - Self-tuning recommendations for ChunkCompressor strategies
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

from brain.accounting import BUDGET_LOG, BUDGET_LIMITS, ChunkCompressor

TOKEN_REPORT_LOG = Path.home() / ".hermes" / "logs" / "token_report.jsonl"


def _read_token_log(hours: int = 168) -> list:
    """Read token_budget.jsonl entries from the last N hours."""
    if not BUDGET_LOG.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    entries = []
    try:
        for line in BUDGET_LOG.read_text(encoding="utf-8").strip().split("\n"):
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
                entries.append(entry)
    except (json.JSONDecodeError, OSError):
        pass
    return entries


def _append_report(entry: dict):
    """Append a report entry to the token report log."""
    try:
        TOKEN_REPORT_LOG.parent.mkdir(parents=True, exist_ok=True)
        with TOKEN_REPORT_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


def generate_weekly_report(hours: int = 168) -> dict:
    """Generate a weekly token usage report.

    Returns dict with:
      - top_expensive: top 10 runs by token count
      - mode_overflows: which modes overflow most
      - tool_combinations: most expensive tool patterns
      - total_tokens, total_entries
      - recommendations: list of tuning suggestions
    """
    entries = _read_token_log(hours)
    if not entries:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "period_hours": hours,
            "total_entries": 0,
            "total_tokens": 0,
            "top_expensive": [],
            "mode_overflows": {},
            "tool_combinations": [],
            "recommendations": ["No token data available for this period."],
        }
        _append_report(report)
        return report

    # Sort by token count descending
    sorted_entries = sorted(entries, key=lambda e: e.get("tokens", 0), reverse=True)
    top_expensive = [
        {
            "tokens": e.get("tokens", 0),
            "mode": e.get("mode", "unknown"),
            "action": e.get("action", "unknown"),
            "timestamp": e.get("timestamp", ""),
        }
        for e in sorted_entries[:10]
    ]

    # Mode overflow analysis
    mode_totals = defaultdict(lambda: {"count": 0, "total_tokens": 0, "overflows": 0})
    for e in entries:
        mode = e.get("mode", "unknown")
        tokens = e.get("tokens", 0)
        mode_totals[mode]["count"] += 1
        mode_totals[mode]["total_tokens"] += tokens
        limits = BUDGET_LIMITS.get(mode)
        if limits and tokens > limits["hard"]:
            mode_totals[mode]["overflows"] += 1

    mode_overflows = dict(mode_totals)

    # Tool combination analysis (action patterns)
    action_counter = Counter(e.get("action", "unknown") for e in entries)
    tool_combinations = [
        {"action": action, "count": count}
        for action, count in action_counter.most_common(10)
    ]

    total_tokens = sum(e.get("tokens", 0) for e in entries)

    # Generate recommendations
    recommendations = []
    for mode, stats in mode_totals.items():
        if stats["overflows"] > 0 and stats["count"] > 0:
            overflow_rate = stats["overflows"] / stats["count"]
            if overflow_rate > 0.2:
                recommendations.append(
                    f"Mode '{mode}' has {overflow_rate:.0%} overflow rate. "
                    f"Consider increasing hard limit or enabling compression."
                )
    if total_tokens > 100_000:
        recommendations.append(
            f"High total token consumption ({total_tokens:,}). "
            f"Consider enabling aggressive ChunkCompressor for large outputs."
        )

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "period_hours": hours,
        "total_entries": len(entries),
        "total_tokens": total_tokens,
        "top_expensive": top_expensive,
        "mode_overflows": mode_overflows,
        "tool_combinations": tool_combinations,
        "recommendations": recommendations,
    }
    _append_report(report)
    return report


def tune_compression_strategy(hours: int = 168) -> dict:
    """Analyze token usage and recommend tuned compression parameters.

    Returns dict with suggested ChunkCompressor settings.
    """
    entries = _read_token_log(hours)
    if not entries:
        return {"strategy": "default", "changes": []}

    # Find average and max token usage per mode
    mode_usage = defaultdict(list)
    for e in entries:
        mode = e.get("mode", "quick")
        tokens = e.get("tokens", 0)
        mode_usage[mode].append(tokens)

    suggestions = {}
    for mode, token_list in mode_usage.items():
        if not token_list:
            continue
        avg = sum(token_list) / len(token_list)
        max_t = max(token_list)
        limits = BUDGET_LIMITS.get(mode, BUDGET_LIMITS["quick"])

        changes = []
        if max_t > limits["hard"] * 0.9:
            changes.append(f"Reduce MAX_CONTEXT_CHARS for {mode} mode")
        if avg > limits["soft"]:
            changes.append(f"Enable chunking for {mode} mode outputs > {limits['soft']:,} tokens")

        if changes:
            suggestions[mode] = changes

    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "strategy": "tuned" if suggestions else "default",
        "suggestions": suggestions,
    }
    return result
