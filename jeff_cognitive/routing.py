"""Phase 11: Model routing — DOGRU model, guclu model DEGIL.

L0: ucuz · L1: ucuz/orta · L2: guclu + adversarial · high-risk: guclu + verify + governance.
Coding: mevcut coding router'a passthrough (burada stub + gecmis).
Gecmis performans ileride rotayi iyilestirir (kayit simdiden tutulur).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

LEVEL_L0 = "L0"
LEVEL_L1 = "L1"
LEVEL_L2 = "L2"
LEVEL_HIGH = "HIGH_RISK"
LEVEL_CODING = "CODING"

MODEL_CHEAP = "cheap"
MODEL_MEDIUM = "medium"
MODEL_STRONG = "strong"

_EST_COST = {MODEL_CHEAP: 1.0, MODEL_MEDIUM: 3.0, MODEL_STRONG: 10.0}


@dataclass
class RouteRecord:
    model: str
    level: str
    task_class: str
    estimated_cost: float
    result_quality: float = 0.0
    retries: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ModelRouter:
    def __init__(self) -> None:
        self.history: List[RouteRecord] = []

    def route(self, task_class: str = "general", complexity: int = 0,
              risk: str = "low", coding: bool = False) -> Dict[str, Any]:
        if coding:
            level, model = LEVEL_CODING, MODEL_MEDIUM  # coding router passthrough
        elif risk in ("high", "critical"):
            level, model = LEVEL_HIGH, MODEL_STRONG
        elif complexity >= 7:
            level, model = LEVEL_L2, MODEL_STRONG
        elif complexity >= 4:
            level, model = LEVEL_L1, MODEL_MEDIUM
        else:
            level, model = LEVEL_L0, MODEL_CHEAP
        rec = RouteRecord(model=model, level=level, task_class=task_class,
                          estimated_cost=_EST_COST[model])
        self.history.append(rec)
        d = asdict(rec)
        d["verify"] = level in (LEVEL_L2, LEVEL_HIGH)
        d["governance"] = level == LEVEL_HIGH
        return d

    def report(self, index: int, quality: float, retries: int = 0) -> RouteRecord:
        rec = self.history[index]
        rec.result_quality = float(quality)
        rec.retries = int(retries)
        return rec
