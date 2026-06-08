"""Tests for Phase 4 eval_daily module."""

import json
from pathlib import Path

from brain.phase4.eval_daily import (
    CATEGORIES,
    _read_agent_runs,
    get_latest_scores,
    run_daily_eval,
)


def _seed_agent_runs(path: Path, runs: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    for r in runs:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(r) + "\n")


def test_run_daily_eval_creates_results(monkeypatch, tmp_path):
    fake_runs = tmp_path / "agent_runs.jsonl"
    _seed_agent_runs(fake_runs, [
        {"timestamp": "2026-06-08T10:00:00+00:00", "error": None, "source": "terminal", "tokens": 500},
        {"timestamp": "2026-06-08T11:00:00+00:00", "error": "timeout", "source": "cron", "tokens": 2000, "recovered": True},
    ])
    monkeypatch.setattr("brain.phase4.eval_daily.AGENT_RUNS_LOG", fake_runs)

    results = run_daily_eval(hours=48)

    assert len(results) == len(CATEGORIES)
    for r in results:
        assert "category" in r
        assert "success" in r
        assert "run_count" in r
    cats = {r["category"] for r in results}
    assert cats == set(CATEGORIES)


def test_run_daily_eval_empty_log(monkeypatch, tmp_path):
    fake_runs = tmp_path / "agent_runs.jsonl"
    fake_runs.parent.mkdir(parents=True, exist_ok=True)
    fake_runs.write_text("", encoding="utf-8")
    monkeypatch.setattr("brain.phase4.eval_daily.AGENT_RUNS_LOG", fake_runs)

    results = run_daily_eval()

    assert len(results) == len(CATEGORIES)
    for r in results:
        assert r["success"] is False
        assert r["run_count"] == 0


def test_run_daily_eval_missing_log(monkeypatch, tmp_path):
    fake_runs = tmp_path / "nonexistent.jsonl"
    monkeypatch.setattr("brain.phase4.eval_daily.AGENT_RUNS_LOG", fake_runs)

    results = run_daily_eval()

    assert len(results) == len(CATEGORIES)
    for r in results:
        assert r["run_count"] == 0


def test_run_daily_eval_custom_executor(monkeypatch, tmp_path):
    fake_runs = tmp_path / "agent_runs.jsonl"
    _seed_agent_runs(fake_runs, [
        {"timestamp": "2026-06-08T10:00:00+00:00"},
    ])
    monkeypatch.setattr("brain.phase4.eval_daily.AGENT_RUNS_LOG", fake_runs)

    results = run_daily_eval(
        hours=48,
        executors={"log_analysis": lambda runs: {"success": True, "metrics": {"custom": 42}}},
    )

    log_analysis = [r for r in results if r["category"] == "log_analysis"][0]
    assert log_analysis["metrics"]["custom"] == 42


def test_get_latest_scores(monkeypatch, tmp_path):
    fake_log = tmp_path / "eval_daily.jsonl"
    monkeypatch.setattr("brain.phase4.eval_daily.EVAL_DAILY_LOG", fake_log)

    # Run eval to populate the log
    fake_runs = tmp_path / "agent_runs.jsonl"
    _seed_agent_runs(fake_runs, [
        {"timestamp": "2026-06-08T10:00:00+00:00", "source": "terminal", "tokens": 100},
    ])
    monkeypatch.setattr("brain.phase4.eval_daily.AGENT_RUNS_LOG", fake_runs)
    run_daily_eval(hours=48)

    scores = get_latest_scores()
    assert len(scores) == len(CATEGORIES)
    for cat in CATEGORIES:
        assert cat in scores


def test_read_agent_runs_filters_by_hours(monkeypatch, tmp_path):
    fake_runs = tmp_path / "agent_runs.jsonl"
    import datetime as dt
    now = dt.datetime.now(dt.timezone.utc)
    _seed_agent_runs(fake_runs, [
        {"timestamp": (now - dt.timedelta(hours=1)).isoformat()},
        {"timestamp": (now - dt.timedelta(hours=3)).isoformat()},
        {"timestamp": (now - dt.timedelta(hours=25)).isoformat()},
    ])
    monkeypatch.setattr("brain.phase4.eval_daily.AGENT_RUNS_LOG", fake_runs)

    runs = _read_agent_runs(hours=24)
    assert len(runs) == 2
