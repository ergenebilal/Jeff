"""Eval senaryo 018: Recovery — API fallback."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from brain.phase4.eval_engine import EvalEngine

def test_recover_api_fallback():
    engine = EvalEngine()
    scenario = {"name": "recover_api_fallback", "category": "recovery",
                "input": "Fallback to backup model on API failure",
                "expected": {"task": "success", "recovery_result": "fallback"}}
    def exec_fn(s):
        return {"success": True, "metrics": {"recovery_result": "fallback",
                                              "fallback_model": "claude-haiku-4-5",
                                              "policy_compliance": True, "retrieval_hit": False}}
    result = engine.run(scenario, executor=exec_fn)
    assert result["success"] is True
    assert result["metrics"]["recovery_result"] == "fallback"
