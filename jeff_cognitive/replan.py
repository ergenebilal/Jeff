"""Phase 10: Replanning — batik maliyet bahanesi YOK.

Sorular: hedef gecerli mi? varsayimlar? kanit artti mi? ekonomi/musteri degisti mi?
Sonuc: CONTINUE | PIVOT | PAUSE | KILL | ESCALATE | RESEARCH
"""

from __future__ import annotations

from typing import Any, Dict

from .state import CognitiveState

OUT_CONTINUE = "CONTINUE"
OUT_PIVOT = "PIVOT"
OUT_PAUSE = "PAUSE"
OUT_KILL = "KILL"
OUT_ESCALATE = "ESCALATE"
OUT_RESEARCH = "RESEARCH"

OUTCOMES = (OUT_CONTINUE, OUT_PIVOT, OUT_PAUSE, OUT_KILL, OUT_ESCALATE, OUT_RESEARCH)


def decide(state: CognitiveState, signals: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Kurallar (acik, denetlenebilir). signals: gozlemden gelen taze bilgi."""
    sig = signals or {}
    econ_collapsed = bool(sig.get("economics_collapsed", False))
    goal_invalid = bool(sig.get("goal_invalid", False))
    hypothesis_refuted = bool(sig.get("hypothesis_refuted", False))
    evidence_up = float(sig.get("evidence_delta", 0.0)) > 0
    blocked = len(state.blocked_tasks) > 3
    over_budget = float(state.budget.get("spent", 0.0)) > float(state.budget.get("limit", 0.0) or 0.0) > 0
    governance_block = state.governance_state.get("level") == "blocked"

    if goal_invalid or econ_collapsed:
        out, reason = OUT_KILL, "hedef/ekonomi gecerliligi kalmadi — batik maliyete bakilmaz"
    elif governance_block:
        out, reason = OUT_ESCALATE, "governance blokladi — insana yukselt"
    elif hypothesis_refuted and not evidence_up:
        out, reason = OUT_PIVOT, "hipotez curutuldu, kanit artmiyor — pivot"
    elif hypothesis_refuted and evidence_up:
        out, reason = OUT_RESEARCH, "curutme + yeni kanit — arastirmaya don"
    elif blocked or over_budget:
        out, reason = OUT_PAUSE, "tikanma/butce — dur ve degerlendir"
    elif state.risk_level == "critical" and state.confidence < 0.3:
        out, reason = OUT_ESCALATE, "kritik risk + dusuk guven"
    else:
        out, reason = OUT_CONTINUE, "varsayimlar gecerli, devam"
    result = {"outcome": out, "reason": reason, "signals": sig}
    state.decisions.append({"kind": "replan", **result})
    state.next_action = {"CONTINUE": "devam", "PIVOT": "pivot plani",
                         "PAUSE": "bekle", "KILL": "kapat",
                         "ESCALATE": "insana sor", "RESEARCH": "arastir"}[out]
    return result
