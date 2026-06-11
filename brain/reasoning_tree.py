"""Reasoning-tree decision log for critical Hermes choices."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATE_PATH = Path.home() / ".hermes" / "agent_state.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _load_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_state(data: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def add_decision(
    command: str,
    task: str,
    chosen_branch: str,
    branches: list[dict[str, Any]] | None,
    outcome: str = "pending",
) -> dict[str, Any]:
    """Append a reasoning-tree decision to agent_state.json."""
    state = _load_state()
    items = state.setdefault("reasoning_tree", [])
    entry = {
        "timestamp_utc": _now(),
        "command": str(command),
        "task": str(task),
        "chosen_branch": str(chosen_branch),
        "branches": branches or [],
        "outcome": str(outcome),
    }
    items.append(entry)
    state["reasoning_tree"] = items[-200:]
    _save_state(state)
    return entry


def get_recent(limit: int = 10) -> list[dict[str, Any]]:
    state = _load_state()
    items = state.get("reasoning_tree", [])
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict)][-max(0, int(limit)) :]


def summarize() -> str:
    recent = get_recent(5)
    if not recent:
        return "Reasoning tree: karar kaydi yok."
    last = recent[-1]
    return (
        "Reasoning tree: "
        f"{len(recent)} recent | last={last.get('chosen_branch', '?')} "
        f"| outcome={last.get('outcome', '?')}"
    )
