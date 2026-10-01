"""Phase 16: Cost control — her dongu LLM kullanimini izler + erken durdurma.

Metrikler: cagri sayisi, model, tahmini maliyet, retry, debate seviyesi, gorev karmasikligi.
Erken dur: kanit yeterliyse DUR | hipotez curutulduyse KES | bilgi-kazanci dustuyse BITIR.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List


@dataclass
class CallRecord:
    model: str
    task_class: str = "general"
    estimated_cost: float = 0.0
    retries: int = 0
    debate_level: int = 0
    complexity: int = 0


@dataclass
class CostTracker:
    budget_limit: float = 20.0
    calls: List[CallRecord] = field(default_factory=list)

    def log(self, model: str, estimated_cost: float, **kw: Any) -> CallRecord:
        rec = CallRecord(model=model, estimated_cost=float(estimated_cost), **kw)
        self.calls.append(rec)
        return rec

    def totals(self) -> Dict[str, Any]:
        spent = round(sum(c.estimated_cost for c in self.calls), 2)
        return {"calls": len(self.calls), "spent": spent,
                "budget_limit": self.budget_limit,
                "over": spent > self.budget_limit,
                "retries": sum(c.retries for c in self.calls)}


def should_stop(evidence_sufficient: bool = False, hypothesis_refuted: bool = False,
                expected_gain: float = 1.0, gain_threshold: float = 0.2,
                over_budget: bool = False) -> Dict[str, Any]:
    if evidence_sufficient:
        return {"stop": True, "reason": "kanit yeterli — arastirmayi durdur"}
    if hypothesis_refuted:
        return {"stop": True, "reason": "hipotez curutuldu — harcamayi kes"}
    if expected_gain < gain_threshold:
        return {"stop": True, "reason": "bilgi-kazanci dustu — deneyi bitir"}
    if over_budget:
        return {"stop": True, "reason": "butce asildi — durdur"}
    return {"stop": False, "reason": "devam"}
