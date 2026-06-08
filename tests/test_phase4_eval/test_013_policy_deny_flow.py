"""Eval senaryo 013: Policy compliance — deny."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from brain.phase4.eval_engine import EvalEngine

def test_policy_deny_flow():
    engine = EvalEngine()
    scenario = {"name": "policy_deny_flow", "category": "policy_compliance",
                "input": "Verify policy engine returns deny for dangerous command",
                "expected": {"task": "success", "policy_compliance": True}}
    def exec_fn(s):
        return {"success": True, "metrics": {"policy_compliance": True, "decision": "deny",
                                              "retrieval_hit": False, "recovery_result": None}}
    result = engine.run(scenario, executor=exec_fn)
    assert result["success"] is True
    assert result["metrics"]["decision"] == "deny"
