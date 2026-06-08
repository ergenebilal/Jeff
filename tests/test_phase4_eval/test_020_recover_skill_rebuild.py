"""Eval senaryo 020: Recovery — skill yeniden oluşturma."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from brain.phase4.eval_engine import EvalEngine

def test_recover_skill_rebuild():
    engine = EvalEngine()
    scenario = {"name": "recover_skill_rebuild", "category": "recovery",
                "input": "Rebuild corrupted skill registry from backup",
                "expected": {"task": "success", "recovery_result": "rebuilt"}}
    def exec_fn(s):
        return {"success": True, "metrics": {"recovery_result": "rebuilt", "skills_restored": 12,
                                              "policy_compliance": True, "retrieval_hit": False}}
    result = engine.run(scenario, executor=exec_fn)
    assert result["success"] is True
    assert result["metrics"]["skills_restored"] == 12
