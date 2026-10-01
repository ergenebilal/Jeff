"""Phase 7: Real-world feedback — DECISION→PREDICTION→REAL_WORLD_RESULT→ERROR_ANALYSIS.

Mevcut DecisionRecord yok (canlida bulunamadi) → burada minimal, additive,
serializable kayit. Uyumlu isimlendirme: decision_id / prediction / confidence /
actual / error.
"""

from __future__ import annotations
from contextlib import contextmanager

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DecisionRecord:
    record_id: str = field(default_factory=lambda: str(uuid4()))
    goal_id: str = ""
    decision: str = ""
    prediction: float = 0.0  # örn odeme istegi 0.70
    confidence: float = 0.5
    decision_type: str = "general"
    domain: str = "general"
    real_world_result: Optional[float] = None
    error_analysis: str = ""
    lesson_ref: str = ""
    created_at: str = field(default_factory=_utcnow)
    closed_at: str = ""

    def error(self) -> Optional[float]:
        if self.real_world_result is None:
            return None
        return round(self.real_world_result - self.prediction, 4)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["prediction_error"] = self.error()
        return d


_SCHEMA = """
CREATE TABLE IF NOT EXISTS decision_records (
    record_id TEXT PRIMARY KEY,
    goal_id TEXT DEFAULT '',
    data TEXT NOT NULL,
    closed INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    closed_at TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_dec_goal ON decision_records (goal_id, closed);
"""


class FeedbackStore:
    """Karar→tahmin→gercek→hata. Kapanmamis kayit = bekleyen ogrenme."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=5000")
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def record(self, decision: str, prediction: float, goal_id: str = "",
               confidence: float = 0.5, **kw: Any) -> DecisionRecord:
        rec = DecisionRecord(decision=decision, prediction=float(prediction),
                             goal_id=goal_id, confidence=float(confidence), **kw)
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO decision_records (record_id,goal_id,data,closed,created_at,closed_at)"
                " VALUES (?,?,?,?,?,?)",
                (rec.record_id, rec.goal_id, json.dumps(asdict(rec), ensure_ascii=False),
                 0, rec.created_at, ""),
            )
        return rec

    def observe(self, record_id: str, real_world_result: float,
                error_analysis: str = "", lesson_ref: str = "") -> DecisionRecord:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM decision_records WHERE record_id=?", (record_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"kayit yok: {record_id}")
            d = json.loads(row["data"])
            rec = DecisionRecord(**{k: v for k, v in d.items() if k in DecisionRecord.__dataclass_fields__})
            rec.real_world_result = float(real_world_result)
            rec.error_analysis = error_analysis
            rec.lesson_ref = lesson_ref
            rec.closed_at = _utcnow()
            conn.execute(
                "UPDATE decision_records SET data=?, closed=1, closed_at=? WHERE record_id=?",
                (json.dumps(asdict(rec), ensure_ascii=False), rec.closed_at, record_id),
            )
        return rec

    def pending(self, goal_id: str = "") -> List[DecisionRecord]:
        with self._connect() as conn:
            if goal_id:
                rows = conn.execute(
                    "SELECT data FROM decision_records WHERE closed=0 AND goal_id=?",
                    (goal_id,)).fetchall()
            else:
                rows = conn.execute(
                    "SELECT data FROM decision_records WHERE closed=0").fetchall()
        out = []
        for r in rows:
            d = json.loads(r["data"])
            out.append(DecisionRecord(**{k: v for k, v in d.items() if k in DecisionRecord.__dataclass_fields__}))
        return out

    def closed(self) -> List[DecisionRecord]:
        with self._connect() as conn:
            rows = conn.execute("SELECT data FROM decision_records WHERE closed=1").fetchall()
        out = []
        for r in rows:
            d = json.loads(r["data"])
            out.append(DecisionRecord(**{k: v for k, v in d.items() if k in DecisionRecord.__dataclass_fields__}))
        return out
