"""Eval senaryo 002: Log analizi — gecikme spike'larını tespit."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from brain.phase4.eval_engine import EvalEngine

def test_log_identify_spikes():
    engine = EvalEngine()
    scenario = {"name": "log_identify_spikes", "category": "log_analysis",
                "input": "Identify latency spikes in step_trace.jsonl",
                "expected": {"task": "success", "metric": "latency_spikes"}}
    def exec_fn(s):
        return {"success": True, "metrics": {"spikes_found": 2, "policy_compliance": True,
                                              "retrieval_hit": False, "recovery_result": None}}
    result = engine.run(scenario, executor=exec_fn)
    assert result["success"] is True
    assert result["metrics"]["spikes_found"] == 2
