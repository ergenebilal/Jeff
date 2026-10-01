"""Phase 6 testleri."""

import tempfile
from pathlib import Path

import pytest

from jeff_cognitive.experiments import ExperimentEngine


@pytest.fixture()
def eng():
    with tempfile.TemporaryDirectory() as tmp:
        yield ExperimentEngine(Path(tmp) / "e.db")


def _full_cycle(eng):
    e = eng.propose("surtunme ↔ lead sorunu", goal_id="g1", target="Bursa emlak",
                    method="10 ofis tara", success_criteria="3+ kant",
                    failure_criteria="0 kant", cost_limit=5.0)
    eng.move(e.experiment_id, "APPROVED")
    eng.move(e.experiment_id, "RUNNING")
    return e


def test_lifecycle(eng):
    e = _full_cycle(eng)
    closed = eng.close(e.experiment_id, observed_result="2/10 kant",
                       interpretation="zayif korelasyon", conclusion="WEAKLY_SUPPORTED")
    assert closed.status == "COMPLETED" and closed.conclusion == "WEAKLY_SUPPORTED"


def test_no_interpretation_no_close(eng):
    e = _full_cycle(eng)
    with pytest.raises(ValueError):
        eng.close(e.experiment_id, observed_result="x", interpretation="  ",
                  conclusion="SUPPORTED")


def test_illegal_transition(eng):
    e = eng.propose("h")
    with pytest.raises(ValueError):
        eng.move(e.experiment_id, "RUNNING")  # PROPOSED→RUNNING yasak


def test_refuted_path(eng):
    e = _full_cycle(eng)
    closed = eng.close(e.experiment_id, observed_result="0/10",
                       interpretation="korelasyon yok", conclusion="REFUTED",
                       to="COMPLETED")
    assert closed.conclusion == "REFUTED"


def test_list_for_goal(eng):
    e = _full_cycle(eng)
    assert len(eng.list_for_goal("g1")) == 1
