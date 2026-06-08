"""Eval senaryo 019: Recovery — oturum geri yükleme."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from brain.phase4.eval_engine import EvalEngine

def test_recover_session_restore():
    engine = EvalEngine()
    scenario = {"name": "recover_session_restore", "category": "recovery",
                "input": "Restore interrupted session state from checkpoint",
                "expected": {"task": "success", "recovery_result": "restored"}}
    def exec_fn(s):
        return {"success": True, "metrics": {"recovery_result": "restored", "state_integrity": True,
                                              "policy_compliance": True, "retrieval_hit": False}}
    result = engine.run(scenario, executor=exec_fn)
    assert result["success"] is True
    assert result["metrics"]["state_integrity"] is True
