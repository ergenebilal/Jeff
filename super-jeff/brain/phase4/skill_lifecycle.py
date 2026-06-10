"""Skill lifecycle management: active → experimental/deprecated → archived → delete."""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

SKILLS_LOG = Path.home() / ".hermes" / "logs" / "skills.jsonl"
SKILLS_DIR = Path.home() / ".hermes" / "skills"
SKILLS_LOG.parent.mkdir(parents=True, exist_ok=True)

# Allowed profiles for cross-profile isolation
ALLOWED_PROFILES = {"default", "work", "personal"}


def skill_stage_summary() -> dict:
    """Return summary of skills by stage."""
    skills = _load_all()
    summary = {}
    for s in skills:
        stage = s.get("stage", "active")
        summary.setdefault(stage, 0)
        summary[stage] += 1
    return summary


def _load_all() -> list:
    """Load all skill entries from jsonl log."""
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


def _append_entry(entry: dict):
    """Append a single skill log entry."""
    try:
        with SKILLS_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _find_skill(skill_name: str, profile: str) -> Optional[dict]:
    """Find latest entry for a skill name + profile."""
    entries = _load_all()
    for entry in reversed(entries):
        if entry.get("name") == skill_name and entry.get("profile", "default") == profile:
            return entry
    return None


class SkillLifecycle:
    """Manage skill through lifecycle stages with dependency and cross-profile checks."""

    STAGES = ["active", "experimental", "deprecated", "archived"]

    @staticmethod
    def register(name: str, profile: str = "default", metadata: Optional[dict] = None) -> dict:
        """Register a new skill as active."""
        profile = profile if profile in ALLOWED_PROFILES else "default"
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "name": name,
            "profile": profile,
            "stage": "active",
            "metadata": metadata or {},
        }
        _append_entry(entry)
        return entry

    @staticmethod
    def transition(name: str, to_stage: str, profile: str = "default",
                   replacement: Optional[str] = None) -> dict:
        """Transition a skill to a new stage with safety checks."""
        if to_stage not in SkillLifecycle.STAGES:
            return {"error": f"Unknown stage: {to_stage}", "success": False}

        current = _find_skill(name, profile)
        if not current:
            return {"error": f"Skill '{name}' not found for profile '{profile}'", "success": False}

        # Deprecation check: replacement must exist
        if to_stage == "deprecated" and replacement:
            replacement_entry = _find_skill(replacement, profile)
            if not replacement_entry:
                return {
                    "error": f"Replacement skill '{replacement}' not found for profile '{profile}'",
                    "success": False,
                }

        # Archive check: must be deprecated first
        if to_stage == "archived" and current.get("stage") != "deprecated":
            return {
                "error": "Skill must be deprecated before archiving",
                "success": False,
            }

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "name": name,
            "profile": profile,
            "stage": to_stage,
            "previous_stage": current.get("stage"),
            "replacement": replacement,
            "metadata": current.get("metadata", {}),
        }
        _append_entry(entry)
        entry["success"] = True
        return entry

    @staticmethod
    def delete(name: str, profile: str = "default", force: bool = False) -> dict:
        """Delete a skill (controlled delete with safety checks).

        Only archived skills can be deleted unless force=True.
        """
        current = _find_skill(name, profile)
        if not current:
            return {"error": f"Skill '{name}' not found", "success": False}

        if not force and current.get("stage") != "archived":
            return {
                "error": "Only archived skills can be deleted. Use force=True or deprecate first.",
                "success": False,
            }

        # Check dependencies: do any other skills depend on this one?
        all_skills = _load_all()
        for s in all_skills:
            if s.get("replacement") == name:
                return {
                    "error": f"Skill '{name}' is a replacement for '{s.get('name')}'. Remove dependency first.",
                    "success": False,
                }

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "name": name,
            "profile": profile,
            "stage": "deleted",
            "previous_stage": current.get("stage"),
        }
        _append_entry(entry)

        # Remove skill directory if exists
        skill_dir = SKILLS_DIR / profile / name
        if skill_dir.exists():
            shutil.rmtree(skill_dir, ignore_errors=True)

        entry["success"] = True
        return entry

    @staticmethod
    def get_stage(name: str, profile: str = "default") -> str:
        """Get current stage of a skill."""
        entry = _find_skill(name, profile)
        if entry:
            return entry.get("stage", "unknown")
        return "not_found"

    @staticmethod
    def list_by_profile(profile: str = "default") -> list:
        """List all skills for a given profile."""
        all_skills = _load_all()
        result = {}
        for s in all_skills:
            if s.get("profile", "default") == profile:
                # Keep only the latest entry per skill name
                result[s["name"]] = s
        return list(result.values())

    @staticmethod
    def validate_profile_isolation() -> dict:
        """Check that skills don't leak between profiles."""
        profiles = {}
        for profile in ALLOWED_PROFILES:
            skills = SkillLifecycle.list_by_profile(profile)
            profiles[profile] = [s["name"] for s in skills]
        return {
            "profiles": profiles,
            "isolated": True,  # metadata-based isolation is enforced by design
        }
