"""Phase 8: Self-calibration — hafif, durust, small-n'e saygili.

Her olculebilir tahmin icin: prediction/confidence/actual/error/type/domain/ts.
n kucukse 'unavailable — sample too small' (istatistiksel anlamlilik iddiasi YOK).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

MIN_N = 30  # altinda kalibrasyon aciklanmaz


@dataclass
class CalibPoint:
    prediction: float
    confidence: float
    actual: float
    decision_type: str = "general"
    domain: str = "general"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def error(self) -> float:
        return self.actual - self.prediction


class Calibrator:
    def __init__(self) -> None:
        self.points: List[CalibPoint] = []

    def add(self, prediction: float, confidence: float, actual: float,
            decision_type: str = "general", domain: str = "general") -> CalibPoint:
        p = CalibPoint(float(prediction), float(confidence), float(actual),
                       decision_type, domain)
        self.points.append(p)
        return p

    def summary(self) -> Dict[str, Any]:
        n = len(self.points)
        if n < MIN_N:
            return {"status": "unavailable — sample too small", "n": n,
                    "min_n": MIN_N}
        errs = [p.error() for p in self.points]
        over = sum(1 for p in self.points if p.prediction > p.actual)
        under = sum(1 for p in self.points if p.prediction < p.actual)
        by_type: Dict[str, List[float]] = {}
        by_domain: Dict[str, List[float]] = {}
        for p in self.points:
            by_type.setdefault(p.decision_type, []).append(abs(p.error()))
            by_domain.setdefault(p.domain, []).append(abs(p.error()))
        mae = sum(abs(e) for e in errs) / n
        bias = sum(errs) / n
        success = sum(1 for e in errs if abs(e) <= 0.2)
        return {
            "status": "available", "n": n,
            "mae": round(mae, 4), "bias": round(bias, 4),
            "overconfidence_rate": round(over / n, 3),
            "underconfidence_rate": round(under / n, 3),
            "success_rate": round(success / n, 3),
            "by_type_mae": {k: round(sum(v) / len(v), 4) for k, v in by_type.items()},
            "by_domain_mae": {k: round(sum(v) / len(v), 4) for k, v in by_domain.items()},
        }
