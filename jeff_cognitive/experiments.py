"""Phase 6: Experiment engine — yorumSUZ 'completed' YOK.

Lifecycle: PROPOSED→APPROVED→RUNNING→{COMPLETED,FAILED,ABORTED,INCONCLUSIVE}
Conclusion (kapanista zorunlu): SUPPORTED | WEAKLY_SUPPORTED | REFUTED | INCONCLUSIVE
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

ST_PROPOSED = "PROPOSED"
ST_APPROVED = "APPROVED"
ST_RUNNING = "RUNNING"
ST_COMPLETED = "COMPLETED"
ST_FAILED = "FAILED"
ST_ABORTED = "ABORTED"
ST_INCONCLUSIVE = "INCONCLUSIVE"

STATUSES = (ST_PROPOSED, ST_APPROVED, ST_RUNNING, ST_COMPLETED,
            ST_FAILED, ST_ABORTED, ST_INCONCLUSIVE)
_ACTIVE = (ST_APPROVED, ST_RUNNING)
_CLOSED = (ST_COMPLETED, ST_FAILED, ST_ABORTED, ST_INCONCLUSIVE)

CONC_SUPPORTED = "SUPPORTED"
CONC_WEAK = "WEAKLY_SUPPORTED"
CONC_REFUTED = "REFUTED"
CONC_INCONCLUSIVE = "INCONCLUSIVE"
CONCLUSIONS = (CONC_SUPPORTED, CONC_WEAK, CONC_REFUTED, CONC_INCONCLUSIVE)

_TRANSITIONS: Dict[str, set] = {
    ST_PROPOSED: {ST_APPROVED, ST_ABORTED},
    ST_APPROVED: {ST_RUNNING, ST_ABORTED},
    ST_RUNNING: {ST_COMPLETED, ST_FAILED, ST_ABORTED, ST_INCONCLUSIVE},
    ST_COMPLETED: set(), ST_FAILED: set(), ST_ABORTED: set(), ST_INCONCLUSIVE: set(),
}


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Experiment:
    experiment_id: str = field(default_factory=lambda: str(uuid4()))
    hypothesis: str = ""
    target: str = ""
    method: str = ""
    expected_result: str = ""
    success_criteria: str = ""
    failure_criteria: str = ""
    cost_limit: float = 0.0
    time_limit_min: int = 60
    evidence_required: str = ""
    status: str = ST_PROPOSED
    observed_result: str = ""
    interpretation: str = ""
    conclusion: str = ""
    confidence_before: float = 0.5
    confidence_after: float = 0.5
    goal_id: str = ""
    created_at: str = field(default_factory=_utcnow)
    completed_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id TEXT PRIMARY KEY,
    goal_id TEXT DEFAULT '',
    data TEXT NOT NULL,
    status TEXT NOT NULL,
    conclusion TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    completed_at TEXT DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_exp_goal ON experiments (goal_id, status);
"""


class ExperimentEngine:
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

    def _write(self, exp: Experiment) -> None:
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO experiments (experiment_id,goal_id,data,status,conclusion,created_at,completed_at)"
                " VALUES (?,?,?,?,?,?,?)"
                " ON CONFLICT(experiment_id) DO UPDATE SET goal_id=excluded.goal_id, data=excluded.data,"
                " status=excluded.status, conclusion=excluded.conclusion, completed_at=excluded.completed_at",
                (exp.experiment_id, exp.goal_id, json.dumps(exp.to_dict(), ensure_ascii=False),
                 exp.status, exp.conclusion, exp.created_at, exp.completed_at),
            )

    def _read(self, experiment_id: str) -> Experiment:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM experiments WHERE experiment_id=?", (experiment_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"deney yok: {experiment_id}")
        d = json.loads(row["data"])
        return Experiment(**{k: v for k, v in d.items() if k in Experiment.__dataclass_fields__})

    def propose(self, hypothesis: str, goal_id: str = "", **kw: Any) -> Experiment:
        if not hypothesis.strip():
            raise ValueError("hipotez bos olamaz")
        exp = Experiment(hypothesis=hypothesis.strip(), goal_id=goal_id, **kw)
        self._write(exp)
        return exp

    def move(self, experiment_id: str, to: str) -> Experiment:
        exp = self._read(experiment_id)
        if to not in _TRANSITIONS[exp.status]:
            raise ValueError(f"gecis yasak: {exp.status}→{to}")
        exp.status = to
        if to in _CLOSED and not exp.completed_at:
            exp.completed_at = _utcnow()
        self._write(exp)
        return exp

    def close(
        self, experiment_id: str, observed_result: str, interpretation: str,
        conclusion: str, confidence_after: float = 0.5,
        to: str = ST_COMPLETED,
    ) -> Experiment:
        """Kapanis yorum + conclusion ZORUNLU — bos birakilirsa ValueError."""
        if not interpretation.strip():
            raise ValueError("interpretation olmadan kapatma YOK")
        if conclusion not in CONCLUSIONS:
            raise ValueError(f"conclusion sart: {CONCLUSIONS}")
        exp = self._read(experiment_id)
        if exp.status not in _ACTIVE:
            raise ValueError(f"kapanabilir durumda degil: {exp.status}")
        if to not in _TRANSITIONS[exp.status] or to not in _CLOSED:
            raise ValueError(f"kapanis hedefi gecersiz: {to}")
        exp.observed_result = observed_result
        exp.interpretation = interpretation.strip()
        exp.conclusion = conclusion
        exp.confidence_after = float(confidence_after)
        exp.status = to
        exp.completed_at = _utcnow()
        self._write(exp)
        return exp

    def list_for_goal(self, goal_id: str) -> List[Experiment]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT data FROM experiments WHERE goal_id=? ORDER BY created_at ASC",
                (goal_id,),
            ).fetchall()
        out = []
        for r in rows:
            d = json.loads(r["data"])
            out.append(Experiment(**{k: v for k, v in d.items() if k in Experiment.__dataclass_fields__}))
        return out
