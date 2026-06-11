"""Hermes brain facade for core state, health, token and decision helpers."""

from .state import close_db, get_db, get_session
from .monitor import check_health, get_metrics
from .accounting import (
    TokenGuard,
    ChunkCompressor,
    compress_message,
    estimate_tokens,
    get_budget_left,
    get_daily_usage,
    get_session_breakdown,
    log_token_usage,
    set_log_level,
    should_log,
    token_budget_check,
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
from .baseline import collect_baseline_snapshot, summarize_baseline
from .context_loader import get_relevant_context
from .context_manager import close_topic, get_active_topic, list_topics, new_topic, recall_topic
from .legacy_memory import import_legacy_memory
from .mood import detect_tone, format_by_tone, get_style_guide
from .advisors import assess_proposal, format_assessment
from .persona import (
    build_persona_context_line,
    build_persona_identity_block,
    load_persona_profile,
)
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
    "ChunkCompressor",
    "log_token_usage",
    "token_budget_check",
    "save_lesson",
    "get_recent_lessons",
    "get_lessons_summary",
    "mark_applied",
    "sync_all_to_mnemosyne",
    "TimeSyncGuard",
    "run_clock_keeper",
    "collect_baseline_snapshot",
    "summarize_baseline",
    "get_relevant_context",
    "new_topic",
    "close_topic",
    "list_topics",
    "recall_topic",
    "get_active_topic",
    "import_legacy_memory",
    "detect_tone",
    "get_style_guide",
    "format_by_tone",
    "assess_proposal",
    "format_assessment",
    "load_persona_profile",
    "build_persona_identity_block",
    "build_persona_context_line",
    "generate_brain_health_report",
]
