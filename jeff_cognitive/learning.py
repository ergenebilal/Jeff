"""Phase 9: Learning engine — 'lesson learned' cumlesi DEGIL, yapilandirilmis ogrenme.

7 alan zorunlu: believed / happened / why_matters / failed_assumption /
change / apply_where / confidence. Cikti lesson_enforcer formatina cevrilebilir.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Lesson:
    lesson_id: str = field(default_factory=lambda: str(uuid4()))
    believed: str = ""
    happened: str = ""
    why_matters: str = ""
    failed_assumption: str = ""
    change: str = ""
    apply_where: str = ""
    confidence: float = 0.5
    goal_id: str = ""
    created_at: str = field(default_factory=_utcnow)

    def __post_init__(self) -> None:
        missing = [k for k in ("believed", "happened", "why_matters",
                               "failed_assumption", "change", "apply_where")
                   if not getattr(self, k).strip()]
        if missing:
            raise ValueError(f"eksik lesson alani: {missing}")
        if not 0.0 <= float(self.confidence) <= 1.0:
            raise ValueError("confidence 0..1 olmali")

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_enforcer_format(self) -> Dict[str, Any]:
        """lesson_enforcer (yedek governance) uyumlu kural."""
        return {
            "rule": self.change,
            "scope": self.apply_where,
            "because": f"{self.believed} != {self.happened}: {self.why_matters}",
            "failed_assumption": self.failed_assumption,
            "confidence": self.confidence,
            "lesson_id": self.lesson_id,
        }


def build_lesson(believed: str, happened: str, why_matters: str,
                 failed_assumption: str, change: str, apply_where: str,
                 confidence: float = 0.5, goal_id: str = "") -> Lesson:
    return Lesson(believed=believed, happened=happened, why_matters=why_matters,
                  failed_assumption=failed_assumption, change=change,
                  apply_where=apply_where, confidence=confidence, goal_id=goal_id)
