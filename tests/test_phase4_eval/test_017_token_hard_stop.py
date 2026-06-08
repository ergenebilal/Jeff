"""Eval senaryo 017: Token budget — hard durdurma."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from brain.phase4.eval_engine import EvalEngine

def test_token_hard_stop():
    engine = EvalEngine()
    scenario = {"name": "token_hard_stop", "category": "token_budget",
                "input": "Enforce hard stop at 100% token budget",
                "expected": {"task": "success", "budget_status": "hard"}}
    def exec_fn(s):
        return {"success": True, "metrics": {"budget_status": "hard", "usage_pct": 1.0,
                                              "policy_compliance": True, "retrieval_hit": False,
                                              "recovery_result": None}}
    result = engine.run(scenario, executor=exec_fn)
    assert result["success"] is True
    assert result["metrics"]["budget_status"] == "hard"
