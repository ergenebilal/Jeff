"""Cron job summary: session-start report + priority notifications.

Reads background job outputs from ~/.hermes/cron/output/ and produces:
  - Session start report: job count, success/fail rates, key findings
  - Priority notification for critical job failures
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

CRON_OUTPUT_DIR = Path.home() / ".hermes" / "cron" / "output"

# Critical job patterns (jobs whose failure triggers immediate notification)
CRITICAL_JOB_PATTERNS = ["health_check", "gateway", "eval_daily", "token_report"]


def _load_jobs(hours: int = 24) -> list:
    """Load background job outputs from the last N hours."""
    if not CRON_OUTPUT_DIR.exists():
        return []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    jobs = []
    for f in CRON_OUTPUT_DIR.iterdir():
        if f.suffix != ".json":
            continue
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            ts = data.get("timestamp", data.get("started_at", ""))
            try:
                job_dt = datetime.fromisoformat(ts)
                if job_dt.tzinfo is None:
                    job_dt = job_dt.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                job_dt = datetime.now(timezone.utc)
            if job_dt >= cutoff:
                data["_file"] = str(f)
                data["_job_id"] = f.stem
                jobs.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return jobs


def generate_session_start_report(hours: int = 24) -> dict:
    """Generate a cron job summary for session start.

    Returns:
        Dict with job counts, success/fail breakdown, and findings.
    """
    jobs = _load_jobs(hours)
    if not jobs:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "period_hours": hours,
            "total_jobs": 0,
            "summary": "Son 24 saatte cron job bulunamadı.",
        }

    total = len(jobs)
    success = sum(1 for j in jobs if j.get("status") == "completed" or j.get("success"))
    failed = total - success

    # Group by type/source
    by_source = {}
    for j in jobs:
        source = j.get("source", j.get("job_type", "unknown"))
        by_source.setdefault(source, {"total": 0, "success": 0})
        by_source[source]["total"] += 1
        if j.get("status") == "completed" or j.get("success"):
            by_source[source]["success"] += 1

    # Find critical failures
    critical_failures = []
    for j in jobs:
        job_id = j.get("_job_id", "")
        is_critical = any(pattern in job_id for pattern in CRITICAL_JOB_PATTERNS)
        if is_critical and not (j.get("status") == "completed" or j.get("success")):
            critical_failures.append({
                "job_id": job_id,
                "source": j.get("source", "unknown"),
                "error": j.get("error", j.get("stderr", "unknown error")),
            })

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "period_hours": hours,
        "total_jobs": total,
        "success": success,
        "failed": failed,
        "success_rate": round(success / total, 2) if total > 0 else 0,
        "by_source": by_source,
        "critical_failures": critical_failures,
        "summary": (
            f"{total} job | {success} başarılı | {failed} başarısız "
            f"| {len(critical_failures)} kritik hata"
        ),
    }
    return report


def check_critical_failures(hours: int = 24) -> list:
    """Check for critical job failures that need immediate notification.

    Returns:
        List of critical failure dicts (empty if none).
    """
    report = generate_session_start_report(hours)
    return report.get("critical_failures", [])


def github_tracker_summary() -> str:
    """Return a one-line summary of the latest GitHub tracker report.

    Called during session-start to show what's new on GitHub.
    """
    try:
        from brain.github_tracker import summarize_report
        return summarize_report()
    except ImportError:
        return "GitHub tracker: modul yuklu degil."
    except Exception:
        return "GitHub tracker: hata."
