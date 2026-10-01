"""v1.1 T1–T15 — etiketli: UNIT / INTEGRATION / BEHAVIORAL / RUNTIME / MOCKED.

RUNTIME = gerçek canlı kod+state (dry_run LLM hariç — anahtar yoksa gerçek
LLM iddiası YOK). MOCKED = stub girdiyle akış testi (açıkça etiketli).
"""

import tempfile
from pathlib import Path

import pytest

from jeff_cognitive import Bridge, BridgeUnavailable, CognitiveLoop, CognitiveStore

LIVE = Path("/opt/hermes/jeff_v2")


@pytest.fixture()
def env():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        store = CognitiveStore(tmp / "c.db")
        bridge = Bridge(hermes_home=tmp, dry_run=True)
        loop = CognitiveLoop(store, bridge=bridge)
        yield {"tmp": tmp, "store": store, "bridge": bridge, "loop": loop}


def _needs_live():
    import os
    if os.environ.get('JEFF_COGNITIVE_LIVE_TESTS') != '1':
        pytest.skip('live dependency requires explicit isolated runtime opt-in')
    if not (LIVE / "adversarial_engine.py").exists():
        pytest.skip("canlı jeff_v2 yok (sadece hermes sunucusunda)")


# ── T1 DECIDE→canlı ADE [RUNTIME/dry] ──
def test_T1_decide_live_ade(env):
    _needs_live()
    out = env["bridge"].decide_ade("Test sorusu", {"k": "v"}, trigger="t1")
    assert out["via"] == "live-ade" and out["verdict"]
    assert out["action"] in ("continue", "experiment", "pivot", "wait",
                             "block", "research", "continue_governed")
    assert out["decision_id"].startswith("dec_")


def test_T1b_board_live(env):
    _needs_live()
    out = env["bridge"].decide_board("Test sorusu", {"evidence": []})
    assert out["via"] == "live-board"
    assert out["verdict"] in ("ACCEPT", "MODIFY", "VALIDATE_FIRST", "DEFER", "REJECT")


# ── T2 ACT→Worker [RUNTIME] ──
def test_T2_act_echo_python_fileread(env):
    _needs_live()
    b = env["bridge"]
    r1 = b.act("echo", {"task": "merhaba"})
    assert r1["success"] and "merhaba" in str(r1.get("result", ""))
    r2 = b.act("python", {"code": "result = 40 + 2"})
    assert r2["success"] and "42" in str(r2.get("result", ""))
    p = env["tmp"] / "read.txt"
    p.write_text("okuma-icerik")
    r3 = b.act("file_read", {"path": str(p)})
    assert r3["success"] and "okuma-icerik" in str(r3.get("result", ""))


def test_T2b_act_governance_paths_blocked(env):
    _needs_live()
    r = env["bridge"].act("shell", {"command": "rm -rf /"})
    assert not r["success"]  # canlı guard engeller


# ── T3 ACT→OBSERVE [INTEGRATION] ──
def test_T3_observe_structure(env):
    _needs_live()
    res = env["bridge"].act("echo", {"task": "t"})
    obs = env["bridge"].observe("echo", "echo", {"task": "t"}, res, expected="x")
    for k in ("observation_id", "action", "success", "output", "error",
              "expected", "created_at"):
        assert k in obs
    assert obs["success"] is True


# ── T4 VERIFY [UNIT] ──
def test_T4_verify_math():
    b = Bridge(hermes_home=tempfile.mkdtemp(), dry_run=True)
    assert b.verify(0.40, 0.05)["outcome"] == "REFUTED"  # err -0.35
    assert b.verify(0.40, 0.05)["error"] == pytest.approx(-0.35)
    assert b.verify(0.40, 0.20)["outcome"] == "PARTIALLY_VERIFIED"  # err -0.20
    assert b.verify(0.50, 0.52)["outcome"] == "VERIFIED"
    assert b.verify(None, 0.2)["outcome"] == "INCONCLUSIVE"


def test_T4b_record_real_world(env):
    _needs_live()
    b = env["bridge"]
    rec = b.decide_ade("Kalibrasyon testi", {}, trigger="t4b")["record"]
    out = b.record_real_world(rec["decision_id"], {"success": False})
    assert out.get("calibration") == "OVERCONFIDENT" or "real_world_result" in out


