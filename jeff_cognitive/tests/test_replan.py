"""Phase 10 testleri."""

from jeff_cognitive import CognitiveState
from jeff_cognitive.replan import decide


def test_kill_on_invalid_goal():
    s = CognitiveState(objective="X")
    assert decide(s, {"goal_invalid": True})["outcome"] == "KILL"


def test_pivot_on_refuted():
    s = CognitiveState(objective="X")
    assert decide(s, {"hypothesis_refuted": True})["outcome"] == "PIVOT"


def test_continue_default():
    s = CognitiveState(objective="X")
    assert decide(s, {})["outcome"] == "CONTINUE"


def test_pause_on_budget():
    s = CognitiveState(objective="X", budget={"limit": 5.0, "spent": 9.0, "currency": "USD"})
    assert decide(s, {})["outcome"] == "PAUSE"


def test_no_sunk_cost():
    s = CognitiveState(objective="X", completed_tasks=[{"t": 1}] * 50)
    # 50 tamamlanmis is bile KILL'i engellemez
    assert decide(s, {"economics_collapsed": True})["outcome"] == "KILL"
