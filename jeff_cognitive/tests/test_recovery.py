"""Phase 13 testleri."""

from jeff_cognitive import CognitiveState
from jeff_cognitive.recovery import classify, handle_failure


def test_transient_retries():
    s = CognitiveState(objective="X")
    r = handle_failure(s, "api cagrisi", "connection timeout", attempts=1)
    assert r["strategy"] == "retry"


def test_retry_budget_exhausted():
    s = CognitiveState(objective="X")
    r = handle_failure(s, "api", "503 service down", attempts=5, max_retries=3)
    assert r["strategy"] == "alternative"


def test_structural_replans_and_persists():
    s = CognitiveState(objective="X")
    r = handle_failure(s, "sil", "permission denied", attempts=1)
    assert r["strategy"] == "replan"
    assert len(s.blocked_tasks) == 1  # kaybolmadi


def test_classify_unknown():
    assert classify("garip bir sey oldu") == "unknown"
