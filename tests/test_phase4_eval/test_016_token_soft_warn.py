"""Eval senaryo 016: Token budget — soft uyarı."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from brain.phase4.eval_engine import EvalEngine

def test_token_soft_warn():
    engine = EvalEngine()
    scenario = {"name": "token_soft_warn", "category": "token_budget",
                "input": "Trigger soft warning at 75% token budget",
                "expected": {"task": "success", "budget_status": "warn"}}
    def exec_fn(s):
        return {"success": True, "metrics": {"budget_status": "warn", "usage_pct": 0.78,
                                              "policy_compliance": True, "retrieval_hit": False,
                                              "recovery_result": None}}
    result = engine.run(scenario, executor=exec_fn)
    assert result["success"] is True
    assert result["metrics"]["budget_status"] == "warn"
