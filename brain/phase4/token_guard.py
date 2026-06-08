"""Token economy guard: budget enforcement, chunk + summarize + compression."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

BUDGET_LOG = Path.home() / ".hermes" / "logs" / "token_budget.jsonl"
BUDGET_LOG.parent.mkdir(parents=True, exist_ok=True)


# ── Budget limits ──────────────────────────────────────────────────────────
BUDGET_LIMITS = {
    "quick": {"soft": 20_000, "hard": 40_000},
    "deep": {"soft": 60_000, "hard": 100_000},
    "background": {"soft": 40_000, "hard": 80_000},
}


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


def log_token_usage(tokens: int, mode: str, action: str):
    """Append a token usage entry to the budget log."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tokens": tokens,
        "mode": mode,
        "action": action,
    }
    try:
        with BUDGET_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


# ── Chunk + Summarize + Compression ────────────────────────────────────────

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


class TokenGuard:
    """Token budget guard per mode (quick/deep/background)."""

    @staticmethod
    def check(mode: str = "quick") -> dict:
        """Check budget and return status + stats."""
        return token_budget_check(mode)

    @staticmethod
    def guard(mode: str = "quick") -> bool:
        """Return False if hard limit exceeded (should block operation)."""
        result = token_budget_check(mode)
        return result["status"] != "hard"