# ── T5/T6 VERIFY→LEARN→persistent [RUNTIME] ──
def test_T5_T6_learn_persistent(env):
    b = env["bridge"]
    les = {"rule": "Sessizlik talep kaniti degildir",
           "applies_to": ["instagram", "comments"],
           "lesson": "test-dersi", "confidence": 0.7}
    saved = b.learn_save(les)
    assert saved["lesson_id"]
    found = b.lessons_for("instagram profile comments scan")
    assert found and found[0]["lesson_id"] == saved["lesson_id"]


# ── T7 LEARN→BEHAVIOR [BEHAVIORAL, LLM'siz gerçek dosya-davranış] ──
def test_T7_behavior_changes(env):
    b = env["bridge"]
    q = "Instagram profile scan sessizlik yorumlar"
    run1 = b.assess_claim_evidence(q)
    assert run1["stance"] == "baseline"
    b.learn_save({"rule": "Yorum sessizligi yanitsiz musteri talebinin kaniti degildir",
                  "applies_to": ["instagram", "comments", "silence"],
                  "lesson": "silence-is-not-demand", "confidence": 0.8})
    run2 = b.assess_claim_evidence(q)
    assert run2["stance"] == "cautious"
    assert "OBSERVED" in run2["statement"]
    assert run1["statement"] != run2["statement"]  # davranış FARKLI


# ── T7b LEARN→BEHAVIOR loop seviyesi [BEHAVIORAL/RUNTIME] ──
def test_T7b_plan_uses_lesson_in_loop(env):
    store, loop, bridge = env["store"], env["loop"], env["bridge"]
    # RUN1 dersten önce: plansız hedef → lesson_informed False
    s1 = store.create(objective="Instagram sessizlik analizi")
    loop.run(s1.goal_id, max_steps=3)  # GOAL,UNDERSTAND,PLAN→DECIDE
    plan_out_1 = [t for t in loop.history(s1.goal_id)
                  if t["from_phase"] == "PLAN"][-1]
    import json as _json
    assert _json.loads(plan_out_1["output"])["lesson_informed"] is False
    # ders kaydet (RUN1'in LEARN çıktısı gibi)
    bridge.learn_save({"rule": "Yorum sessizligi talep kaniti degildir",
                       "applies_to": ["instagram", "sessizlik"],
                       "lesson": "silence-is-not-demand", "confidence": 0.8})
    # RUN2 aynı hedef: plan dersi uygular
    s2 = store.create(objective="Instagram sessizlik analizi")
    loop.run(s2.goal_id, max_steps=3)
    plan_out_2 = [t for t in loop.history(s2.goal_id)
                  if t["from_phase"] == "PLAN"][-1]
    assert _json.loads(plan_out_2["output"])["lesson_informed"] is True
    assert any("ders:" in c for c in store.load(s2.goal_id).constraints)


# ── T8 CALIBRATE→DB + small-n [RUNTIME] ──
def test_T8_calibrate_persistent_smalln(env):
    b = env["bridge"]
    out = b.calibrate_add(env["tmp"] / "c.db", 0.4, 0.2, 0.45)
    assert out["status"].startswith("unavailable") and out["n"] == 1


# ── T9 REPLAN→PLAN [INTEGRATION, loop üzerinden] ──
def test_T9_replan_to_plan(env):
    store, loop = env["store"], env["loop"]
    s = store.create(objective="X")
    loop.run(s.goal_id, max_steps=9)
    nxt = loop.step(s.goal_id, {"replan_signals": {"hypothesis_refuted": True}})
    assert nxt.current_phase == "PLAN"


# ── T10 governance [INTEGRATION] ──
def test_T10_irreversible_blocked_in_loop(env):
    store, loop = env["store"], env["loop"]
    s = store.create(objective="X")
    loop.run(s.goal_id, max_steps=4)  # DECIDE sonrasi ACT fazi
    st = loop.step(s.goal_id, {"category": "IRREVERSIBLE_ACTION",
                               "action": {"worker_type": "echo",
                                          "params": {"task": "x"}}})
    assert st.current_phase == "REPLAN"
    assert st.blocked_tasks  # kaybolmadi


def test_T10b_live_guard_called(env):
    _needs_live()
    g = env["bridge"].govern("siteyi oku", tool="file_read")
    assert g["via"] == "live-guard" and g["decision"] in ("ALLOW", "APPROVAL_REQUIRED", "DENY")


