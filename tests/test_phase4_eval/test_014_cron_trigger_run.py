"""Eval senaryo 014: Cron — tetikleme."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from brain.phase4.eval_engine import EvalEngine

def test_cron_trigger_run():
    engine = EvalEngine()
    scenario = {"name": "cron_trigger_run", "category": "cron",
                "input": "Trigger scheduled maintenance job via cron",
                "expected": {"task": "success", "executed": True}}
    def exec_fn(s):
        return {"success": True, "metrics": {"executed": True, "duration_sec": 1.2,
                                              "policy_compliance": True, "retrieval_hit": False,
                                              "recovery_result": None}}
    result = engine.run(scenario, executor=exec_fn)
    assert result["success"] is True
    assert result["metrics"]["executed"] is True
