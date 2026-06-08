"""Autonomy policy engine: formalized allow/ask/deny with audit trail.

99/1 principle:
  - allow (99%): read, analysis, dry-run, non-destructive
  - ask (1%): config changes, cron edit, skill retire, destructive
  - deny: explicitly forbidden destructive actions
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

AUTONOMY_LOG = Path.home() / ".hermes" / "logs" / "autonomy_policy.jsonl"

# ── Risk levels ──────────────────────────────────────────────────────────────

RISK_LEVELS = {
    "info": {"label": "Bilgi", "default": "allow"},
    "read": {"label": "Okuma", "default": "allow"},
    "analysis": {"label": "Analiz", "default": "allow"},
    "dry_run": {"label": "Deneme", "default": "allow"},
    "write": {"label": "Yazma", "default": "ask"},
    "config": {"label": "Konfigürasyon", "default": "ask"},
    "destructive": {"label": "Yıkıcı", "default": "deny"},
}

# Action type → risk level mapping
ACTION_RISK = {
    # Allow by default
    "read_file": "read",
    "list_directory": "read",
    "check_status": "info",
    "analyze_logs": "analysis",
    "run_eval": "analysis",
    "search_code": "read",
    "dry_run": "dry_run",
    "summarize": "analysis",
    "query_db_read": "read",
    # Ask by default
    "write_file": "write",
    "edit_config": "config",
    "restart_service": "config",
    "schedule_cron": "config",
    "retire_skill": "config",
    "deprecate_skill": "config",
    "send_notification": "write",
    "run_command": "write",
    # Deny by default
    "delete_file": "destructive",
    "drop_database": "destructive",
    "rm_rf": "destructive",
    "shutdown": "destructive",
    "format_disk": "destructive",
}


def _load_log() -> list:
    """Load all policy decision entries."""
    if not AUTONOMY_LOG.exists():
        return []
    entries = []
    try:
        for line in AUTONOMY_LOG.read_text(encoding="utf-8").strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    except (json.JSONDecodeError, OSError):
        pass
    return entries


def _append_log(entry: dict):
    """Append a policy decision to the log."""
    try:
        AUTONOMY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with AUTONOMY_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


def get_risk_level(action_type: str) -> str:
    """Get the risk level for an action type."""
    return ACTION_RISK.get(action_type, "ask")


def evaluate_action(action_type: str, resource: str = "",
                    context: Optional[dict] = None) -> dict:
    """Evaluate an action against the autonomy policy.

    Args:
        action_type: Type of action (e.g., "read_file", "delete_file").
        resource: The target resource (file path, URL, etc.).
        context: Optional context (user message, session info, etc.).

    Returns:
        Dict with decision (allow/ask/deny), risk_level, reason, and policy.
    """
    risk_level = get_risk_level(action_type)
    risk_info = RISK_LEVELS.get(risk_level, {"default": "ask", "label": "Bilinmiyor"})
    decision = risk_info["default"]

    reasons = []

    if decision == "allow":
        reasons.append(f"Düşük risk: {risk_info['label']}")
    elif decision == "ask":
        reasons.append(f"Orta risk: {risk_info['label']} — onay gerekiyor")
    elif decision == "deny":
        reasons.append(f"Yüksek risk: {risk_info['label']} — izin verilmiyor")

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action_type": action_type,
        "resource": resource,
        "risk_level": risk_level,
        "policy_decision": decision,
        "reason": "; ".join(reasons),
        "context": context or {},
    }
    _append_log(entry)
    return entry


def self_audit() -> dict:
    """Run self-audit on policy decisions.

    Returns summary of allow/ask/deny distribution and patterns.
    """
    entries = _load_log()
    if not entries:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_decisions": 0,
            "summary": "Henüz politika kararı yok.",
        }

    total = len(entries)
    allow_count = sum(1 for e in entries if e.get("policy_decision") == "allow")
    ask_count = sum(1 for e in entries if e.get("policy_decision") == "ask")
    deny_count = sum(1 for e in entries if e.get("policy_decision") == "deny")

    # Most common action types that trigger ask/deny
    action_counts = {}
    for e in entries:
        if e.get("policy_decision") in ("ask", "deny"):
            at = e.get("action_type", "unknown")
            action_counts[at] = action_counts.get(at, 0) + 1

    top_blocked = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # Generate recommendations
    recommendations = []
    deny_pct = deny_count / total if total > 0 else 0
    if deny_pct > 0.3:
        recommendations.append(
            f"Yüksek deny oranı (%{deny_pct:.0f}). Politika tanımlarını gözden geçirin."
        )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_decisions": total,
        "allow": allow_count,
        "ask": ask_count,
        "deny": deny_count,
        "top_blocked_actions": [{"action": a, "count": c} for a, c in top_blocked],
        "recommendations": recommendations,
    }


def format_ask_message(evaluation: dict) -> str:
    """Format an ask decision into a user-friendly message.

    Returns a string with the action summary and numbered alternatives.
    """
    action_type = evaluation.get("action_type", "unknown")
    resource = evaluation.get("resource", "")
    reason = evaluation.get("reason", "")

    lines = [
        f"**Aksiyon:** {action_type}",
        f"**Hedef:** {resource}" if resource else "",
        f"**Sebep:** {reason}",
        "",
        "Seçenekler:",
        "1. Devam et (onayla)",
        "2. İptal et",
        "3. Farklı bir yaklaşım öner",
    ]
    return "\n".join(line for line in lines if line)
