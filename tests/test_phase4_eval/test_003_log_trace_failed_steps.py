"""Eval senaryo 003: Log analizi — başarısız adımları izle."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from brain.phase4.eval_engine import EvalEngine

def test_log_trace_failed_steps():
    engine = EvalEngine()
    scenario = {"name": "log_trace_failed_steps", "category": "log_analysis",
                "input": "Trace root cause from failed step in step_trace",
                "expected": {"task": "success", "recovery": "traced"}}
    def exec_fn(s):
        return {"success": True, "metrics": {"steps_traced": 5, "policy_compliance": True,
                                              "retrieval_hit": False, "recovery_result": "traced"}}
    result = engine.run(scenario, executor=exec_fn)
    assert result["success"] is True
    assert "traced" in str(result["metrics"])
