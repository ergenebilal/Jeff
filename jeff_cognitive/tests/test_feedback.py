"""Phase 7 testleri: prediction→result→error."""

import tempfile
from pathlib import Path

import pytest

from jeff_cognitive.feedback import FeedbackStore


@pytest.fixture()
def fb():
    with tempfile.TemporaryDirectory() as tmp:
        yield FeedbackStore(Path(tmp) / "f.db")


def test_prediction_error_flow(fb):
    rec = fb.record("odeme istegi yuksek", prediction=0.70, goal_id="g1",
                    confidence=0.7, decision_type="pricing", domain="real-estate")
    assert fb.pending("g1")
    closed = fb.observe(rec.record_id, real_world_result=0.20,
                        error_analysis="materyal asiri guven")
    assert closed.error() == pytest.approx(-0.50)
    assert "asiri guven" in closed.error_analysis
    assert not fb.pending("g1") and len(fb.closed()) == 1


def test_missing_record(fb):
    with pytest.raises(KeyError):
        fb.observe("yok", 0.5)
