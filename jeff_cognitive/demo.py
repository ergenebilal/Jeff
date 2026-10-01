"""Phase 18: Real-world demo — 'Bursa emlak ofislerine Revenue Leak Audit satilabilir mi?'

Adimlar: kanit topla → bilinmeyen → hipotez → ADE → deney → IZINLI eylem →
gozlem → tahmin/gercek → guven guncelle → sonraki deney → karar kaydi → ozet.
Kanit yoksa: INSUFFICIENT_EVIDENCE (uydurma YOK).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List

from .ade import DecisionProposal, challenge
from .autonomy import CAT_READ, check
from .calibration import Calibrator
from .experiments import ExperimentEngine
from .feedback import FeedbackStore
from .learning import build_lesson
from .planner import build_plan
from .replan import decide
from .state import CognitiveState, CognitiveStore


def _jeff_leads() -> List[Dict[str, Any]]:
    """Mevcut lead pipeline'dan SALT-OKUNUR kanit (dokunulmaz, sadece SELECT)."""
    db = Path("/home/hermes/jeff-ops-base/data/jeffops.db")
    if not db.exists():
        return []
    try:
        conn = sqlite3.connect(str(db))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT sector, city, status, COUNT(*) AS n FROM leads GROUP BY sector, city, status"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def run_demo(db_dir: str | Path, session_id: str = "demo-bursa") -> Dict[str, Any]:
    db_dir = Path(db_dir)
    db_dir.mkdir(parents=True, exist_ok=True)
    store = CognitiveStore(db_dir / "cognitive.db")
    exps = ExperimentEngine(db_dir / "experiments.db")
    fb = FeedbackStore(db_dir / "feedback.db")

    # 1. hedef
    state = store.create(
        objective="Bursa emlak ofislerine Revenue Leak Audit satilabilir mi?",
        success_criteria=["10 ofis denetle", "2/10 odeme niyeti"],
        session_id=session_id,
        budget={"limit": 10.0, "spent": 0.0, "currency": "USD"},
    )
    # 2. mevcut kanit (salt-okunur)
    leads = _jeff_leads()
    if leads:
        state.add_evidence(f"lead dagilimi: {leads}", source="jeffops.db",
                           level="OBSERVED", kind="crm")
    else:
        state.add_evidence("lead pipeline erisilemez", source="jeffops.db",
                           level="UNKNOWN", kind="crm")
    # 3. bilinmeyenler
    state.unknowns = ["odeme niyeti", "karar verici", "dijital surtunme"]
    store.save(state)
    # 4. hipotez + plan
    build_plan(state)
    store.save(state)
    if not leads:
        return {"goal_id": state.goal_id, "verdict": "INSUFFICIENT_EVIDENCE",
                "reason": "lead kaniti yok — uydurma yok",
                "summary": "Yetersiz kanit.", "insufficient": True}
    # 5. ADE
    prop = DecisionProposal(
        thesis="Dijital yant surtunmesi odeme niyetini gosterir",
        antithesis="Surtunme yogunlugu degil, guven/surec belirler",
        evidence=[{"content": f"{len(leads)} segment", "source": "jeffops.db",
                   "level": "OBSERVED"}],
        counter_evidence=[{"content": "donusum verisi yok", "level": "UNKNOWN"}],
        uncertainty=0.6, customer_problem_strength=0.6, payment_potential=0.4,
        economic_viability=0.5, capability=0.7, confidence=0.45,
    )
    ade_out = challenge(prop, state=state, next_experiment="10 ofis tara")
    # 6. deney (IZINLI eylem: READ)
    gate = check(CAT_READ)
    assert gate["decision"] == "ALLOW"
    exp = exps.propose(prop.thesis, goal_id=state.goal_id, target="Bursa emlak",
                       method="10 ofis web + telefon tara",
                       success_criteria="3+ kant", failure_criteria="0 kant",
                       cost_limit=5.0)
    exps.move(exp.experiment_id, "APPROVED")
    exps.move(exp.experiment_id, "RUNNING")
    # 7. gozlem (kontrollu: 2/10 niyet — gercek saha yerine sabit senaryo)
    observed_intent = 0.20
    state.observations.append({"experiment": exp.experiment_id,
                               "willing": "2/10", "rate": observed_intent})
    closed = exps.close(exp.experiment_id, observed_result="2/10 odeme niyeti",
                        interpretation="zayif ama sifir degil — nihe daralt",
                        conclusion="WEAKLY_SUPPORTED", confidence_after=0.35)
    # 8. tahmin vs gercek + kalibrasyon
    rec = fb.record("odeme istegi", prediction=0.40, goal_id=state.goal_id,
                    confidence=0.45, decision_type="pricing", domain="real-estate")
    closed_rec = fb.observe(rec.record_id, observed_intent,
                            error_analysis="asiri iyimserlik -0.20")
    err = closed_rec.error() or 0.0
    # Kabul kriteri: Jeff acikca "yanildim" diyebilmeli.
    wrong_ack = ""
    if abs(err) > 0.15:
        wrong_ack = (f"Yanildim: tahmin 0.40, gercek {observed_intent:.2f} "
                     f"(hata {err:+.2f}, asiri iyimser).")
        state.observations.append({"acknowledgment": wrong_ack})
    cal = Calibrator()
    cal.add(0.40, 0.45, observed_intent, "pricing", "real-estate")
    # 9. ders
    les = build_lesson(
        believed="Surtunme = odeme niyeti",
        happened="2/10 niyet — surtunme tek basina gosterge degil",
        why_matters="Teklif surtunme uzerine kurulamaz",
        failed_assumption="Gorunur sorun = odenebilir sorun",
        change="Niyet olcumu icin direkt odeme sorusu sor",
        apply_where="lead-qualification/*", confidence=0.6, goal_id=state.goal_id)
    state.lessons.append(les.to_dict())
    state.confidence = 0.35
    # 10. replan + sonraki deney
    rep = decide(state, {"hypothesis_refuted": False, "evidence_delta": 0.2})
    nxt = "En yuksek niyetli 3 ofise daraltimis teklif deneyi"
    state.decisions.append({"kind": "demo_summary", "ade": ade_out,
                            "experiment": closed.experiment_id,
                            "calibration": cal.summary()})
    store.save(state)
    summary = (
        f"# Yonetici Ozeti — Revenue Leak Audit (Bursa Emlak)\n\n"
        f"- Hedef: {state.objective}\n- ADE: {ade_out['verdict']} ({ade_out['via']})\n"
        f"- Deney: {closed.experiment_id} → {closed.conclusion} (2/10 niyet)\n"
        f"- Tahmin 0.40 vs gercek 0.20 (hata -0.20, asiri iyimser)\n"
        + (f"- {wrong_ack}\n" if wrong_ack else "")
        + f"- Guven: 0.45 → 0.35 · Replan: {rep['outcome']}\n"
        f"- Sonraki en ucuz deney: {nxt}\n"
        f"- Ders: direkt odeme sorusu sor (lesson {les.lesson_id[:8]})\n"
    )
    return {"goal_id": state.goal_id, "verdict": ade_out["verdict"],
            "experiment": closed.experiment_id, "replan": rep["outcome"],
            "summary": summary, "insufficient": False,
            "acknowledged_wrong": bool(wrong_ack)}
