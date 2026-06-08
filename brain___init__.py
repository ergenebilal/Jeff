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
]
