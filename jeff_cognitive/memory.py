"""Phase 15: Memory boundaries — tum state'i permanent memory'e DUMP ETME.

OPERATIONAL (gecici, cognitive.db) | DECISION (stratejik) | LESSON (genellenebilir) |
USER (tercih/baglam) | SYSTEM (mimari bilgi). Sisme onleme: limit + secici yazma.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .state import CognitiveState

BUCKET_OPERATIONAL = "operational"
BUCKET_DECISION = "decision"
BUCKET_LESSON = "lesson"
BUCKET_USER = "user"
BUCKET_SYSTEM = "system"

MAX_OPERATIONAL_TASKS = 50
MAX_EVIDENCE = 100


def split(state: CognitiveState) -> Dict[str, Any]:
    """State'i 5 kovaya ayir. Operational disindakiler sinirli + secici."""
    decisions = [d for d in state.decisions
                 if d.get("kind") in ("ade_challenge", "replan", "plan_selection")]
    lessons = state.lessons
    return {
        BUCKET_OPERATIONAL: {
            "goal_id": state.goal_id, "current_phase": state.current_phase,
            "plan": state.plan,
            "active_tasks": state.active_tasks[-MAX_OPERATIONAL_TASKS:],
            "blocked_tasks": state.blocked_tasks[-MAX_OPERATIONAL_TASKS:],
            "next_action": state.next_action,
        },
        BUCKET_DECISION: decisions[-20:],
        BUCKET_LESSON: lessons[-20:],
        BUCKET_USER: {},
        BUCKET_SYSTEM: {"risk_level": state.risk_level,
                        "governance": state.governance_state.get("level")},
    }


def enforce_limits(state: CognitiveState) -> CognitiveState:
    """Sisme korumasi: operational listeleri buda (karar/ders budanmaz, onlar secici)."""
    state.active_tasks = state.active_tasks[-MAX_OPERATIONAL_TASKS:]
    state.completed_tasks = state.completed_tasks[-MAX_OPERATIONAL_TASKS:]
    state.blocked_tasks = state.blocked_tasks[-MAX_OPERATIONAL_TASKS:]
    state.evidence = state.evidence[-MAX_EVIDENCE:]
    return state
