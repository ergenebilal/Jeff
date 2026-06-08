"""Eval senaryo 006: Root cause — API timeout."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from brain.phase4.eval_engine import EvalEngine

def test_rc_api_timeout():
    engine = EvalEngine()
    scenario = {"name": "rc_api_timeout", "category": "root_cause",
                "input": "Root cause: API timeout from model provider",
                "expected": {"task": "success", "cause": "identified"}}
    def exec_fn(s):
        return {"success": True, "metrics": {"cause": "api_timeout", "confidence": 0.95,
                                              "policy_compliance": True, "retrieval_hit": False,
                                              "recovery_result": None}}
    result = engine.run(scenario, executor=exec_fn)
    assert result["success"] is True
    assert result["metrics"]["cause"] == "api_timeout"
