"""Phase 3 testleri: 5 kavram ayrimi + hiyerarsi kurallari."""

import tempfile
from pathlib import Path

import pytest

from jeff_cognitive.goals import GoalManager


@pytest.fixture()
def gm():
    with tempfile.TemporaryDirectory() as tmp:
        yield GoalManager(Path(tmp) / "g.db")


def test_prompt_example_hierarchy(gm):
    g = gm.create_goal("Ilk odemeli musteri")
    o1 = gm.add_objective(g.node_id, "viable niche belirle")
    o2 = gm.add_objective(g.node_id, "odemeye istekliligi dogrula")
    t = gm.add_task(o1.node_id, "10 Bursa emlak ofisini denetle")
    e = gm.add_experiment(o1.node_id, "dijital yant surtunmesi ↔ lead sorunu korelasyonu")
    a = gm.add_action(t.node_id, "siteyi incele")
    assert a.parent_id == t.node_id
    assert e.parent_id == o1.node_id
    tree = gm.tree(g.node_id)
    assert len(tree["children"]) == 2
    titles = [c["title"] for c in tree["children"]]
    assert "viable niche belirle" in titles


def test_action_cannot_hang_under_goal(gm):
    g = gm.create_goal("G")
    with pytest.raises(ValueError):
        gm.add_action(g.node_id, "direkt aksiyon")  # ACTION parent TASK olmali


def test_experiment_cannot_hang_under_task(gm):
    g = gm.create_goal("G")
    t = gm.add_task(g.node_id, "T")
    with pytest.raises(ValueError):
        gm.add_experiment(t.node_id, "E")  # EXPERIMENT → GOAL/OBJECTIVE


def test_task_needs_parent(gm):
    with pytest.raises(ValueError):
        gm.create("task", "sahipsiz gorev")


def test_empty_title_rejected(gm):
    with pytest.raises(ValueError):
        gm.create_goal("  ")


def test_status_flow(gm):
    g = gm.create_goal("G")
    gm.set_status(g.node_id, "active")
    gm.set_status(g.node_id, "done")
    with pytest.raises(ValueError):
        gm.set_status(g.node_id, "flying")
