"""Eval senaryo 008: Retrieval — skill bulma."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from brain.phase4.eval_engine import EvalEngine

def test_retr_skill_find():
    engine = EvalEngine()
    scenario = {"name": "retr_skill_find", "category": "retrieval",
                "input": "Find skill for pytest debugging workflow",
                "expected": {"task": "success", "retrieval_hit": True}}
    def exec_fn(s):
        return {"success": True, "metrics": {"retrieval_hit": True, "skill_count": 3,
                                              "policy_compliance": True, "recovery_result": None}}
    result = engine.run(scenario, executor=exec_fn)
    assert result["success"] is True
    assert result["metrics"]["skill_count"] == 3
