"""Tests for brain/github_tracker.py."""

import json
from datetime import datetime, timezone
from pathlib import Path

from brain.github_tracker import (
    run_weekly_tracker,
    get_latest_report,
    summarize_report,
    _evaluate_repo,
)


def test_evaluate_repo_useful():
    repo = {
        "full_name": "test/hermes-project",
        "stargazers_count": 50,
        "description": "A useful Hermes project for testing",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "pushed_at": datetime.now(timezone.utc).isoformat(),
        "html_url": "https://github.com/test/hermes-project",
        "language": "Python",
        "topics": ["hermes"],
        "owner": {"login": "test"},
    }
    result = _evaluate_repo(repo)
    assert result["decision"] == "faydali"
    assert result["stars"] == 50
    assert len(result["reasons"]) == 0


def test_evaluate_repo_too_few_stars():
    repo = {
        "full_name": "test/hermes-old",
        "stargazers_count": 2,
        "description": "A small project",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "pushed_at": datetime.now(timezone.utc).isoformat(),
        "html_url": "https://github.com/test/hermes-old",
        "language": "Python",
        "topics": [],
        "owner": {"login": "test"},
    }
    result = _evaluate_repo(repo)
    assert result["decision"] == "faydasiz"
    assert "yildiz" in result["reasons"][0]


def test_evaluate_repo_stale():
    repo = {
        "full_name": "test/hermes-stale",
        "stargazers_count": 50,
        "description": "A stale project",
        "updated_at": "2020-01-01T00:00:00Z",
        "pushed_at": "2020-01-01T00:00:00Z",
        "html_url": "https://github.com/test/hermes-stale",
        "language": "Python",
        "topics": [],
        "owner": {"login": "test"},
    }
    result = _evaluate_repo(repo)
    assert result["decision"] == "faydasiz"
    assert "guncelleme" in result["reasons"][0]


def test_evaluate_repo_no_description():
    repo = {
        "full_name": "test/hermes-nodesc",
        "stargazers_count": 50,
        "description": "",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "pushed_at": datetime.now(timezone.utc).isoformat(),
        "html_url": "https://github.com/test/hermes-nodesc",
        "language": "Python",
        "topics": [],
        "owner": {"login": "test"},
    }
    result = _evaluate_repo(repo)
    assert result["decision"] == "faydasiz"
    assert "aciklama" in result["reasons"][0]


def test_get_latest_report_none(tmp_path, monkeypatch):
    monkeypatch.setattr("brain.github_tracker.REPORT_FILE", tmp_path / "nonexistent.json")
    assert get_latest_report() is None


def test_get_latest_report_with_data(tmp_path, monkeypatch):
    fake = tmp_path / "github_weekly.json"
    fake.write_text(json.dumps({"timestamp": "2026-01-01T00:00:00Z", "summary": {"total_projects": 5}}), encoding="utf-8")
    monkeypatch.setattr("brain.github_tracker.REPORT_FILE", fake)
    report = get_latest_report()
    assert report is not None
    assert report["summary"]["total_projects"] == 5


def test_summarize_report_empty():
    result = summarize_report(None)
    assert "Henuz" in result or "yok" in result


def test_summarize_report_with_data():
    report = {
        "timestamp": "2026-01-01T00:00:00Z",
        "summary": {"total_projects": 10, "useful": 3, "faydasiz": 7, "incelenmeli": 0},
        "top_picks": [{"name": "a/hermes"}, {"name": "b/hermes"}, {"name": "c/hermes"}],
    }
    result = summarize_report(report)
    assert "10" in result
    assert "3" in result
    assert "a/hermes" in result


def test_github_tracker_summary_in_cron(monkeypatch, tmp_path):
    """Ensure brain.phase5.cron_summary.github_tracker_summary works."""
    from brain.phase5.cron_summary import github_tracker_summary

    # Point report to empty path
    monkeypatch.setattr("brain.github_tracker.REPORT_FILE", tmp_path / "empty.json")
    result = github_tracker_summary()
    assert "yok" in result or "degil" in result or "hata" in result
