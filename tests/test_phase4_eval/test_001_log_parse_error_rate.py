"""Eval senaryo 001: Log analizi — hata oranı çıkarma."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from brain.phase4.eval_engine import EvalEngine

def test_log_parse_error_rate():
    engine = EvalEngine()
    scenario = {"name": "log_parse_error_rate", "category": "log_analysis",
                "input": "Parse error rate from agent_runs.jsonl",
                "expected": {"task": "success", "metric": "error_rate"}}
    def exec_fn(s):
        return {"success": True, "metrics": {"error_rate": 0.03, "policy_compliance": True,
                                              "retrieval_hit": False, "recovery_result": None}}
    result = engine.run(scenario, executor=exec_fn)
    assert result["success"] is True
    assert result["metrics"]["error_rate"] == 0.03
