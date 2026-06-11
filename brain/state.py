"""Small SQLite session-state facade used by Hermes brain helpers."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path.home() / ".hermes" / "state.db"
_CONN: sqlite3.Connection | None = None


def get_db(path: str | Path | None = None) -> sqlite3.Connection:
    """Return a reusable SQLite connection for the Hermes state DB."""
    global _CONN
    db_path = Path(path) if path is not None else DB_PATH
    if _CONN is None or path is not None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        if path is not None:
            return conn
        _CONN = conn
    return _CONN


def close_db() -> None:
    """Close the cached state DB connection, if open."""
    global _CONN
    if _CONN is not None:
        _CONN.close()
        _CONN = None


def get_session(session_id: str, path: str | Path | None = None) -> dict[str, Any] | None:
    """Fetch one session row as a dict."""
    conn = get_db(path)
    try:
        row = conn.execute("select * from sessions where id = ?", (session_id,)).fetchone()
        return dict(row) if row else None
    finally:
        if path is not None:
            conn.close()
