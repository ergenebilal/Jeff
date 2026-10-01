"""Phase 16 testleri."""

from jeff_cognitive.cost import CostTracker, should_stop


def test_tracking_and_budget():
    t = CostTracker(budget_limit=5.0)
    t.log("cheap", 1.0, task_class="arastir")
    t.log("strong", 10.0, task_class="strateji", retries=2)
    tot = t.totals()
    assert tot["calls"] == 2 and tot["spent"] == 11.0 and tot["over"]


def test_early_stopping():
    assert should_stop(evidence_sufficient=True)["stop"]
    assert should_stop(hypothesis_refuted=True)["stop"]
    assert should_stop(expected_gain=0.05)["stop"]
    assert not should_stop(expected_gain=0.9)["stop"]
