"""Token usage and filtering facade for Hermes."""

import json
import sqlite3
import subprocess
from pathlib import Path


LOG_LEVELS = {"critical": 0, "normal": 1, "verbose": 2}
_current_level = LOG_LEVELS["normal"]
TOKEN_GUARD_SCRIPT = Path.home() / "hermes_scripts" / "token_guard.py"
TOKEN_STATE_FILE = Path.home() / ".hermes" / "data" / "token_state.json"


def _state_db_path() -> Path:
    return Path.home() / ".hermes" / "hermes_state.db"


def track_usage() -> dict:
    script = TOKEN_GUARD_SCRIPT
    if script.exists():
        try:
            result = subprocess.run(
                ["python3", str(script), "report"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                return json.loads(result.stdout)
        except Exception:
            pass
    if TOKEN_STATE_FILE.exists():
        try:
            return json.loads(TOKEN_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"error": "token_guard.py not available"}


def get_budget_left() -> float:
    usage = track_usage()
    if "budget_left" in usage:
        return float(usage["budget_left"])
    if "session_cost" in usage:
        return max(TokenGuard.MAX_SEANS - float(usage["session_cost"]), 0.0)
    return TokenGuard.MAX_SEANS


def get_daily_usage() -> dict:
    db_path = _state_db_path()
    if not db_path.exists():
        return {"total_tokens": 0, "total_cost": 0.0}
    try:
        conn = sqlite3.connect(str(db_path))
        try:
            cur = conn.execute(
                """
                SELECT COALESCE(SUM(total_tokens), 0),
                       COALESCE(SUM(total_cost), 0.0)
                FROM sessions
                WHERE date(created_at) = date('now')
                """
            )
            row = cur.fetchone()
            return {"total_tokens": int(row[0] or 0), "total_cost": float(row[1] or 0.0)}
        finally:
            conn.close()
    except Exception:
        return {"total_tokens": 0, "total_cost": 0.0}


def get_session_breakdown(limit: int = 10) -> list:
    db_path = _state_db_path()
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(str(db_path))
        try:
            cur = conn.execute(
                """
                SELECT session_id, source, total_tokens, total_cost, created_at
                FROM sessions
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (int(limit),),
            )
            return [
                {
                    "session_id": row[0],
                    "source": row[1],
                    "tokens": row[2],
                    "cost": row[3],
                    "time": row[4],
                }
                for row in cur.fetchall()
            ]
        finally:
            conn.close()
    except Exception:
        return []


def set_log_level(level: str):
    global _current_level
    if level in LOG_LEVELS:
        _current_level = LOG_LEVELS[level]


def should_log(level: str) -> bool:
    return LOG_LEVELS.get(level, LOG_LEVELS["normal"]) <= _current_level


def compress_message(msg: str, max_tokens: int = 500) -> str:
    if len(msg) < max_tokens:
        return msg
    keep = min(200, max_tokens // 2)
    removed = max(len(msg) - (keep * 2), 0)
    return msg[:keep] + f"\n... [{removed} chars compressed] ...\n" + msg[-keep:]


def estimate_tokens(text: str) -> int:
    return len(text) // 4


class TokenGuard:
    MAX_SEANS = 0.50
    WARN_AT = 0.75
    FLASH_AT = 0.90
    STOP_AT = 1.00

    @staticmethod
    def check() -> dict:
        usage = track_usage()
        current = float(usage.get("session_cost", usage.get("usage", 0.0)) or 0.0)
        ratio = current / TokenGuard.MAX_SEANS if TokenGuard.MAX_SEANS else 1.0
        if ratio >= TokenGuard.STOP_AT:
            status = "stop"
        elif ratio >= TokenGuard.FLASH_AT:
            status = "flash"
        elif ratio >= TokenGuard.WARN_AT:
            status = "warn"
        else:
            status = "ok"
        return {
            "status": status,
            "usage": current,
            "budget_left": max(TokenGuard.MAX_SEANS - current, 0.0),
        }
