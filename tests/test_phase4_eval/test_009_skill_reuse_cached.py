"""Eval senaryo 009: Skill reuse — önbellek kullanımı."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from brain.phase4.eval_engine import EvalEngine

def test_skill_reuse_cached():
    engine = EvalEngine()
    scenario = {"name": "skill_reuse_cached", "category": "skill_reuse",
                "input": "Reuse cached skill for code review task",
                "expected": {"task": "success", "reuse": True}}
    def exec_fn(s):
        return {"success": True, "metrics": {"reuse": True, "cache_hit": True,
                                              "policy_compliance": True, "retrieval_hit": False,
                                              "recovery_result": None}}
    result = engine.run(scenario, executor=exec_fn)
    assert result["success"] is True
    assert result["metrics"]["cache_hit"] is True
