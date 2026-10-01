"""Phase 17: integration — karar→ADE→deney→gercek→ders→replan tek akista."""

import tempfile
from pathlib import Path

from jeff_cognitive import CognitiveLoop, CognitiveStore
from jeff_cognitive.ade import DecisionProposal, challenge
from jeff_cognitive.calibration import Calibrator
from jeff_cognitive.cost import CostTracker
from jeff_cognitive.experiments import ExperimentEngine
from jeff_cognitive.feedback import FeedbackStore
from jeff_cognitive.goals import GoalManager
from jeff_cognitive.learning import build_lesson
from jeff_cognitive.observability import reconstruct
from jeff_cognitive.planner import build_plan
from jeff_cognitive.replan import decide


def test_end_to_end_mock():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        store = CognitiveStore(tmp / "c.db")
        gm = GoalManager(tmp / "g.db")
        exps = ExperimentEngine(tmp / "e.db")
        fb = FeedbackStore(tmp / "f.db")
        loop = CognitiveLoop(store)
        costs = CostTracker(budget_limit=50.0)

        g = gm.create_goal("Ilk odemeli musteri")
        o = gm.add_objective(g.node_id, "odeme niyetini dogrula")
        t = gm.add_task(o.node_id, "10 ofis denetle")

        s = store.create(objective="Ilk odemeli musteri", session_id="e2e",
                         external_refs={"goal_node": g.node_id})
        s.unknowns = ["odeme niyeti"]
        build_plan(s)
        out = challenge(DecisionProposal(
            thesis="Audit satilir", antithesis="Satilmaz",
            evidence=[{"content": "5 lead", "source": "jeffops", "level": "OBSERVED"}],
            counter_evidence=[], uncertainty=0.5,
            customer_problem_strength=0.7, payment_potential=0.6,
            economic_viability=0.6, capability=0.7), state=s,
            next_experiment="10 ofis")
        assert out["verdict"]

        e = exps.propose("Audit satilir", goal_id=s.goal_id)
        exps.move(e.experiment_id, "APPROVED")
        exps.move(e.experiment_id, "RUNNING")
        exps.close(e.experiment_id, observed_result="2/10",
                   interpretation="zayif destek", conclusion="WEAKLY_SUPPORTED")
        rec = fb.record("satis", prediction=0.6, goal_id=s.goal_id)
        fb.observe(rec.record_id, 0.2, error_analysis="asiri guven")
        cal = Calibrator()
        cal.add(0.6, 0.6, 0.2)
        assert cal.summary()["status"].startswith("unavailable")  # small-n durustlugu
        les = build_lesson("a", "b", "c", "d", "e", "f")
        s.lessons.append(les.to_dict())
        costs.log("cheap", 1.0, task_class="e2e")
        rep = decide(s, {"hypothesis_refuted": False, "evidence_delta": 0.1})
        assert rep["outcome"] == "CONTINUE"
        gm.set_status(t.node_id, "done")
        final = loop.run(s.goal_id, max_steps=20)
        assert final.current_phase == "DONE"
        rep2 = reconstruct(store, s.goal_id)
        assert rep2["why"] == "Ilk odemeli musteri"
        assert costs.totals()["calls"] == 1
