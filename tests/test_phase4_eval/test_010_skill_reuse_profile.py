"""Eval senaryo 010: Skill reuse — profil bazlı."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from brain.phase4.eval_engine import EvalEngine

def test_skill_reuse_profile():
    engine = EvalEngine()
    scenario = {"name": "skill_reuse_profile", "category": "skill_reuse",
                "input": "Reuse personal profile skill across sessions",
                "expected": {"task": "success", "reuse": True}}
    def exec_fn(s):
        return {"success": True, "metrics": {"reuse": True, "profile_match": "personal",
                                              "policy_compliance": True, "retrieval_hit": False,
                                              "recovery_result": None}}
    result = engine.run(scenario, executor=exec_fn)
    assert result["success"] is True
    assert result["metrics"]["profile_match"] == "personal"
