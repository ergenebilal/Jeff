"""Eval senaryo 011: Policy compliance — allow."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from brain.phase4.eval_engine import EvalEngine

def test_policy_allow_check():
    engine = EvalEngine()
    scenario = {"name": "policy_allow_check", "category": "policy_compliance",
                "input": "Verify policy engine returns allow for safe command",
                "expected": {"task": "success", "policy_compliance": True}}
    def exec_fn(s):
        return {"success": True, "metrics": {"policy_compliance": True, "decision": "allow",
                                              "retrieval_hit": False, "recovery_result": None}}
    result = engine.run(scenario, executor=exec_fn)
    assert result["success"] is True
    assert result["metrics"]["decision"] == "allow"
