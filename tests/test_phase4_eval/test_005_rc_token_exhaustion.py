"""Eval senaryo 005: Root cause — token exhaustion."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from brain.phase4.eval_engine import EvalEngine

def test_rc_token_exhaustion():
    engine = EvalEngine()
    scenario = {"name": "rc_token_exhaustion", "category": "root_cause",
                "input": "Root cause: token budget exhaustion in token_budget.jsonl",
                "expected": {"task": "success", "cause": "identified"}}
    def exec_fn(s):
        return {"success": True, "metrics": {"cause": "token_exhaustion", "confidence": 0.85,
                                              "policy_compliance": True, "retrieval_hit": False,
                                              "recovery_result": None}}
    result = engine.run(scenario, executor=exec_fn)
    assert result["success"] is True
    assert result["metrics"]["cause"] == "token_exhaustion"
