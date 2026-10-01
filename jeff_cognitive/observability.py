"""Phase 14: Observability — her dongu reconstruct edilebilir.

goal_id verildiğinde: NEDEN? NEYE inandi? Hangi kanit? Neyi BILMIYORDU?
KIM karar verdi? Ne yapildi? Gercekte ne oldu? Ne ogrenildi? Ne degisti?
Dogal-dil loglara degil, yapilandirilmis kayda dayanir.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .state import CognitiveState, CognitiveStore


def reconstruct(store: CognitiveStore, goal_id: str) -> Dict[str, Any]:
    state = store.load(goal_id)
    transitions = store.transitions(goal_id)
    return {
        "goal_id": goal_id,
        "why": state.objective,
        "beliefs": {"assumptions": state.assumptions, "confidence": state.confidence},
        "evidence": state.evidence,
        "unknowns": state.unknowns,
        "decisions": state.decisions,
        "actions": state.completed_tasks + state.active_tasks,
        "reality": state.observations,
        "verification": state.verification_results,
        "lessons": state.lessons,
        "changes": [t for t in transitions if t["to_phase"] in ("REPLAN", "DONE")],
        "full_transitions": transitions,
    }


def export_log(store: CognitiveStore, goal_id: str) -> List[Dict[str, Any]]:
    """Dis sistemlere structured log (append-only tuketim icin)."""
    return [
        {"ts": t["created_at"], "from": t["from_phase"], "to": t["to_phase"],
         "reason": t["reason"], "confidence": t["confidence"],
         "cost": t["cost"], "errors": t["errors"]}
        for t in store.transitions(goal_id)
    ]
