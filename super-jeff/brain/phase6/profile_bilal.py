"""Bilal work profile: analyzes usage patterns from logs.

Reads agent_runs and autonomy_policy logs to build:
  - Most common modes and tools
  - Typical task types
  - Ask/deny patterns
  - Preferences for domain Jeff setup
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

AGENT_RUNS_LOG = Path.home() / ".hermes" / "logs" / "agent_runs.jsonl"
AUTONOMY_LOG = Path.home() / ".hermes" / "logs" / "autonomy_policy.jsonl"


def _read_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    entries = []
    try:
        for line in path.read_text(encoding="utf-8").strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        pass
    return entries


def build_profile() -> dict:
    """Build Bilal's work profile from log data.

    Returns dict with mode preferences, common tools, and patterns.
    """
    runs = _read_jsonl(AGENT_RUNS_LOG)
    policies = _read_jsonl(AUTONOMY_LOG)

    profile = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_sessions": 0,
        "common_modes": {},
        "common_sources": {},
        "error_rate": 0,
        "policy_patterns": {},
        "recommendations": [],
    }

    if runs:
        mode_counter = Counter(r.get("mode", "quick") for r in runs)
        source_counter = Counter(r.get("source", "terminal") for r in runs)
        error_count = sum(1 for r in runs if r.get("error"))

        profile["total_sessions"] = len(runs)
        profile["common_modes"] = dict(mode_counter.most_common(5))
        profile["common_sources"] = dict(source_counter.most_common(5))
        profile["error_rate"] = round(error_count / len(runs), 3) if runs else 0

        # Determine default mode preference
        if mode_counter:
            profile["preferred_mode"] = mode_counter.most_common(1)[0][0]

    if policies:
        action_counter = Counter(p.get("action_type", "unknown") for p in policies)
        decision_counter = Counter(p.get("policy_decision", "unknown") for p in policies)
        profile["policy_patterns"] = {
            "top_actions": dict(action_counter.most_common(5)),
            "decisions": dict(decision_counter),
        }

    # Generate recommendations
    recs = []
    if profile.get("error_rate", 0) > 0.2:
        recs.append("Yuksek hata orani. Deep mode veya planli execution onerilir.")
    if profile.get("common_modes", {}).get("background", 0) > 10:
        recs.append("Yogun background kullanimi. Cron job monitoring guclendirilebilir.")
    if not recs:
        recs.append("Profil henuz yeterli veriye sahip degil.")

    profile["recommendations"] = recs
    return profile


def domain_recommendations() -> list:
    """Generate recommendations for domain-specific Jeff setups.

    Returns list of suggested domain configurations.
    """
    profile = build_profile()
    base = {
        "core_modules": [
            "brain.accounting",
            "brain.phase4.skill_lifecycle",
            "brain.phase4.eval_engine",
            "brain.phase4.autonomy_policy",
            "brain.phase5.mode_router",
        ],
        "shared_components": [
            "ChunkCompressor",
            "TokenGuard",
            "SkillLifecycle",
            "AutonomyPolicy",
        ],
    }

    domains = [
        {
            "domain": "klinik",
            "skills": ["hasta_kayit", "randevu", "recete", "tibbi_rapor"],
            "config": base.copy(),
        },
        {
            "domain": "restoran",
            "skills": ["menu", "siparis", "stok", "rezervasyon"],
            "config": base.copy(),
        },
        {
            "domain": "ergeneai",
            "skills": ["uretim_takip", "kalite_kontrol", "bakim", "sevkiyat"],
            "config": base.copy(),
        },
    ]

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "current_profile": profile,
        "available_domains": domains,
        "integration_note": "Domain-specific skills at L4 only. Core untouched.",
    }
