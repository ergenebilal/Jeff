"""Phase 3: Goal management — 5 kavram ASLA cakistirilamaz.

GOAL (hedef): örn "Ilk odemeli musteri".
OBJECTIVE (amac): gole bagli olculebilir ara cikti (niche bul, agriyi dogrula...).
TASK (gorev): tek seanslik somut is ("10 Bursa emlak ofisini denetle").
EXPERIMENT (deney): hipotez + basari/kriter + gozlem (Phase 6 objesi, burada ref).
ACTION (aksiyon): atomik adim ("siteyi incele"), parent'i TASK olmak zorunda.
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

NODE_GOAL = "goal"
NODE_OBJECTIVE = "objective"
NODE_TASK = "task"
NODE_EXPERIMENT = "experiment"
NODE_ACTION = "action"

NODE_TYPES = (NODE_GOAL, NODE_OBJECTIVE, NODE_TASK, NODE_EXPERIMENT, NODE_ACTION)

# hangi tip, hangi parent tipine baglanabilir
PARENT_RULES: Dict[str, set] = {
    NODE_GOAL: set(),  # kok
    NODE_OBJECTIVE: {NODE_GOAL},
    NODE_TASK: {NODE_GOAL, NODE_OBJECTIVE},
    NODE_EXPERIMENT: {NODE_GOAL, NODE_OBJECTIVE},
    NODE_ACTION: {NODE_TASK},
}

STATUS_OPEN = "open"
STATUS_ACTIVE = "active"
STATUS_DONE = "done"
STATUS_BLOCKED = "blocked"
STATUS_KILLED = "killed"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class GoalNode:
    node_id: str = field(default_factory=lambda: str(uuid4()))
    node_type: str = NODE_TASK
    title: str = ""
    parent_id: Optional[str] = None
    session_id: str = ""
    status: str = STATUS_OPEN
    detail: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


_SCHEMA = """
CREATE TABLE IF NOT EXISTS cognitive_nodes (
    node_id TEXT PRIMARY KEY,
    node_type TEXT NOT NULL,
    title TEXT NOT NULL,
    parent_id TEXT,
    session_id TEXT DEFAULT '',
    status TEXT DEFAULT 'open',
    detail TEXT DEFAULT '{}',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_nodes_parent ON cognitive_nodes (parent_id);
CREATE INDEX IF NOT EXISTS idx_nodes_session ON cognitive_nodes (session_id, node_type);
"""


class GoalManager:
    """Hiyerarsik hedef yonetimi. Kural ihlali → ValueError (sessiz collapse yok)."""

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

    def _get(self, conn: sqlite3.Connection, node_id: str) -> GoalNode:
        row = conn.execute(
            "SELECT * FROM cognitive_nodes WHERE node_id=?", (node_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"node yok: {node_id}")
        d = dict(row)
        d["detail"] = json.loads(d["detail"] or "{}")
        return GoalNode(**d)

    def create(
        self,
        node_type: str,
        title: str,
        parent_id: Optional[str] = None,
        session_id: str = "",
        detail: Optional[Dict[str, Any]] = None,
    ) -> GoalNode:
        if node_type not in NODE_TYPES:
            raise ValueError(f"bilinmeyen tip: {node_type!r}")
        if not title.strip():
            raise ValueError("title bos olamaz")
        with self._connect() as conn:
            if parent_id is not None:
                parent = self._get(conn, parent_id)
                allowed = PARENT_RULES[node_type]
                if parent.node_type not in allowed:
                    raise ValueError(
                        f"{node_type} → {parent.node_type} baglanamaz "
                        f"(izin: {sorted(allowed)})"
                    )
            elif node_type != NODE_GOAL:
                raise ValueError(f"{node_type} kok olamaz — parent sart")
            node = GoalNode(
                node_type=node_type, title=title.strip(),
                parent_id=parent_id, session_id=session_id,
                detail=dict(detail or {}),
            )
            conn.execute(
                "INSERT INTO cognitive_nodes (node_id,node_type,title,parent_id,session_id,status,detail,created_at)"
                " VALUES (?,?,?,?,?,?,?,?)",
                (node.node_id, node.node_type, node.title, node.parent_id,
                 node.session_id, node.status, json.dumps(node.detail, ensure_ascii=False),
                 node.created_at),
            )
        return node

    # ── kisayollar ──
    def create_goal(self, title: str, **kw: Any) -> GoalNode:
        return self.create(NODE_GOAL, title, parent_id=None, **kw)

    def add_objective(self, goal_id: str, title: str, **kw: Any) -> GoalNode:
        return self.create(NODE_OBJECTIVE, title, parent_id=goal_id, **kw)

    def add_task(self, parent_id: str, title: str, **kw: Any) -> GoalNode:
        return self.create(NODE_TASK, title, parent_id=parent_id, **kw)

    def add_experiment(self, parent_id: str, title: str, **kw: Any) -> GoalNode:
        return self.create(NODE_EXPERIMENT, title, parent_id=parent_id, **kw)

    def add_action(self, task_id: str, title: str, **kw: Any) -> GoalNode:
        return self.create(NODE_ACTION, title, parent_id=task_id, **kw)

    def children(self, node_id: str) -> List[GoalNode]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM cognitive_nodes WHERE parent_id=? ORDER BY created_at ASC",
                (node_id,),
            ).fetchall()
            out = []
            for r in rows:
                d = dict(r)
                d["detail"] = json.loads(d["detail"] or "{}")
                out.append(GoalNode(**d))
            return out

    def tree(self, goal_id: str) -> Dict[str, Any]:
        with self._connect() as conn:
            root = self._get(conn, goal_id)
        if root.node_type != NODE_GOAL:
            raise ValueError("tree kokü goal olmali")

        def _build(node: GoalNode) -> Dict[str, Any]:
            d = node.to_dict()
            d["children"] = [_build(c) for c in self.children(node.node_id)]
            return d

        return _build(root)

    def set_status(self, node_id: str, status: str) -> GoalNode:
        if status not in (STATUS_OPEN, STATUS_ACTIVE, STATUS_DONE, STATUS_BLOCKED, STATUS_KILLED):
            raise ValueError(f"bilinmeyen status: {status!r}")
        with self._connect() as conn:
            node = self._get(conn, node_id)
            node.status = status
            conn.execute(
                "UPDATE cognitive_nodes SET status=? WHERE node_id=?", (status, node_id)
            )
        return node
