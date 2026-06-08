"""Hermes brain facade for core state, health, token and decision helpers."""

# Graceful imports — each sub-module may not exist in all deployments
def _import_or_dummy(module_name, names):
    """Try to import names from a module; return dummy objects on failure."""
    try:
        mod = __import__(f"brain.{module_name}", fromlist=names)
        return {n: getattr(mod, n, None) for n in names}
    except (ImportError, AttributeError, ModuleNotFoundError):
        return {n: None for n in names}

_imports = _import_or_dummy("state", ["close_db", "get_db", "get_session"])
close_db = _imports["close_db"]
get_db = _imports["get_db"]
get_session = _imports["get_session"]

_imports = _import_or_dummy("monitor", ["check_health", "get_metrics"])
check_health = _imports["check_health"]
get_metrics = _imports["get_metrics"]

_imports = _import_or_dummy("token", [
    "TokenGuard", "compress_message", "estimate_tokens",
    "get_budget_left", "get_daily_usage", "get_session_breakdown",
    "set_log_level", "should_log", "track_usage",
])
track_usage = _imports["track_usage"]
get_budget_left = _imports["get_budget_left"]
get_daily_usage = _imports["get_daily_usage"]
get_session_breakdown = _imports["get_session_breakdown"]
set_log_level = _imports["set_log_level"]
should_log = _imports["should_log"]
compress_message = _imports["compress_message"]
estimate_tokens = _imports["estimate_tokens"]
TokenGuard = _imports["TokenGuard"]
from .learning import (
    get_lessons_summary,
    get_recent_lessons,
    mark_applied,
    save_lesson,
    sync_all_to_mnemosyne,
)
from .clock_keeper import TimeSyncGuard, run_clock_keeper
from .context_loader import get_relevant_context
from .mood import detect_tone, format_by_tone, get_style_guide
from .advisors import assess_proposal, format_assessment
from .reporter import generate_health_report as generate_brain_health_report

__all__ = [
    "get_db",
    "get_session",
    "close_db",
    "check_health",
    "get_metrics",
    "track_usage",
    "get_budget_left",
    "get_daily_usage",
    "get_session_breakdown",
    "set_log_level",
    "should_log",
    "compress_message",
    "estimate_tokens",
    "TokenGuard",
    "save_lesson",
    "get_recent_lessons",
    "get_lessons_summary",
    "mark_applied",
    "sync_all_to_mnemosyne",
    "TimeSyncGuard",
    "run_clock_keeper",
    "get_relevant_context",
    "detect_tone",
    "get_style_guide",
    "format_by_tone",
    "assess_proposal",
    "format_assessment",
    "generate_brain_health_report",
]
