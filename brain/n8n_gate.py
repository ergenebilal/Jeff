"""Safe write gate for n8n operations."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


GATE_PATH = Path.home() / ".hermes" / "n8n_write_gate.json"
LOG_PATH = Path.home() / ".hermes" / "logs" / "n8n_write.log"
WRITE_TTL_MINUTES = 60


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def is_write_enabled() -> bool:
    state = _load_state()
    if not state.get("enabled"):
        return False
    expires_at = _parse_dt(state.get("expires_at"))
    if expires_at is None:
        return False
    if utc_now() >= expires_at:
        _disable_state("expired")
        return False
    return True


def enable_write(minutes: int = WRITE_TTL_MINUTES, reason: str = "manual", actor: str = "local") -> dict[str, Any]:
    ttl = max(1, int(minutes))
    enabled_at = utc_now()
    expires_at = enabled_at + timedelta(minutes=ttl)
    state = {
        "enabled": True,
        "enabled_at": enabled_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "reason": str(reason or "manual"),
        "actor": str(actor or "local"),
    }
    _save_state(state)
    _append_log(f"{enabled_at.isoformat()} ENABLE actor={state['actor']} expires_at={state['expires_at']} reason={state['reason']}")
    return health()


def disable_write(reason: str = "manual") -> dict[str, Any]:
    return _disable_state(reason)


def health() -> dict[str, Any]:
    state = _load_state()
    enabled = bool(state.get("enabled")) and is_write_enabled()
    expires_at = _parse_dt(state.get("expires_at"))
    remaining = 0
    if enabled and expires_at is not None:
        remaining = max(0, int((expires_at - utc_now()).total_seconds()))
    return {
        "enabled": enabled,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "remaining_seconds": remaining,
        "log_path": str(LOG_PATH),
        "state_path": str(GATE_PATH),
        "reason": state.get("reason"),
        "actor": state.get("actor"),
    }


def record_write_action(action: str, detail: str = "") -> bool:
    if not is_write_enabled():
        return False
    stamp = utc_now().isoformat()
    suffix = f" detail={detail}" if detail else ""
    _append_log(f"{stamp} WRITE action={action}{suffix}")
    return True


def _disable_state(reason: str) -> dict[str, Any]:
    state = {
        "enabled": False,
        "disabled_at": utc_now().isoformat(),
        "reason": str(reason or "manual"),
    }
    _save_state(state)
    _append_log(f"{state['disabled_at']} DISABLE reason={state['reason']}")
    return health()


def _load_state() -> dict[str, Any]:
    try:
        if GATE_PATH.exists():
            raw = GATE_PATH.read_text(encoding="utf-8")
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
    except Exception:
        pass
    return {}


def _save_state(state: dict[str, Any]) -> None:
    try:
        GATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp = GATE_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(GATE_PATH)
    except Exception:
        pass


def _append_log(message: str) -> None:
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(message.rstrip() + "\n")
    except Exception:
        pass


def _parse_dt(value: Any) -> datetime | None:
    try:
        if not value:
            return None
        dt = datetime.fromisoformat(str(value))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None

