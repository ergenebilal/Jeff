"""Phase 4 testleri."""

from jeff_cognitive import CognitiveState
from jeff_cognitive.planner import build_plan, generate_candidates


def test_cheapest_sufficient_wins():
    from jeff_cognitive.planner import select_plan
    s = CognitiveState(objective="X", unknowns=["a", "b", "c", "d"])
    cands = generate_candidates(s)
    assert len(cands) == 3
    # esik dusukse lean (en ucuz yeterli) kazanir
    plan = build_plan(s, required_gain=3.0)
    assert plan["strategy"] == "lean"
    # default esikte lean yetmez (4.0 < 5.0) → yeterli olanlarin en ucuzu (balanced)
    s2 = CognitiveState(objective="X", unknowns=["a", "b", "c", "d"])
    plan2 = build_plan(s2)
    sufficient = [c for c in generate_candidates(s2) if c["total_gain"] >= 5.0]
    assert plan2["total_cost"] == min(c["total_cost"] for c in sufficient)


def test_stop_fail_fallback_present():
    s = CognitiveState(objective="X")
    plan = build_plan(s)
    assert plan["stopping_conditions"] and plan["failure_conditions"] and plan["fallback"]


def test_state_updated():
    s = CognitiveState(objective="X")
    build_plan(s)
    assert len(s.plan) == 1 and s.decisions[-1]["kind"] == "plan_selection"
    assert s.next_action == "karar ver"


def test_reward_is_gain_over_cost_not_activity():
    s = CognitiveState(objective="X", unknowns=["tek bilinmeyen"])
    cands = generate_candidates(s)
    lean = next(c for c in cands if c["strategy"] == "lean")
    thorough = next(c for c in cands if c["strategy"] == "thorough")
    assert lean["score"] >= thorough["score"]  # daha fazla is, daha iyi skor DEGIL
