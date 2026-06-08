"""Tests for Phase 4 token_report module."""

import json
from pathlib import Path

from brain.phase4.token_report import (
    _read_token_log,
    generate_weekly_report,
    tune_compression_strategy,
)


def _seed_token_log(path: Path, entries: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    for e in entries:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(e) + "\n")


def test_generate_weekly_report_empty(monkeypatch, tmp_path):
    fake_log = tmp_path / "token_budget.jsonl"
    monkeypatch.setattr("brain.phase4.token_report.BUDGET_LOG", fake_log)

    report = generate_weekly_report(hours=168)

    assert report["total_entries"] == 0
    assert "No token data" in report["recommendations"][0]


def test_generate_weekly_report_with_data(monkeypatch, tmp_path):
    fake_log = tmp_path / "token_budget.jsonl"
    _seed_token_log(fake_log, [
        {"tokens": 50000, "mode": "quick", "action": "eval", "timestamp": "2026-06-07T10:00:00+00:00"},
        {"tokens": 3000, "mode": "deep", "action": "research", "timestamp": "2026-06-07T11:00:00+00:00"},
        {"tokens": 1000, "mode": "quick", "action": "chat", "timestamp": "2026-06-08T10:00:00+00:00"},
    ])
    monkeypatch.setattr("brain.phase4.token_report.BUDGET_LOG", fake_log)

    report = generate_weekly_report(hours=168)

    assert report["total_entries"] == 3
    assert report["total_tokens"] == 54000
    assert len(report["top_expensive"]) == 3
    assert report["top_expensive"][0]["tokens"] == 50000
    assert "quick" in report["mode_overflows"]


def test_generate_weekly_report_overflow_detection(monkeypatch, tmp_path):
    fake_log = tmp_path / "token_budget.jsonl"
    # 3 quick entries, 2 overflow the 40K hard limit
    _seed_token_log(fake_log, [
        {"tokens": 45000, "mode": "quick", "action": "big_eval", "timestamp": "2026-06-07T10:00:00+00:00"},
        {"tokens": 50000, "mode": "quick", "action": "big_eval", "timestamp": "2026-06-07T11:00:00+00:00"},
        {"tokens": 500, "mode": "quick", "action": "small_chat", "timestamp": "2026-06-08T10:00:00+00:00"},
    ])
    monkeypatch.setattr("brain.phase4.token_report.BUDGET_LOG", fake_log)

    report = generate_weekly_report(hours=168)

    quick_stats = report["mode_overflows"]["quick"]
    assert quick_stats["overflows"] == 2
    assert quick_stats["count"] == 3
    assert len(report["recommendations"]) > 0


def test_tune_compression_strategy_empty(monkeypatch, tmp_path):
    fake_log = tmp_path / "token_budget.jsonl"
    monkeypatch.setattr("brain.phase4.token_report.BUDGET_LOG", fake_log)

    result = tune_compression_strategy(hours=168)

    assert result["strategy"] == "default"


def test_tune_compression_strategy_with_data(monkeypatch, tmp_path):
    fake_log = tmp_path / "token_budget.jsonl"
    _seed_token_log(fake_log, [
        {"tokens": 95000, "mode": "deep", "action": "research", "timestamp": "2026-06-07T10:00:00+00:00"},
    ])
    monkeypatch.setattr("brain.phase4.token_report.BUDGET_LOG", fake_log)

    result = tune_compression_strategy(hours=168)

    assert result["strategy"] == "tuned"
    assert "deep" in result["suggestions"]


def test_read_token_log_filters_by_hours(monkeypatch, tmp_path):
    import datetime as dt
    now = dt.datetime.now(dt.timezone.utc)
    fake_log = tmp_path / "token_budget.jsonl"
    _seed_token_log(fake_log, [
        {"tokens": 100, "timestamp": (now - dt.timedelta(hours=1)).isoformat()},
        {"tokens": 200, "timestamp": (now - dt.timedelta(hours=100)).isoformat()},
    ])
    monkeypatch.setattr("brain.phase4.token_report.BUDGET_LOG", fake_log)

    entries = _read_token_log(hours=48)
    assert len(entries) == 1
