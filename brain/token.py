"""Token guard facade with deterministic, dependency-light helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

_LOG_LEVEL = "normal"
_LEVELS = {"critical": 0, "normal": 1, "verbose": 2}


def estimate_tokens(text: str) -> int:
    """Cheap prompt token estimate used for guardrails."""
    return max(1, len(str(text)) // 4) if text else 0


def compress_message(msg: Any, max_tokens: int = 500) -> str:
    """Return a bounded string representation for prompt/log context."""
    text = msg if isinstance(msg, str) else str(msg)
    limit = max(1, int(max_tokens)) * 4
    if len(text) <= limit:
        return text
    head = max(0, limit - 120)
    return text[:head] + f"\n...[{len(text) - head} chars compressed]"


def set_log_level(level: str) -> str:
    global _LOG_LEVEL
    if level not in _LEVELS:
        raise ValueError("level must be critical, normal, or verbose")
    _LOG_LEVEL = level
    return _LOG_LEVEL


def should_log(level: str) -> bool:
    return _LEVELS.get(level, 1) <= _LEVELS.get(_LOG_LEVEL, 1)


def track_usage(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return {"tracked": True, "args": len(args), "keys": sorted(kwargs)}


def get_budget_left() -> int:
    return 0


def get_daily_usage() -> dict[str, Any]:
    return {"tokens": 0, "estimated": True}


def get_session_breakdown(limit: int = 10) -> list[dict[str, Any]]:
    return [] if limit >= 0 else []


@dataclass
class TokenGuard:
    threshold_pct: float = 90.0

    def check(self) -> dict[str, Any]:
        return {"status": "ok", "threshold_pct": self.threshold_pct}
