"""Tests for Phase 4 skill_lifecycle module."""

import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def sl(monkeypatch):
    """Import skill_lifecycle and isolate its log path."""
    import brain.phase4.skill_lifecycle as sl
    fake_log = Path(tempfile.mkdtemp()) / "skills.jsonl"
    fake_log.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(sl, "SKILLS_LOG", fake_log)
    return sl


def test_register_skill(sl):
    entry = sl.SkillLifecycle.register("test-skill", profile="default")
    assert entry["name"] == "test-skill"
    assert entry["stage"] == "active"
    assert entry["profile"] == "default"


def test_register_with_custom_profile(sl):
    entry = sl.SkillLifecycle.register("work-skill", profile="work")
    assert entry["profile"] == "work"


def test_register_fallback_invalid_profile(sl):
    entry = sl.SkillLifecycle.register("bad-skill", profile="invalid")
    assert entry["profile"] == "default"


def test_transition_to_deprecated(sl):
    sl.SkillLifecycle.register("old-skill", profile="default")
    result = sl.SkillLifecycle.transition("old-skill", "deprecated", profile="default")
    assert result["stage"] == "deprecated"
    assert result["success"] is True


def test_transition_requires_replacement(sl):
    sl.SkillLifecycle.register("old-skill", profile="default")
    sl.SkillLifecycle.register("new-skill", profile="default")
    result = sl.SkillLifecycle.transition("old-skill", "deprecated", profile="default",
                                          replacement="new-skill")
    assert result["success"] is True
    assert result["replacement"] == "new-skill"


def test_transition_missing_replacement_fails(sl):
    sl.SkillLifecycle.register("old-skill", profile="default")
    result = sl.SkillLifecycle.transition("old-skill", "deprecated", profile="default",
                                          replacement="nonexistent")
    assert result["success"] is False
    assert "Replacement" in result.get("error", "")


def test_transition_to_archived_requires_deprecated_first(sl):
    sl.SkillLifecycle.register("skill", profile="default")
    result = sl.SkillLifecycle.transition("skill", "archived", profile="default")
    assert result["success"] is False
    assert "deprecated" in result.get("error", "")


def test_transition_deprecated_then_archived(sl):
    sl.SkillLifecycle.register("skill", profile="default")
    sl.SkillLifecycle.transition("skill", "deprecated", profile="default")
    result = sl.SkillLifecycle.transition("skill", "archived", profile="default")
    assert result["success"] is True
    assert result["stage"] == "archived"


def test_delete_archived_skill(sl):
    sl.SkillLifecycle.register("skill-to-delete", profile="default")
    sl.SkillLifecycle.transition("skill-to-delete", "deprecated", profile="default")
    sl.SkillLifecycle.transition("skill-to-delete", "archived", profile="default")
    result = sl.SkillLifecycle.delete("skill-to-delete", profile="default")
    assert result["success"] is True
    assert result["stage"] == "deleted"


def test_delete_active_skill_fails(sl):
    sl.SkillLifecycle.register("active-skill", profile="default")
    result = sl.SkillLifecycle.delete("active-skill", profile="default")
    assert result["success"] is False


def test_delete_force_works(sl):
    sl.SkillLifecycle.register("forced-skill", profile="default")
    result = sl.SkillLifecycle.delete("forced-skill", profile="default", force=True)
    assert result["success"] is True


def test_get_stage(sl):
    sl.SkillLifecycle.register("test", profile="default")
    assert sl.SkillLifecycle.get_stage("test") == "active"
    assert sl.SkillLifecycle.get_stage("nonexistent") == "not_found"


def test_list_by_profile(sl):
    sl.SkillLifecycle.register("skill-a", profile="default")
    sl.SkillLifecycle.register("skill-b", profile="default")
    sl.SkillLifecycle.register("skill-c", profile="work")

    default_skills = sl.SkillLifecycle.list_by_profile("default")
    assert len(default_skills) == 2
    work_skills = sl.SkillLifecycle.list_by_profile("work")
    assert len(work_skills) == 1


def test_validate_profile_isolation(sl):
    sl.SkillLifecycle.register("default-skill", profile="default")
    sl.SkillLifecycle.register("work-skill", profile="work")
    sl.SkillLifecycle.register("personal-skill", profile="personal")

    result = sl.SkillLifecycle.validate_profile_isolation()
    assert result["isolated"] is True
    assert "default" in result["profiles"]
    assert "work" in result["profiles"]
    assert "personal" in result["profiles"]


def test_skill_stage_summary(sl):
    sl.SkillLifecycle.register("skill-1", profile="default")
    sl.SkillLifecycle.register("skill-2", profile="default")
    summary = sl.skill_stage_summary()
    assert summary.get("active", 0) >= 2
