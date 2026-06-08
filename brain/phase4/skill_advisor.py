"""Skill advisor: auto-deprecate, golden tags, deprecation warnings.

Extends SkillLifecycle with intelligence:
  - Auto-deprecate: marks stale/low-success skills as deprecated
  - Golden skills: tags high-performers with 'golden' label
  - Deprecation warning: warns when deprecated skill is queried
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from brain.phase4.skill_lifecycle import SKILLS_LOG, SkillLifecycle

GOLDEN_THRESHOLD_USAGE = 5
GOLDEN_THRESHOLD_SUCCESS = 0.8
STALE_DAYS = 30
STALE_SUCCESS_RATE = 0.3


def _load_all_skills() -> list:
    """Load all skills from the skills log."""
    if not SKILLS_LOG.exists():
        return []
    entries = []
    try:
        for line in SKILLS_LOG.read_text(encoding="utf-8").strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            entries.append(json.loads(line))
    except (json.JSONDecodeError, OSError):
        pass
    return entries


def get_golden_skills() -> list:
    """Return skills with high usage and success rate (golden tag)."""
    entries = _load_all_skills()
    if not entries:
        return []

    # Build per-skill stats from most recent entries
    skill_stats = defaultdict(lambda: {"usage_count": 0, "success_count": 0, "entries": []})
    for e in entries:
        name = e.get("name", "unknown")
        skill_stats[name]["usage_count"] += 1
        # Count as success if stage is not "failed" or "error"
        stage = e.get("stage", "")
        if stage not in ("failed", "error"):
            skill_stats[name]["success_count"] += 1
        skill_stats[name]["entries"].append(e)

    golden = []
    for name, stats in skill_stats.items():
        if stats["usage_count"] < GOLDEN_THRESHOLD_USAGE:
            continue
        success_rate = stats["success_count"] / stats["usage_count"]
        if success_rate >= GOLDEN_THRESHOLD_SUCCESS:
            golden.append({
                "name": name,
                "usage_count": stats["usage_count"],
                "success_rate": round(success_rate, 2),
            })

    return sorted(golden, key=lambda g: g["usage_count"], reverse=True)


def find_deprecation_candidates() -> list:
    """Find skills that should be auto-deprecated.

    Criteria (either):
      - No usage in STALE_DAYS AND success_rate < STALE_SUCCESS_RATE
      - success_rate < STALE_SUCCESS_RATE / 2 (critically low)
    """
    entries = _load_all_skills()
    if not entries:
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=STALE_DAYS)

    # Group by skill name, get latest timestamp and stage
    skill_info = {}
    for e in entries:
        name = e.get("name", "unknown")
        ts = e.get("timestamp", "")
        try:
            e_dt = datetime.fromisoformat(ts)
            if e_dt.tzinfo is None:
                e_dt = e_dt.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            e_dt = datetime.now(timezone.utc)

        if name not in skill_info:
            skill_info[name] = {
                "last_used": e_dt,
                "usage_count": 0,
                "success_count": 0,
                "stage": e.get("stage", "active"),
                "profile": e.get("profile", "default"),
            }
        else:
            if e_dt > skill_info[name]["last_used"]:
                skill_info[name]["last_used"] = e_dt
                skill_info[name]["stage"] = e.get("stage", skill_info[name]["stage"])
                skill_info[name]["profile"] = e.get("profile", skill_info[name]["profile"])

        skill_info[name]["usage_count"] += 1
        stage = e.get("stage", "")
        if stage not in ("failed", "error"):
            skill_info[name]["success_count"] += 1

    candidates = []
    for name, info in skill_info.items():
        if info["stage"] in ("deprecated", "archived", "deleted"):
            continue
        success_rate = info["success_count"] / max(info["usage_count"], 1)
        stale = info["last_used"] < cutoff

        reason = None
        if stale and success_rate < STALE_SUCCESS_RATE:
            reason = f"Stale (last used {info['last_used'].strftime('%Y-%m-%d')}) + low success ({success_rate:.0%})"
        elif success_rate < STALE_SUCCESS_RATE / 2:
            reason = f"Critically low success rate ({success_rate:.0%})"

        if reason:
            candidates.append({
                "name": name,
                "reason": reason,
                "success_rate": round(success_rate, 2),
                "usage_count": info["usage_count"],
                "profile": info["profile"],
                "stage": info["stage"],
            })

    return candidates


def auto_deprecate(dry_run: bool = True) -> list:
    """Auto-deprecate stale/low-success skills.

    Args:
        dry_run: If True, only return candidates without applying changes.

    Returns:
        List of deprecation results.
    """
    candidates = find_deprecation_candidates()
    results = []
    for c in candidates:
        if dry_run:
            results.append({**c, "action": "would_deprecate"})
        else:
            result = SkillLifecycle.transition(
                c["name"],
                to_stage="deprecated",
                profile=c.get("profile", "default"),
                replacement=None,
            )
            results.append({
                "name": c["name"],
                "reason": c["reason"],
                "action": "deprecated",
                "success": result.get("success", False),
            })
    return results


def deprecation_warning(name: str, profile: str = "default") -> Optional[str]:
    """Return a warning message if the skill is deprecated, with replacement."""
    stage = SkillLifecycle.get_stage(name, profile)
    if stage != "deprecated":
        return None

    # Find the deprecation entry to get the replacement
    entries = _load_all_skills()
    for e in reversed(entries):
        if e.get("name") == name and e.get("profile", "default") == profile:
            replacement = e.get("replacement")
            if replacement:
                return (
                    f"Skill '{name}' is deprecated. Recommended replacement: "
                    f"'{replacement}'. Consider updating your workflow."
                )
            return f"Skill '{name}' is deprecated. It may be removed in a future update."
    return None
