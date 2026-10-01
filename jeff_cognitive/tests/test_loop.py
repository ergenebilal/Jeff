"""Phase 2 testleri: order, observable transitions, resume, error→REPLAN, DONE terminal."""

import tempfile
from pathlib import Path

import pytest

from jeff_cognitive import CognitiveLoop, CognitiveStore
from jeff_cognitive.loop import PHASE_ORDER


@pytest.fixture()
def setup():
    with tempfile.TemporaryDirectory() as tmp:
        store = CognitiveStore(Path(tmp) / "c.db")
        loop = CognitiveLoop(store)
        yield store, loop


def test_full_order_goal_to_done(setup):
    store, loop = setup
    s = store.create(objective="X", success_criteria=["ok"])
    final = loop.run(s.goal_id, max_steps=20)
    assert final.current_phase == "DONE"
    phases = [t["from_phase"] for t in loop.history(s.goal_id)]
    assert phases[0] == "GOAL"
    # sira korunmus mu (REPLAN→DONE dahil 10 gecis)
    assert len(loop.history(s.goal_id)) == len(PHASE_ORDER)


def test_each_transition_observable(setup):
    store, loop = setup
    s = store.create(objective="X")
    loop.run(s.goal_id, max_steps=3)
    for t in loop.history(s.goal_id):
        for key in ("reason", "input", "output", "confidence", "errors", "next", "created_at"):
            assert key in t, f"eksik alan: {key}"
        assert t["created_at"]


def test_interruption_resume(setup):
    store, loop = setup
    s = store.create(objective="X", session_id="sess-i")
    part = loop.run(s.goal_id, max_steps=2)  # kesinti simulasyonu
    assert part.current_phase == "PLAN"
    # "restart": yeni loop ayni DB uzerinden devam
    resumed = loop.run(s.goal_id, max_steps=20)
    assert resumed.current_phase == "DONE"
    assert len(loop.history(s.goal_id)) == len(PHASE_ORDER)


def test_handler_error_goes_to_replan(setup):
    store, loop = setup
    s = store.create(objective="X")

    def boom(state, ctx):
        raise RuntimeError("plan patladi")

    loop.register("PLAN", boom)
    # GOAL, UNDERSTAND gecer, PLAN patlar → REPLAN
    st = loop.run(s.goal_id, max_steps=3)
    assert st.current_phase == "REPLAN"
    last = loop.history(s.goal_id)[-1]
    assert "plan patladi" in last["reason"]
    assert last["errors"]


def test_done_is_terminal(setup):
    store, loop = setup
    s = store.create(objective="X")
    loop.run(s.goal_id, max_steps=20)
    n = len(loop.history(s.goal_id))
    loop.run(s.goal_id, max_steps=20)  # tekrar calistir — yeni gecis YOK
    assert len(loop.history(s.goal_id)) == n


def test_empty_objective_goes_done_with_error(setup):
    store, loop = setup
    s = store.create(objective="  ")
    final = loop.run(s.goal_id, max_steps=5)
    assert final.current_phase == "DONE"
    assert loop.history(s.goal_id)[0]["errors"]


def test_custom_handler_override_next(setup):
    store, loop = setup
    s = store.create(objective="X")

    def decide(state, ctx):
        return {"reason": "risk yuksek — arastir", "confidence": 0.3,
                "output": {}, "next_phase": "OBSERVE", "next_action": "gozle"}

    loop.register("DECIDE", decide)
    loop.run(s.goal_id, max_steps=4)
    tos = [t["to_phase"] for t in loop.history(s.goal_id)]
    assert "OBSERVE" in tos  # sira disi atlama calisti


def _drive_to_replan(store, loop, goal_id):
    """State'i REPLAN fazina kadar ilerlet (varsayilan sinyalsiz)."""
    state = loop.run(goal_id, max_steps=9)
    assert state.current_phase == "REPLAN"
    return state


def test_replan_continue_ends_done(setup):
    store, loop = setup
    s = store.create(objective="X")
    _drive_to_replan(store, loop, s.goal_id)
    final = loop.step(s.goal_id, {"replan_signals": {}})
    assert final.current_phase == "DONE"
    last = loop.history(s.goal_id)[-1]
    assert "CONTINUE" in last["reason"]


def test_replan_pivot_cycles_to_plan(setup):
    store, loop = setup
    s = store.create(objective="X")
    _drive_to_replan(store, loop, s.goal_id)
    nxt = loop.step(s.goal_id, {"replan_signals": {"hypothesis_refuted": True}})
    assert nxt.current_phase == "PLAN"  # yeni dongu plana dondu
    tos = [t["to_phase"] for t in loop.history(s.goal_id)]
    assert tos.count("PLAN") >= 2


def test_replan_research_goes_understand(setup):
    store, loop = setup
    s = store.create(objective="X")
    _drive_to_replan(store, loop, s.goal_id)
    nxt = loop.step(s.goal_id, {"replan_signals": {"hypothesis_refuted": True,
                                                  "evidence_delta": 0.5}})
    assert nxt.current_phase == "UNDERSTAND"


def test_replan_kill_ends_done(setup):
    store, loop = setup
    s = store.create(objective="X")
    _drive_to_replan(store, loop, s.goal_id)
    final = loop.step(s.goal_id, {"replan_signals": {"goal_invalid": True}})
    assert final.current_phase == "DONE"
    assert "KILL" in loop.history(s.goal_id)[-1]["reason"]
