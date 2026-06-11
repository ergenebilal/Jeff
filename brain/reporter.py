"""Brain health report facade."""

from __future__ import annotations

from typing import Any


def generate_health_report() -> dict[str, Any]:
    try:
        from .monitor import check_health

        return check_health()
    except Exception as exc:
        return {"status": "degraded", "error": str(exc)}


def run_report_cycle() -> dict[str, Any]:
    """Return a quiet two-hour report payload for cron use."""
    report = generate_health_report()
    return {
        "status": report.get("status", "unknown"),
        "sent": False,
        "quiet": True,
        "report": report,
    }
