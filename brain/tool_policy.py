"""Tool and MCP policy snapshot helpers for Hermes brain.

This module is read-only: it observes how the tool surface is shaped and
writes an auditable JSONL trace. It does not enable, disable, or call tools.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

POLICY_LOG = Path.home() / ".hermes" / "logs" / "tool_policy.jsonl"
CORE_TOOL_NAMES = frozenset(
    {
        "terminal",
        "read_file",
        "write_file",
        "patch",
        "search_files",
        "todo",
        "memory",
        "browser_navigate",
        "browser_snapshot",
        "browser_click",
        "browser_type",
        "web_search",
        "web_extract",
        "session_search",
        "clarify",
        "execute_code",
        "delegate_task",
        "send_message",
        "tool_search",
        "tool_describe",
        "tool_call",
    }
)


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def _tool_name(tool_def: dict[str, Any]) -> str:
    return str((tool_def.get("function") or {}).get("name") or "")


def _estimate_tokens(tool_defs: list[dict[str, Any]]) -> int:
    total_chars = 0
    for item in tool_defs:
        try:
            total_chars += len(json.dumps(item, ensure_ascii=False, separators=(",", ":")))
        except Exception:
            total_chars += len(str(item))
    return max(total_chars // 4, 0)


def _source_kind(name: str) -> str:
    if name in CORE_TOOL_NAMES:
        return "core"
    try:
        from toolsets import _HERMES_CORE_TOOLS

        if name in _HERMES_CORE_TOOLS:
            return "core"
    except Exception:
        pass
    try:
        from tools.registry import registry

        entry = registry.get_entry(name)
        toolset = getattr(entry, "toolset", "") if entry is not None else ""
        if str(toolset).startswith("mcp-"):
            return "mcp"
        if toolset:
            return "plugin"
    except Exception:
        pass
    if name.startswith("mcp_"):
        return "mcp"
    if name.startswith("plugin_") or name.startswith("ext_"):
        return "plugin"
    return "other"


def _normalize_policy(raw: Any) -> dict[str, Any]:
    if raw is True:
        return {"enabled": "auto", "threshold_pct": 10.0}
    if raw is False:
        return {"enabled": "off", "threshold_pct": 10.0}
    if not isinstance(raw, dict):
        raw = {}
    enabled = str(raw.get("enabled", "auto")).strip().lower()
    if enabled in {"true", "yes", "1"}:
        enabled = "on"
    elif enabled in {"false", "no", "0"}:
        enabled = "off"
    elif enabled not in {"auto", "on", "off"}:
        enabled = "auto"
    try:
        threshold_pct = float(raw.get("threshold_pct", 10.0))
    except Exception:
        threshold_pct = 10.0
    threshold_pct = max(0.0, min(100.0, threshold_pct))
    return {"enabled": enabled, "threshold_pct": threshold_pct}


def _load_default_tool_search_policy() -> dict[str, Any]:
    try:
        from tools.tool_search import load_config

        cfg = load_config()
        return {"enabled": cfg.enabled, "threshold_pct": cfg.threshold_pct}
    except Exception:
        return {"enabled": "auto", "threshold_pct": 10.0}


def _load_tool_defs(enabled_toolsets=None, disabled_toolsets=None, quiet_mode: bool = True) -> list[dict[str, Any]]:
    from model_tools import get_tool_definitions

    return get_tool_definitions(
        enabled_toolsets=enabled_toolsets,
        disabled_toolsets=disabled_toolsets,
        quiet_mode=quiet_mode,
        skip_tool_search_assembly=True,
    )


def build_tool_policy_snapshot(
    *,
    tool_defs: list[dict[str, Any]] | None = None,
    enabled_toolsets=None,
    disabled_toolsets=None,
    quiet_mode: bool = True,
    tool_search_policy: Any = None,
    context_length: int | None = None,
) -> dict[str, Any]:
    """Return and log the current tool/MCP visibility policy snapshot."""
    raw_defs = list(tool_defs) if tool_defs is not None else _load_tool_defs(
        enabled_toolsets=enabled_toolsets,
        disabled_toolsets=disabled_toolsets,
        quiet_mode=quiet_mode,
    )
    policy = _normalize_policy(tool_search_policy if tool_search_policy is not None else _load_default_tool_search_policy())

    entries = []
    source_breakdown = {"core": 0, "mcp": 0, "plugin": 0, "other": 0}
    for item in raw_defs:
        name = _tool_name(item)
        if not name:
            continue
        kind = _source_kind(name)
        source_breakdown[kind] += 1
        entries.append({"name": name, "source": kind, "tool_def": item})

    visible_names = [item["name"] for item in entries if item["source"] in {"core", "other"}]
    deferred_entries = [item for item in entries if item["source"] in {"mcp", "plugin"}]
    deferred_names = [item["name"] for item in deferred_entries]
    deferred_defs = [item["tool_def"] for item in deferred_entries]
    deferred_tokens = _estimate_tokens(deferred_defs)

    threshold_tokens = 0
    if context_length:
        threshold_tokens = int(int(context_length) * (policy["threshold_pct"] / 100.0))
    if policy["enabled"] == "off" or not deferred_names:
        bridge_active = False
    elif policy["enabled"] == "on":
        bridge_active = True
    elif not context_length:
        bridge_active = deferred_tokens >= 20_000
    else:
        bridge_active = deferred_tokens >= threshold_tokens

    snapshot = {
        "event": "tool_policy_snapshot",
        "timestamp_utc": _utc_iso(),
        "policy": policy,
        "policy_mode": "bridge" if bridge_active else "pass_through",
        "bridge_active": bool(bridge_active),
        "context_length": context_length,
        "threshold_tokens": threshold_tokens,
        "deferred_tokens": deferred_tokens,
        "source_breakdown": source_breakdown,
        "visible_count": len(visible_names),
        "deferred_count": len(deferred_names),
        "visible_names": visible_names,
        "deferred_names": deferred_names,
    }
    snapshot["policy_lines"] = format_tool_policy_snapshot(snapshot).splitlines()
    _append_jsonl(POLICY_LOG, snapshot)
    return snapshot


def format_tool_policy_snapshot(snapshot: dict[str, Any]) -> str:
    """Render a compact prompt-safe policy summary."""
    breakdown = snapshot.get("source_breakdown") or {}
    deferred = snapshot.get("deferred_names") or []
    visible = snapshot.get("visible_names") or []
    lines = [
        (
            "🧩 Tool policy: "
            f"{snapshot.get('policy_mode', 'unknown')} | "
            f"visible={len(visible)} | deferred={len(deferred)} | "
            f"bridge={'on' if snapshot.get('bridge_active') else 'off'}"
        ),
        (
            "Kaynaklar: "
            f"core={breakdown.get('core', 0)} | "
            f"mcp={breakdown.get('mcp', 0)} | "
            f"plugin={breakdown.get('plugin', 0)} | "
            f"other={breakdown.get('other', 0)}"
        ),
    ]
    if deferred:
        lines.append("Deferred: " + ", ".join(deferred[:8]))
    return "\n".join(lines)


__all__ = [
    "POLICY_LOG",
    "build_tool_policy_snapshot",
    "format_tool_policy_snapshot",
]