# ── T11 failure recovery [INTEGRATION] ──
def test_T11_unknown_worker_replans(env):
    _needs_live()
    from jeff_cognitive.recovery import handle_failure
    from jeff_cognitive import CognitiveState
    s = CognitiveState(objective="X")
    r = env["bridge"].act("yok-boyle-worker", {})
    assert not r["success"]
    out = handle_failure(s, "yok-boyle-worker", r.get("error", "bulunamadi"))
    assert out["strategy"] in ("replan", "alternative", "retry")
    assert s.blocked_tasks or s.active_tasks


# ── T12 crash resume [RUNTIME] ──
def test_T12_crash_resume(env):
    store, loop = env["store"], env["loop"]
    s = store.create(objective="X", session_id="crash")
    part = loop.run(s.goal_id, max_steps=5)  # ACT/OBSERVE civarinda "ol"
    assert part.current_phase != "DONE"
    resumed = loop.run(s.goal_id, max_steps=20)
    assert resumed.current_phase == "DONE"
    assert len(loop.history(s.goal_id)) >= 10


# ── T13 cost [UNIT] ──
def test_T13_cost_tracked():
    from jeff_cognitive.cost import CostTracker
    t = CostTracker(budget_limit=5.0)
    t.log("cheap", 1.0)
    assert t.totals()["calls"] == 1


# ── T14 routing→kaynak [UNIT] ──
def test_T14_route_mapping():
    b = Bridge(hermes_home=tempfile.mkdtemp(), dry_run=True)
    assert b.route_for("L0")["worker"] == "echo"
    assert b.route_for("HIGH_RISK")["governance"] is True
    assert b.route_for("CODING")["worker"] == "opencode"


# ── T15 full closed loop [RUNTIME, güvenli görev] ──
def test_T15_closed_loop(env):
    _needs_live()
    store, loop = env["store"], env["loop"]
    s = store.create(objective="Arastirma: tmp dizininde kanit dosyasi var mi?",
                     success_criteria=["gozlem kaydi", "dogrulama kaydi"],
                     session_id="t15")
    probe = env["tmp"] / "kanit.txt"
    probe.write_text("kanit-123")
    ctx = {"dry_run": True,
           "action": {"worker_type": "file_read",
                      "params": {"path": str(probe)}},
           "category": "READ",
           "expected": 1.0, "actual": 1.0}
    final = loop.run(s.goal_id, max_steps=20, ctx=ctx)
    assert final.current_phase == "DONE"
    assert final.observations  # T3
    assert final.verification_results  # T4
    assert final.lessons  # T5
    phases = [t["from_phase"] for t in loop.history(s.goal_id)]
    assert phases[0] == "GOAL" and len(phases) >= 10


# ── T16 ADE L1 parse sağlamlaştırma: 1 retry (mock LLM) [MOCKED/RUNTIME] ──
def test_T16_ade_retry_on_parse_error(env):
    _needs_live()
    from unittest import mock
    from jeff_cognitive.runtime_bridge import live_import
    mod = live_import("adversarial_engine")
    calls = {"n": 0}

    def fake_llm(system, user, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            # thesis: geçersiz JSON → retry tetiklenmeli
            return '{"claim": "X", bu gecersiz JSON'
        if calls["n"] == 2:
            return '{"claim": "X", "why": "y", "evidence": "e", "assumptions": ["a"], "expected_benefit": "b", "confidence": 40}'
        if calls["n"] == 3:
            return '{"counter_claim": "c", "strongest_objection": "o"}'
        return '{"evidence_strength": 60, "customer_problem_strength": 55, "payment_potential": 40, "competitive_advantage": 30, "hermes_capability": 50, "economic_viability": 35, "uncertainty": 40, "verdict": "READY", "confidence": 70}'

    engine = mod.AdversarialDecisionEngine(dry_run=False)
    with mock.patch.object(mod, "llm_call", side_effect=fake_llm):
        rec = engine.run(question="P1 mock sorusu",
                         trigger="assumption_validation")
    assert rec["verdict"] == "READY"
    assert calls["n"] == 4  # thesis fail + retry, anti, judge
    assert rec["num_llm_calls"] == 3
    assert "parse_error" not in str(rec.get("raw_outputs", {}).get("thesis", ""))
