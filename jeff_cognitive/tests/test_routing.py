"""Phase 11 testleri."""

from jeff_cognitive.routing import ModelRouter


def test_cheap_for_simple():
    r = ModelRouter().route(task_class="listele", complexity=1, risk="low")
    assert r["model"] == "cheap" and r["level"] == "L0" and not r["verify"]


def test_strong_for_complex():
    r = ModelRouter().route(task_class="strateji", complexity=9, risk="low")
    assert r["model"] == "strong" and r["verify"]


def test_high_risk_governance():
    r = ModelRouter().route(task_class="odeme", complexity=2, risk="critical")
    assert r["governance"] and r["model"] == "strong"


def test_coding_passthrough():
    r = ModelRouter().route(task_class="refactor", coding=True)
    assert r["level"] == "CODING"


def test_history_tracks():
    m = ModelRouter()
    m.route(task_class="a", complexity=1)
    rec = m.report(0, quality=0.8, retries=1)
    assert rec.result_quality == 0.8 and rec.retries == 1
