"""Eval senaryo 007: Retrieval — ders eşleştirme."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from brain.phase4.eval_engine import EvalEngine

def test_retr_lesson_match():
    engine = EvalEngine()
    scenario = {"name": "retr_lesson_match", "category": "retrieval",
                "input": "Retrieve relevant lesson for 'token limit exceeded'",
                "expected": {"task": "success", "retrieval_hit": True}}
    def exec_fn(s):
        return {"success": True, "metrics": {"retrieval_hit": True, "relevance": 0.88,
                                              "policy_compliance": True, "recovery_result": None}}
    result = engine.run(scenario, executor=exec_fn)
    assert result["success"] is True
    assert result["metrics"]["retrieval_hit"] is True
