"""State facade over hermes_state.SessionDB."""

from pathlib import Path


def _resolve_db_path() -> Path:
    try:
        from hermes_constants import get_hermes_home

        return Path(get_hermes_home()) / "hermes_state.db"
    except Exception:
        return Path.home() / ".hermes" / "hermes_state.db"


def get_db(read_only: bool = False):
    from hermes_state import SessionDB

    return SessionDB(db_path=_resolve_db_path(), read_only=read_only)


def get_session(session_id: str):
    db = get_db(read_only=True)
    try:
        return db.get_session(session_id)
    finally:
        db.close()


def close_db():
    db = get_db()
    db.close()
