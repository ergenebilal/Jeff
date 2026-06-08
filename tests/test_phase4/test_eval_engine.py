"""Tests for Phase 4 eval_engine module."""

import json
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))


def _import_and_patch(monkeypatch, tmp_path):
    """Import eval_engine and patch EVAL_LOG to a temp path."""
    import brain.phase4.eval_engine as ee
    fake_log = tmp_path / "eval_results.jsonl"
    fake_log.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(ee, "EVAL_LOG", fake_log)
    return ee


def test_eval_engine_run_basic(monkeypatch):
    ee = _import_and_patch(monkeypatch, Path(tempfile.mkdtemp()))
    engine = ee.EvalEngine()
    scenario = {"name": "test-scenario", "category": "log_analysis", "input": "test input"}
    result = engine.run(scenario)
    assert result["success"] is True
    assert result["name"] == "test-scenario"
    assert result["category"] == "log_analysis"


def test_eval_engine_run_with_executor(monkeypatch):
    ee = _import_and_patch(monkeypatch, Path(tempfile.mkdtemp()))
    engine = ee.EvalEngine()
    scenario = {"name": "custom", "category": "recovery", "input": "test"}

    def executor(s):
        return {"success": True, "metrics": {"recovery_result": "ok", "policy_compliance": True}}

    result = engine.run(scenario, executor=executor)
    assert result["success"] is True
    assert result["metrics"]["recovery_result"] == "ok"
    assert result["metrics"]["policy_compliance"] is True


def test_eval_engine_logs_result(monkeypatch):
    ee = _import_and_patch(monkeypatch, Path(tempfile.mkdtemp()))
    engine = ee.EvalEngine()
    scenario = {"name": "logged-scenario", "category": "cron", "input": "trigger"}
    engine.run(scenario)

    assert ee.EVAL_LOG.exists()
    lines = ee.EVAL_LOG.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["name"] == "logged-scenario"
    assert entry["category"] == "cron"


def test_eval_engine_executor_exception(monkeypatch):
    ee = _import_and_patch(monkeypatch, Path(tempfile.mkdtemp()))
    engine = ee.EvalEngine()
    scenario = {"name": "broken", "category": "root_cause", "input": "crash"}

    def failing(s):
        raise ValueError("simulated failure")

    result = engine.run(scenario, executor=failing)
    assert result["success"] is False
    assert "simulated failure" in result["error"]


def test_run_eval_scenario_helper(monkeypatch):
    ee = _import_and_patch(monkeypatch, Path(tempfile.mkdtemp()))
    scenario = {"name": "helper-test", "category": "token_budget", "input": "check"}
    result = ee.run_eval_scenario(scenario)
    assert result["success"] is True


def test_eval_report_generation():
    from brain.phase4.eval_engine import eval_report

    results = [
        {"name": "s1", "category": "log_analysis", "success": True, "metrics": {}},
        {"name": "s2", "category": "root_cause", "success": False, "error": "timeout",
         "metrics": {}},
    ]
    report = eval_report(results)
    assert "EVAL REPORT" in report
    assert "Passed: 1" in report
    assert "Failed: 1" in report
    assert "PASS" in report
    assert "FAIL" in report
    assert "timeout" in report


def test_eval_report_detail_metrics():
    from brain.phase4.eval_engine import eval_report

    results = [
        {"name": "s1", "category": "retrieval", "success": True,
         "metrics": {"retrieval_hit": True, "policy_compliance": 1.0, "recovery_result": "ok"}},
    ]
    report = eval_report(results)
    assert "retrieval_hit=True" in report
    assert "policy_compliance=1.0" in report
    assert "recovery_result=ok" in report


def test_builtin_scenarios_exist():
    from brain.phase4.eval_engine import BUILTIN_SCENARIOS

    assert len(BUILTIN_SCENARIOS) == 20


def test_builtin_scenarios_all_categories():
    from brain.phase4.eval_engine import BUILTIN_SCENARIOS

    categories = set(s["category"] for s in BUILTIN_SCENARIOS)
    expected = {"log_analysis", "root_cause", "retrieval", "skill_reuse",
                "policy_compliance", "cron", "token_budget", "recovery"}
    assert categories == expected


def test_builtin_scenarios_all_pass_with_executor(monkeypatch):
    ee = _import_and_patch(monkeypatch, Path(tempfile.mkdtemp()))
    engine = ee.EvalEngine()
    results = []
    for scenario in ee.BUILTIN_SCENARIOS:
        s_copy = dict(scenario)
        executor = s_copy.pop("executor", None)
        result = engine.run(s_copy, executor=executor)
        results.append(result)

    passed = sum(1 for r in results if r["success"])
    assert passed == 20, f"Only {passed}/20 passed"
