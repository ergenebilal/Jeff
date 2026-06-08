"""Hermes observability helpers for run, step, token, and autonomy traces."""

from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

LOG_DIR = Path.home() / ".hermes" / "logs"
RUN_LOG = LOG_DIR / "agent_runs.jsonl"
STEP_LOG = LOG_DIR / "step_trace.jsonl"
ERROR_BUDGET_LOG = LOG_DIR / "error_budget.jsonl"
TOKEN_BUDGET_LOG = LOG_DIR / "token_budget.jsonl"
AUTONOMY_POLICY_LOG = LOG_DIR / "autonomy_policy.jsonl"
MAX_STRING = 480
MAX_REDACTED_CHARS = 220

SECRET_KEY_RE = re.compile(
    r"(?:secret|token|api[_-]?key|password|passwd|bearer|authorization|auth|private[_-]?key)",
    re.IGNORECASE,
)
SECRET_VALUE_RE = re.compile(
    r"(?:sk-[A-Za-z0-9]{16,}|gsk_[A-Za-z0-9]{16,}|gh[pousr]_[A-Za-z0-9]{16,}|xox[baprs]-[A-Za-z0-9-]{10,}|Bearer\s+[A-Za-z0-9._-]{12,})",
    re.IGNORECASE,
)
LONG_TOKEN_RE = re.compile(r"^[A-Za-z0-9+/=._:-]{80,}$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _append_jsonl(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_parent(path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return payload


def _truncate_text(value: str, limit: int = MAX_STRING) -> str:
    if len(value) <= limit:
        return value
    head = max(80, limit // 2)
    tail = max(80, limit // 2)
    removed = len(value) - (head + tail)
    return f"{value[:head]}\n... [{removed} chars compressed] ...\n{value[-tail:]}"


def _looks_secret_key(key: str) -> bool:
    return bool(SECRET_KEY_RE.search(key))


def _looks_secret_value(value: str) -> bool:
    stripped = value.strip()
    if SECRET_VALUE_RE.search(value):
        return True
    if len(stripped) < 80:
        return False
    if len(set(stripped)) <= 4:
        return False
    has_alpha = any(char.isalpha() for char in stripped)
    has_digit = any(char.isdigit() for char in stripped)
    has_symbol = any(not char.isalnum() for char in stripped)
    return sum((has_alpha, has_digit, has_symbol)) >= 2


def redact_payload(value: Any) -> Any:
    """Recursively redact obvious secrets and compress oversized payloads."""
    if isinstance(value, dict):
        return {
            str(key): "[REDACTED]" if _looks_secret_key(str(key)) else redact_payload(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact_payload(item) for item in value]
    if isinstance(value, tuple):
        return [redact_payload(item) for item in value]
    if isinstance(value, str):
        if _looks_secret_value(value):
            return "[REDACTED]"
        return _truncate_text(value)
    return value


def log_run(
    *,
    task_type: str,
    mode: str,
    status: str,
    metrics: dict[str, Any] | None = None,
    context: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    record = {
        "event": "run",
        "run_id": run_id or f"run-{uuid4().hex}",
        "timestamp_utc": _utc_now(),
        "task_type": task_type,
        "mode": mode,
        "status": status,
        "metrics": redact_payload(metrics or {}),
        "context": redact_payload(context or {}),
        "tags": tags or [],
    }
    return _append_jsonl(RUN_LOG, record)


def log_step(
    *,
    run_id: str,
    step: str,
    observation: str,
    command: str | None = None,
    payload: Any | None = None,
    level: str = "normal",
) -> dict[str, Any]:
    record = {
        "event": "step",
        "run_id": run_id,
        "timestamp_utc": _utc_now(),
        "step": step,
        "level": level,
        "command": redact_payload(command) if command else None,
        "observation": redact_payload(observation),
        "payload": redact_payload(payload),
    }
    return _append_jsonl(STEP_LOG, record)


def record_autonomy_decision(
    *,
    action: str,
    reason: str,
    approved: bool = False,
    risk: str = "low",
    task_type: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    record = {
        "event": "autonomy_decision",
        "timestamp_utc": _utc_now(),
        "action": action,
        "reason": redact_payload(reason),
        "approved": approved,
        "risk": risk,
        "task_type": task_type,
        "metadata": redact_payload(metadata or {}),
    }
    return _append_jsonl(AUTONOMY_POLICY_LOG, record)


def record_token_budget(
    *,
    session_id: str,
    usage: float,
    budget_left: float,
    status: str,
) -> dict[str, Any]:
    record = {
        "event": "token_budget",
        "timestamp_utc": _utc_now(),
        "session_id": session_id,
        "usage": float(usage),
        "budget_left": float(budget_left),
        "status": status,
    }
    return _append_jsonl(TOKEN_BUDGET_LOG, record)


def compute_error_budget(days: int = 7) -> dict[str, Any]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    total = 0
    failed = 0
    if RUN_LOG.exists():
        for raw in RUN_LOG.read_text(encoding="utf-8").splitlines():
            if not raw.strip():
                continue
            try:
                row = json.loads(raw)
            except json.JSONDecodeError:
                continue
            timestamp = row.get("timestamp_utc") or row.get("timestamp")
            if not timestamp:
                continue
            try:
                when = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                continue
            if when < cutoff:
                continue
            total += 1
            status = str(row.get("status", "")).lower()
            if status not in {"completed", "success", "ok", "passed"}:
                failed += 1
    rate = failed / total if total else 0.0
    if total == 0 or rate <= 0.10:
        status = "healthy"
    elif rate <= 0.25:
        status = "watch"
    else:
        status = "critical"
    record = {
        "event": "error_budget",
        "timestamp_utc": _utc_now(),
        "window_days": days,
        "total_runs": total,
        "failed_runs": failed,
        "error_rate": round(rate, 4),
        "status": status,
    }
    _append_jsonl(ERROR_BUDGET_LOG, record)
    return record


__all__ = [
    "AUTONOMY_POLICY_LOG",
    "ERROR_BUDGET_LOG",
    "LOG_DIR",
    "MAX_REDACTED_CHARS",
    "MAX_STRING",
    "RUN_LOG",
    "STEP_LOG",
    "TOKEN_BUDGET_LOG",
    "compute_error_budget",
    "log_run",
    "log_step",
    "redact_payload",
    "record_autonomy_decision",
    "record_token_budget",
]
