"""Phase 4: Planning — odul aktivite DEGIL, bilgi-kazanci/maliyet.

Her non-trivial hedef icin: sonuc + olculebilir kriter + varsayim/bilinmeyen +
aday planlar + maliyet/zaman/risk + EN UCUZ yeterli plan + stop/fail/fallback.
"""

from __future__ import annotations

from typing import Any, Dict, List

from .state import CognitiveState

STRATEGIES = ("lean", "balanced", "thorough")

# strateji carpani: (maliyet, bilgi-kazanci, risk)
_STRATEGY_PROFILE = {
    "lean": {"cost_mult": 1.0, "gain_mult": 1.0, "risk": "low", "steps": 2},
    "balanced": {"cost_mult": 2.2, "gain_mult": 1.6, "risk": "medium", "steps": 4},
    "thorough": {"cost_mult": 4.5, "gain_mult": 2.1, "risk": "high", "steps": 6},
}

DEFAULT_REQUIRED_GAIN = 5.0


def _base_actions(state: CognitiveState) -> List[Dict[str, Any]]:
    """Bilinmeyenlerden turetilen atomik arastirma adimlari (pahali LLM yok)."""
    actions = []
    for i, u in enumerate(state.unknowns[:6] or ["hedef gecerliligi"]):
        actions.append({
            "action": f"arastir: {u}",
            "cost_estimate": 1.0,
            "time_estimate_min": 15,
            "info_gain": 2.0,
        })
    return actions


def generate_candidates(state: CognitiveState) -> List[Dict[str, Any]]:
    base = _base_actions(state)
    candidates = []
    for strat in STRATEGIES:
        prof = _STRATEGY_PROFILE[strat]
        steps = []
        for i in range(prof["steps"]):
            b = base[i % len(base)]
            steps.append({
                "step": i + 1,
                "action": b["action"] if i < len(base) else f"dogrula: adim {i + 1}",
                "cost_estimate": round(b["cost_estimate"] * prof["cost_mult"], 2),
                "time_estimate_min": int(b["time_estimate_min"] * prof["cost_mult"]),
                "risk": prof["risk"],
                "info_gain": round(b["info_gain"] * prof["gain_mult"], 2),
            })
        total_cost = round(sum(s["cost_estimate"] for s in steps), 2)
        total_gain = round(sum(s["info_gain"] for s in steps), 2)
        candidates.append({
            "strategy": strat,
            "steps": steps,
            "total_cost": total_cost,
            "total_gain": total_gain,
            "risk": prof["risk"],
            "score": round(total_gain / total_cost, 3) if total_cost else 0.0,
        })
    return candidates


def select_plan(
    candidates: List[Dict[str, Any]],
    required_gain: float = DEFAULT_REQUIRED_GAIN,
) -> Dict[str, Any]:
    sufficient = [c for c in candidates if c["total_gain"] >= required_gain]
    pool = sufficient or sorted(candidates, key=lambda c: -c["total_gain"])
    # yeterli olanlar arasinda EN UCUZ; hicbiri yetmezse en cok kazandiran
    if sufficient:
        return min(pool, key=lambda c: c["total_cost"])
    return pool[0]


def build_plan(state: CognitiveState, required_gain: float = DEFAULT_REQUIRED_GAIN) -> Dict[str, Any]:
    """Plani state'e isler, stop/fail/fallback ile. Donus: secilen plan."""
    candidates = generate_candidates(state)
    chosen = select_plan(candidates, required_gain)
    plan = {
        "strategy": chosen["strategy"],
        "steps": chosen["steps"],
        "total_cost": chosen["total_cost"],
        "total_gain": chosen["total_gain"],
        "stopping_conditions": [
            "kanit yeterliyse arastirmayi DURDUR",
            "hipotez acikca curutulurse harcamayi KES",
        ],
        "failure_conditions": [
            "3 ust uste gozlem basarisizligi",
            "butce asimi",
        ],
        "fallback": "lean stratejiye don, kapsami daralt",
        "selection_reason": (
            f"score={chosen['score']} (gain/cost); "
            f"yeterli planlar arasinda en ucuz"
        ),
    }
    state.plan = [plan]
    state.decisions.append({
        "kind": "plan_selection",
        "strategy": chosen["strategy"],
        "score": chosen["score"],
        "required_gain": required_gain,
        "candidates": len(candidates),
    })
    state.next_action = "karar ver"
    return plan
