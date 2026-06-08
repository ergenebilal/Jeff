"""Tests for Phase 4 skill_advisor module."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from brain.phase4.skill_advisor import (
    GOLDEN_THRESHOLD_USAGE,
    auto_deprecate,
    deprecation_warning,
    find_deprecation_candidates,
    get_golden_skills,
)


def _seed_skills_log(path: Path, entries: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    for e in entries:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(e) + "\n")


def test_get_golden_skills_empty(monkeypatch, tmp_path):
    fake_log = tmp_path / "skills.jsonl"
    monkeypatch.setattr("brain.phase4.skill_advisor.SKILLS_LOG", fake_log)

    golden = get_golden_skills()
    assert golden == []


def test_get_golden_skills_finds_top_performers(monkeypatch, tmp_path):
    fake_log = tmp_path / "skills.jsonl"
    now = datetime.now(timezone.utc).isoformat()
    _seed_skills_log(fake_log, [
        {"name": "code_review", "stage": "active", "profile": "default", "timestamp": now},
        {"name": "code_review", "stage": "active", "profile": "default", "timestamp": now},
        {"name": "code_review", "stage": "active", "profile": "default", "timestamp": now},
        {"name": "code_review", "stage": "active", "profile": "default", "timestamp": now},
        {"name": "code_review", "stage": "active", "profile": "default", "timestamp": now},
        {"name": "code_review", "stage": "active", "profile": "default", "timestamp": now},
        {"name": "buggy_skill", "stage": "error", "profile": "default", "timestamp": now},
        {"name": "buggy_skill", "stage": "error", "profile": "default", "timestamp": now},
        {"name": "buggy_skill", "stage": "active", "profile": "default", "timestamp": now},
    ])
    monkeypatch.setattr("brain.phase4.skill_advisor.SKILLS_LOG", fake_log)

    golden = get_golden_skills()
    names = [g["name"] for g in golden]
    assert "code_review" in names
    assert "buggy_skill" not in names


def test_find_deprecation_candidates_stale(monkeypatch, tmp_path):
    fake_log = tmp_path / "skills.jsonl"
    old_ts = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    now = datetime.now(timezone.utc).isoformat()
    # old_skill: 1 active + 4 error = 20% success rate → below STALE_SUCCESS_RATE (0.3)
    _seed_skills_log(fake_log, [
        {"name": "old_skill", "stage": "active", "profile": "default", "timestamp": old_ts},
        {"name": "old_skill", "stage": "error", "profile": "default", "timestamp": old_ts},
        {"name": "old_skill", "stage": "error", "profile": "default", "timestamp": old_ts},
        {"name": "old_skill", "stage": "error", "profile": "default", "timestamp": old_ts},
        {"name": "old_skill", "stage": "error", "profile": "default", "timestamp": old_ts},
        # active skill with recent usage should NOT be a candidate
        {"name": "fresh_skill", "stage": "active", "profile": "default", "timestamp": now},
    ])
    monkeypatch.setattr("brain.phase4.skill_advisor.SKILLS_LOG", fake_log)

    candidates = find_deprecation_candidates()
    names = [c["name"] for c in candidates]
    assert "old_skill" in names
    assert "fresh_skill" not in names


def test_find_deprecation_candidates_low_success(monkeypatch, tmp_path):
    fake_log = tmp_path / "skills.jsonl"
    now = datetime.now(timezone.utc).isoformat()
    _seed_skills_log(fake_log, [
        {"name": "failing_skill", "stage": "error", "profile": "default", "timestamp": now},
        {"name": "failing_skill", "stage": "error", "profile": "default", "timestamp": now},
        {"name": "failing_skill", "stage": "error", "profile": "default", "timestamp": now},
        {"name": "failing_skill", "stage": "error", "profile": "default", "timestamp": now},
        {"name": "failing_skill", "stage": "error", "profile": "default", "timestamp": now},
        {"name": "failing_skill", "stage": "error", "profile": "default", "timestamp": now},
        {"name": "failing_skill", "stage": "active", "profile": "default", "timestamp": now},
    ])
    monkeypatch.setattr("brain.phase4.skill_advisor.SKILLS_LOG", fake_log)

    candidates = find_deprecation_candidates()
    names = [c["name"] for c in candidates]
    assert "failing_skill" in names


def test_auto_deprecate_dry_run(monkeypatch, tmp_path):
    fake_log = tmp_path / "skills.jsonl"
    old_ts = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    _seed_skills_log(fake_log, [
        {"name": "stale_skill", "stage": "error", "profile": "default", "timestamp": old_ts},
        {"name": "stale_skill", "stage": "error", "profile": "default", "timestamp": old_ts},
    ])
    monkeypatch.setattr("brain.phase4.skill_advisor.SKILLS_LOG", fake_log)

    results = auto_deprecate(dry_run=True)
    assert len(results) >= 1
    assert results[0]["action"] == "would_deprecate"


def test_deprecation_warning_returns_none_for_active(monkeypatch, tmp_path):
    from brain.phase4.skill_lifecycle import SKILLS_LOG as REAL_LOG

    fake_log = tmp_path / "skills.jsonl"
    monkeypatch.setattr("brain.phase4.skill_advisor.SKILLS_LOG", fake_log)
    # Also patch skill_lifecycle.SKILLS_LOG so get_stage works
    monkeypatch.setattr("brain.phase4.skill_lifecycle.SKILLS_LOG", fake_log)

    now = datetime.now(timezone.utc).isoformat()
    _seed_skills_log(fake_log, [
        {"name": "good_skill", "stage": "active", "profile": "default", "timestamp": now},
    ])

    warning = deprecation_warning("good_skill", "default")
    assert warning is None


def test_deprecation_warning_with_replacement(monkeypatch, tmp_path):
    fake_log = tmp_path / "skills.jsonl"
    monkeypatch.setattr("brain.phase4.skill_advisor.SKILLS_LOG", fake_log)
    monkeypatch.setattr("brain.phase4.skill_lifecycle.SKILLS_LOG", fake_log)

    now = datetime.now(timezone.utc).isoformat()
    _seed_skills_log(fake_log, [
        {"name": "old_api", "stage": "deprecated", "profile": "default",
         "replacement": "new_api", "timestamp": now},
    ])

    warning = deprecation_warning("old_api", "default")
    assert warning is not None
    assert "new_api" in warning
    assert "deprecated" in warning
