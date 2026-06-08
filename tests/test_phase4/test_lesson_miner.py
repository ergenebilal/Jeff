"""Tests for Phase 4 lesson_miner module."""

import json
from pathlib import Path

from brain.phase4.lesson_miner import mine_from_eval, mine_from_runs, run_full_mine


def _seed_jsonl(path: Path, entries: list):
    path.parent.mkdir(parents=True, exist_ok=True)
    for e in entries:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(e) + "\n")


def test_mine_from_eval_empty(monkeypatch, tmp_path):
    fake_log = tmp_path / "eval_daily.jsonl"
    monkeypatch.setattr("brain.phase4.lesson_miner.EVAL_DAILY_LOG", fake_log)

    count = mine_from_eval()
    assert count == 0


def test_mine_from_eval_failures(monkeypatch, tmp_path):
    fake_log = tmp_path / "eval_daily.jsonl"
    _seed_jsonl(fake_log, [
        {"category": "log_analysis", "success": False, "error": "parse error"},
        {"category": "retrieval", "success": False, "error": "timeout"},
        {"category": "token_budget", "success": True},
    ])
    monkeypatch.setattr("brain.phase4.lesson_miner.EVAL_DAILY_LOG", fake_log)

    # Patch save_lesson to avoid writing to real ~/.hermes
    saved = []
    def fake_save(category, trigger, lesson, **kw):
        saved.append({"category": category, "trigger": trigger})
    monkeypatch.setattr("brain.phase4.lesson_miner.save_lesson", fake_save)

    count = mine_from_eval()
    assert count == 2


def test_mine_from_runs_empty(monkeypatch, tmp_path):
    fake_log = tmp_path / "agent_runs.jsonl"
    monkeypatch.setattr("brain.phase4.lesson_miner.AGENT_RUNS_LOG", fake_log)

    count = mine_from_runs()
    assert count == 0


def test_mine_from_runs_with_errors(monkeypatch, tmp_path):
    fake_log = tmp_path / "agent_runs.jsonl"
    _seed_jsonl(fake_log, [
        {"source": "terminal", "error": "timeout"},
        {"source": "cron", "error": "connection refused"},
        {"source": "terminal", "error": None},
    ])
    monkeypatch.setattr("brain.phase4.lesson_miner.AGENT_RUNS_LOG", fake_log)

    saved = []
    def fake_save(category, trigger, lesson, **kw):
        saved.append({"category": category, "trigger": trigger})
    monkeypatch.setattr("brain.phase4.lesson_miner.save_lesson", fake_save)

    count = mine_from_runs()
    assert count == 2


def test_run_full_mine(monkeypatch, tmp_path):
    fake_eval = tmp_path / "eval_daily.jsonl"
    fake_runs = tmp_path / "agent_runs.jsonl"
    _seed_jsonl(fake_eval, [{"category": "cron", "success": False, "error": "fail"}])
    _seed_jsonl(fake_runs, [{"source": "terminal", "error": "err"}])

    monkeypatch.setattr("brain.phase4.lesson_miner.EVAL_DAILY_LOG", fake_eval)
    monkeypatch.setattr("brain.phase4.lesson_miner.AGENT_RUNS_LOG", fake_runs)

    saved = []
    def fake_save(category, trigger, lesson, **kw):
        saved.append({"category": category})
    monkeypatch.setattr("brain.phase4.lesson_miner.save_lesson", fake_save)

    result = run_full_mine()
    assert result["total"] == 2
