"""JEFF Cognitive Core — Phase 1: CognitiveState.

Operational state (kisa omurlu, resume edilebilir). Long-term knowledge
Memory'de kalir; burada DUPLICATE YOK — dis referanslar `external_refs`
ile tutulur (goals.db row, jeff_task id, SessionDB session).

Stdlib only. Python 3.10+.
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

# ── Fazlar (prompt: GOAL→UNDERSTAND→PLAN→DECIDE→ACT→OBSERVE→VERIFY→LEARN→CALIBRATE→REPLAN) ──
PHASE_GOAL = "GOAL"
PHASE_UNDERSTAND = "UNDERSTAND"
PHASE_PLAN = "PLAN"
PHASE_DECIDE = "DECIDE"
PHASE_ACT = "ACT"
PHASE_OBSERVE = "OBSERVE"
PHASE_VERIFY = "VERIFY"
PHASE_LEARN = "LEARN"
PHASE_CALIBRATE = "CALIBRATE"
PHASE_REPLAN = "REPLAN"
PHASE_DONE = "DONE"

PHASES = (
    PHASE_GOAL, PHASE_UNDERSTAND, PHASE_PLAN, PHASE_DECIDE, PHASE_ACT,
    PHASE_OBSERVE, PHASE_VERIFY, PHASE_LEARN, PHASE_CALIBRATE, PHASE_REPLAN,
    PHASE_DONE,
)

# ── Kanit seviyeleri (KRITIK: UNKNOWN asla sessizce TRUE olmaz) ──
EV_VERIFIED = "VERIFIED"
EV_OBSERVED = "OBSERVED"
EV_INFERENCE = "INFERENCE"
EV_ESTIMATE = "ESTIMATE"
EV_HYPOTHESIS = "HYPOTHESIS"
EV_UNKNOWN = "UNKNOWN"

EVIDENCE_LEVELS = (
    EV_VERIFIED, EV_OBSERVED, EV_INFERENCE, EV_ESTIMATE, EV_HYPOTHESIS, EV_UNKNOWN,
)

RISK_LEVELS = ("low", "medium", "high", "critical")


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _validate_confidence(value: float) -> float:
    v = float(value)
    if not 0.0 <= v <= 1.0:
        raise ValueError(f"confidence 0..1 olmali: {value!r}")
    return v


def _validate_phase(value: str) -> str:
    if value not in PHASES:
        raise ValueError(f"bilinmeyen faz: {value!r} (gecerli: {PHASES})")
    return value


def _validate_risk(value: str) -> str:
    if value not in RISK_LEVELS:
        raise ValueError(f"bilinmeyen risk: {value!r} (gecerli: {RISK_LEVELS})")
    return value


def _validate_evidence_level(value: str) -> str:
    if value not in EVIDENCE_LEVELS:
        raise ValueError(f"bilinmeyen evidence level: {value!r}")
    return value


@dataclass
class CognitiveState:
    """Persistent, structured operasyonel durum. Tamamı JSON-serializable."""

    goal_id: str = field(default_factory=lambda: str(uuid4()))
    parent_goal_id: Optional[str] = None
    session_id: str = ""
    objective: str = ""
    success_criteria: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    current_phase: str = PHASE_GOAL
    plan: List[Dict[str, Any]] = field(default_factory=list)
    active_tasks: List[Dict[str, Any]] = field(default_factory=list)
    completed_tasks: List[Dict[str, Any]] = field(default_factory=list)
    blocked_tasks: List[Dict[str, Any]] = field(default_factory=list)
    decisions: List[Dict[str, Any]] = field(default_factory=list)
    experiments: List[str] = field(default_factory=list)  # Phase 6'da full obje; simdi id ref
    observations: List[Dict[str, Any]] = field(default_factory=list)
    verification_results: List[Dict[str, Any]] = field(default_factory=list)
    lessons: List[Dict[str, Any]] = field(default_factory=list)
    calibration_data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    budget: Dict[str, Any] = field(default_factory=lambda: {"limit": 0.0, "spent": 0.0, "currency": "USD"})
    risk_level: str = "medium"
    governance_state: Dict[str, Any] = field(default_factory=lambda: {"level": "medium", "approvals": []})
    next_action: Optional[str] = None
    external_refs: Dict[str, Any] = field(default_factory=dict)  # goals.db / jeff_task / session — kopya degil referans
    created_at: str = field(default_factory=_utcnow_iso)
    updated_at: str = field(default_factory=_utcnow_iso)

    def __post_init__(self) -> None:
        _validate_phase(self.current_phase)
        _validate_risk(self.risk_level)
        self.confidence = _validate_confidence(self.confidence)
        for ev in self.evidence:
            if isinstance(ev, dict) and "level" in ev:
                _validate_evidence_level(ev["level"])

    # ── serialization ──
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CognitiveState":
        known = {f for f in cls.__dataclass_fields__}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> "CognitiveState":
        return cls.from_dict(json.loads(payload))

    # ── helpers ──
    def add_evidence(
        self,
        content: str,
        source: str = "",
        level: str = EV_UNKNOWN,
        kind: str = "note",
    ) -> Dict[str, Any]:
        """Yeni kanit ekler. Default level UNKNOWN — sessiz yukseltme YOK."""
        _validate_evidence_level(level)
        item = {
            "kind": kind,
            "content": content,
            "source": source,
            "level": level,
            "created_at": _utcnow_iso(),
        }
        self.evidence.append(item)
        self.updated_at = _utcnow_iso()
        return item

    def spend(self, amount: float) -> Dict[str, Any]:
        spent = float(self.budget.get("spent", 0.0)) + float(amount)
        self.budget["spent"] = spent
        self.updated_at = _utcnow_iso()
        return self.budget


_SCHEMA_STATES = """
CREATE TABLE IF NOT EXISTS cognitive_states (
    goal_id TEXT PRIMARY KEY,
    parent_goal_id TEXT,
    session_id TEXT DEFAULT '',
    data TEXT NOT NULL,
    current_phase TEXT NOT NULL,
    confidence REAL NOT NULL,
    risk_level TEXT NOT NULL,
    next_action TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cog_session_phase
ON cognitive_states (session_id, current_phase);
"""

_SCHEMA_TRANSITIONS = """
CREATE TABLE IF NOT EXISTS cognitive_transitions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    goal_id TEXT NOT NULL,
    from_phase TEXT NOT NULL,
    to_phase TEXT NOT NULL,
    reason TEXT DEFAULT '',
    input TEXT DEFAULT '{}',
    output TEXT DEFAULT '{}',
    confidence REAL DEFAULT 0.0,
    cost REAL,
    errors TEXT DEFAULT '[]',
    next TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_cog_trans_goal
ON cognitive_transitions (goal_id, id);
"""


class CognitiveStore:
    """SQLite persist + resume. WAL + busy_timeout. Tablo disi sema degisikligi yok."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

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

    def _init(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA_STATES)
            conn.executescript(_SCHEMA_TRANSITIONS)

    # ── CRUD ──
    def create(
        self,
        objective: str,
        success_criteria: Optional[List[str]] = None,
        session_id: str = "",
        parent_goal_id: Optional[str] = None,
        constraints: Optional[List[str]] = None,
        budget: Optional[Dict[str, Any]] = None,
        risk_level: str = "medium",
        external_refs: Optional[Dict[str, Any]] = None,
    ) -> CognitiveState:
        state = CognitiveState(
            objective=objective,
            success_criteria=list(success_criteria or []),
            session_id=session_id,
            parent_goal_id=parent_goal_id,
            constraints=list(constraints or []),
            budget=dict(budget) if budget else {"limit": 0.0, "spent": 0.0, "currency": "USD"},
            risk_level=_validate_risk(risk_level),
            external_refs=dict(external_refs or {}),
        )
        self.save(state)
        return state

    def save(self, state: CognitiveState) -> CognitiveState:
        state.updated_at = _utcnow_iso()
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO cognitive_states
                   (goal_id, parent_goal_id, session_id, data, current_phase,
                    confidence, risk_level, next_action, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(goal_id) DO UPDATE SET
                     parent_goal_id=excluded.parent_goal_id,
                     session_id=excluded.session_id,
                     data=excluded.data,
                     current_phase=excluded.current_phase,
                     confidence=excluded.confidence,
                     risk_level=excluded.risk_level,
                     next_action=excluded.next_action,
                     updated_at=excluded.updated_at""",
                (
                    state.goal_id, state.parent_goal_id, state.session_id,
                    state.to_json(), state.current_phase, state.confidence,
                    state.risk_level, state.next_action,
                    state.created_at, state.updated_at,
                ),
            )
        return state

    def load(self, goal_id: str) -> CognitiveState:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT data FROM cognitive_states WHERE goal_id=?", (goal_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"CognitiveState bulunamadi: {goal_id}")
        return CognitiveState.from_json(row["data"])

    def list_open(self, session_id: str = "") -> List[CognitiveState]:
        """Yarim kalmis hedefler — resume icin. DONE haric hepsi."""
        with self._connect() as conn:
            if session_id:
                rows = conn.execute(
                    "SELECT data FROM cognitive_states WHERE session_id=? AND current_phase != 'DONE' ORDER BY updated_at DESC",
                    (session_id,),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT data FROM cognitive_states WHERE current_phase != 'DONE' ORDER BY updated_at DESC"
                ).fetchall()
        return [CognitiveState.from_json(r["data"]) for r in rows]

    # ── Phase 2 hazirligi: gozlemlenebilir gecis logu ──
    def transition(
        self,
        state: CognitiveState,
        to_phase: str,
        reason: str = "",
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        confidence: Optional[float] = None,
        cost: Optional[float] = None,
        errors: Optional[List[str]] = None,
        next_action: str = "",
    ) -> CognitiveState:
        _validate_phase(to_phase)
        from_phase = state.current_phase
        conf = state.confidence if confidence is None else _validate_confidence(confidence)
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO cognitive_transitions
                   (goal_id, from_phase, to_phase, reason, input, output,
                    confidence, cost, errors, next, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    state.goal_id, from_phase, to_phase, reason,
                    json.dumps(input_data or {}, ensure_ascii=False),
                    json.dumps(output_data or {}, ensure_ascii=False),
                    conf, cost,
                    json.dumps(list(errors or []), ensure_ascii=False),
                    next_action, _utcnow_iso(),
                ),
            )
        state.current_phase = to_phase
        state.confidence = conf
        if next_action:
            state.next_action = next_action
        return self.save(state)

    def transitions(self, goal_id: str) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM cognitive_transitions WHERE goal_id=? ORDER BY id ASC",
                (goal_id,),
            ).fetchall()
        return [dict(r) for r in rows]
