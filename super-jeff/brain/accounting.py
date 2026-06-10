"""Unified token accounting: dollar budget + token-count budget per mode.

Merges brain_token / brain.token (dollar-based) with
brain/phase4/token_guard.py (token-count per mode).
"""

import json
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ── Constants ────────────────────────────────────────────────────────────────

LOG_LEVELS = {"critical": 0, "normal": 1, "verbose": 2}
_current_level = LOG_LEVELS["normal"]

# Dollar budget per session
MAX_SEANS = 0.50
WARN_AT = 0.75
FLASH_AT = 0.90
STOP_AT = 1.00

# Token-count budget per mode
BUDGET_LIMITS = {
    "quick": {"soft": 20_000, "hard": 40_000},
    "deep": {"soft": 60_000, "hard": 100_000},
    "background": {"soft": 40_000, "hard": 80_000},
}

# File paths
TOKEN_GUARD_SCRIPT = Path.home() / "hermes_scripts" / "token_guard.py"
TOKEN_STATE_FILE = Path.home() / ".hermes" / "data" / "token_state.json"
BUDGET_LOG = Path.home() / ".hermes" / "logs" / "token_budget.jsonl"


# ── Dollar-based budget (from brain_token / brain.token) ──────────────────

def _state_db_path() -> Path:
    return Path.home() / ".hermes" / "hermes_state.db"


def track_usage() -> dict:
    """Track dollar-based usage via external script or local state file."""
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
    """Remaining dollar budget."""
    usage = track_usage()
    if "budget_left" in usage:
        return float(usage["budget_left"])
    if "session_cost" in usage:
        return max(MAX_SEANS - float(usage["session_cost"]), 0.0)
    return MAX_SEANS


def get_daily_usage() -> dict:
    """Daily token/cost totals from SQLite."""
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
    """Recent session token/cost breakdown from SQLite."""
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


# ── Token-count budget per mode (from brain/phase4/token_guard.py) ─────────

def _read_usage() -> dict:
    """Read accumulated token usage from budget log."""
    total_tokens = 0
    if not BUDGET_LOG.exists():
        return {"total_tokens": 0}
    try:
        for line in BUDGET_LOG.read_text(encoding="utf-8").strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            total_tokens += int(entry.get("tokens", 0))
    except (json.JSONDecodeError, OSError):
        pass
    return {"total_tokens": total_tokens}


def token_budget_check(mode: str = "quick") -> dict:
    """Check current token usage against mode budget.

    Returns status: ok / warn (soft exceeded) / hard (hard exceeded).
    """
    usage = _read_usage()
    used = usage.get("total_tokens", 0)
    limits = BUDGET_LIMITS.get(mode, BUDGET_LIMITS["quick"])

    status = "ok"
    if used >= limits["hard"]:
        status = "hard"
    elif used >= limits["soft"]:
        status = "warn"

    return {
        "mode": mode,
        "used": used,
        "soft": limits["soft"],
        "hard": limits["hard"],
        "status": status,
        "remaining": max(limits["hard"] - used, 0),
    }


def log_token_usage(tokens: int, mode: str, action: str):
    """Append a token usage entry to the budget log."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tokens": tokens,
        "mode": mode,
        "action": action,
    }
    try:
        BUDGET_LOG.parent.mkdir(parents=True, exist_ok=True)
        with BUDGET_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


# ── Text helpers (from brain_token / brain.token) ──────────────────────────

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


# ── Chunk + Summarize + Compression (from brain/phase4/token_guard.py) ─────

class ChunkCompressor:
    """Compress long tool output via chunking, summarization, truncation."""

    MAX_CHUNK_CHARS = 3000
    MAX_SUMMARY_CHARS = 800
    MAX_CONTEXT_CHARS = 1500

    @classmethod
    def compress(cls, text: str, max_chars: Optional[int] = None) -> str:
        """Compress text: trim middle, keep head and tail with summary."""
        if max_chars is None:
            max_chars = cls.MAX_CONTEXT_CHARS
        if not text or len(text) <= max_chars:
            return text

        head_len = max_chars // 3
        tail_len = max_chars // 3
        head = text[:head_len]
        tail = text[-tail_len:]

        middle = text[head_len:-tail_len]
        summary = cls._summarize_middle(middle)

        return (
            f"{head}\n"
            f"[... {len(middle)} chars summarized -> {len(summary)} chars ...]\n"
            f"{summary}\n"
            f"{tail}"
        )

    @classmethod
    def _summarize_middle(cls, text: str) -> str:
        """Extract key lines from middle section."""
        lines = text.split("\n")
        key_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            # Keep error lines, summary lines, unique content
            if any(kw in stripped.lower() for kw in ("error", "fail", "traceback",
                                                       "summary", "passed", "====")):
                key_lines.append(stripped)
            elif len(stripped) > 40 and len(key_lines) < 10:
                key_lines.append(stripped[:120])
        result = "\n".join(key_lines)
        if len(result) > cls.MAX_SUMMARY_CHARS:
            result = result[:cls.MAX_SUMMARY_CHARS] + "\n[...]"
        return result

    @classmethod
    def chunk(cls, text: str, max_chunk: Optional[int] = None) -> list:
        """Split text into chunks for separate processing."""
        if max_chunk is None:
            max_chunk = cls.MAX_CHUNK_CHARS
        if not text:
            return []
        chunks = []
        for i in range(0, len(text), max_chunk):
            chunks.append(text[i:i + max_chunk])
        return chunks


# ── Unified TokenGuard ─────────────────────────────────────────────────────

class TokenGuard:
    """Token budget guard: dollar-based + token-count per mode."""

    MAX_SEANS = MAX_SEANS
    WARN_AT = WARN_AT
    FLASH_AT = FLASH_AT
    STOP_AT = STOP_AT

    @staticmethod
    def check(mode: Optional[str] = None) -> dict:
        """Check budget.

        Args:
            mode: None for dollar-based check (returns status/usage/budget_left),
                  or "quick"/"deep"/"background" for token-count check
                  (returns mode/used/soft/hard/status/remaining).
        """
        if mode is not None:
            return token_budget_check(mode)

        # Dollar-based (backward compat with brain.token)
        usage = track_usage()
        current = float(usage.get("session_cost", usage.get("usage", 0.0)) or 0.0)
        ratio = current / MAX_SEANS if MAX_SEANS else 1.0
        if ratio >= STOP_AT:
            status = "stop"
        elif ratio >= FLASH_AT:
            status = "flash"
        elif ratio >= WARN_AT:
            status = "warn"
        else:
            status = "ok"
        return {
            "status": status,
            "usage": current,
            "budget_left": max(MAX_SEANS - current, 0.0),
        }

    @staticmethod
    def guard(mode: str = "quick") -> bool:
        """Return False if hard limit exceeded (should block operation)."""
        result = token_budget_check(mode)
        return result["status"] != "hard"
