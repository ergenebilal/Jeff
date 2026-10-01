"""Phase 15 testleri."""

from jeff_cognitive import CognitiveState
from jeff_cognitive.memory import enforce_limits, split


def test_no_full_dump():
    s = CognitiveState(objective="X")
    s.active_tasks = [{"t": i} for i in range(200)]
    s.decisions.append({"kind": "ade_challenge", "verdict": "ACCEPT"})
    buckets = split(s)
    assert len(buckets["operational"]["active_tasks"]) <= 50
    assert len(buckets["decision"]) == 1  # secici, tam dump yok
    assert buckets["user"] == {}


def test_enforce_trims():
    s = CognitiveState(objective="X")
    s.evidence = [{"c": i} for i in range(500)]
    enforce_limits(s)
    assert len(s.evidence) == 100
