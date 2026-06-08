"""Hermes brain facade for core state, health, token and decision helpers."""

from .state import close_db, get_db, get_session
from .monitor import check_health, get_metrics
from .token import (
    TokenGuard,
    compress_message,
    estimate_tokens,
    get_budget_left,
    get_daily_usage,
    get_session_breakdown,
    set_log_level,
    should_log,
    track_usage,
)
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
from .retrieval import build_retrieval_layers, format_retrieval_layers
from .observability import (
    AUTONOMY_POLICY_LOG,
    ERROR_BUDGET_LOG,
    RUN_LOG,
    STEP_LOG,
    TOKEN_BUDGET_LOG,
    compute_error_budget,
    log_run,
    log_step,
    redact_payload,
    record_autonomy_decision,
    record_token_budget,
)

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
    "build_retrieval_layers",
    "format_retrieval_layers",
    "RUN_LOG",
    "STEP_LOG",
    "ERROR_BUDGET_LOG",
    "TOKEN_BUDGET_LOG",
    "AUTONOMY_POLICY_LOG",
    "log_run",
    "log_step",
    "record_autonomy_decision",
    "record_token_budget",
    "compute_error_budget",
    "redact_payload",
]
