"""Eval senaryo 015: Cron — hata kurtarma."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from brain.phase4.eval_engine import EvalEngine

def test_cron_recovery_retry():
    engine = EvalEngine()
    scenario = {"name": "cron_recovery_retry", "category": "cron",
                "input": "Retry failed cron job with backoff",
                "expected": {"task": "success", "recovery_result": "retried"}}
    def exec_fn(s):
        return {"success": True, "metrics": {"recovery_result": "retried", "attempts": 2,
                                              "policy_compliance": True, "retrieval_hit": False}}
    result = engine.run(scenario, executor=exec_fn)
    assert result["success"] is True
    assert result["metrics"]["recovery_result"] == "retried"
