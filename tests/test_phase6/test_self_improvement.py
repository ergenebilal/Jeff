"""Tests for Phase 6 self_improvement module."""

from brain.phase6.self_improvement import analyze_lessons, analyze_skills, generate_patch_plan


def test_analyze_lessons_no_data(monkeypatch):
    monkeypatch.setattr("brain.phase6.self_improvement.get_recent_lessons", lambda **kw: [])
    result = analyze_lessons()
    assert result["total_lessons"] == 0
    assert "patterns" in result


def test_analyze_skills_no_data(monkeypatch, tmp_path):
    fake_log = tmp_path / "empty_skills.jsonl"
    monkeypatch.setattr("brain.phase6.self_improvement.SKILLS_LOG", fake_log)
    result = analyze_skills()
    assert result["total"] == 0


def test_generate_patch_plan():
    result = generate_patch_plan()
    assert "patches" in result
    assert "summary" in result
    assert "priority" in result
    assert len(result["patches"]) >= 1
