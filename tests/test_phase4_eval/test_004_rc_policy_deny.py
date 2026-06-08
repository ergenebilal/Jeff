"""Eval senaryo 004: Root cause — policy deny analizi."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from brain.phase4.eval_engine import EvalEngine

def test_rc_policy_deny():
    engine = EvalEngine()
    scenario = {"name": "rc_policy_deny", "category": "root_cause",
                "input": "Root cause: autonomy_policy.jsonl deny decision",
                "expected": {"task": "success", "cause": "identified"}}
    def exec_fn(s):
        return {"success": True, "metrics": {"cause": "policy_deny", "confidence": 0.9,
                                              "policy_compliance": True, "retrieval_hit": False,
                                              "recovery_result": None}}
    result = engine.run(scenario, executor=exec_fn)
    assert result["success"] is True
    assert result["metrics"]["cause"] == "policy_deny"
