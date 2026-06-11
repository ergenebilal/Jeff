"""Layered retrieval bridge for Hermes memory recall.

L1 = live session / clock / topic framing
L2 = recent lessons
L3 = recent decisions
L4 = durable cross-session summary
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .clock_keeper import TimeSyncGuard, utc_now
from . import learning, reasoning_tree

RETRIEVAL_LOG = Path.home() / ".hermes" / "logs" / "retrieval_trace.jsonl"


def _append_jsonl(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return payload


def _utc_iso() -> str:
    return utc_now().astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _summarize_lessons(limit: int) -> str:
    summary = learning.get_lessons_summary(limit)
    return summary if summary else "Henüz öğrenilmiş ders yok."


def _summarize_decisions() -> str:
    summary = reasoning_tree.summarize()
    return summary if summary else "Henüz karar kaydı yok."


def build_retrieval_layers(topic: str = "", limit: int = 5) -> dict:
    """Build a four-layer retrieval snapshot and persist it for inspection."""
    topic_text = str(topic or "").strip()
    limit = max(int(limit), 0)

    clock = TimeSyncGuard().check()
    lessons = learning.get_recent_lessons(limit=limit, category=topic_text or None)
    if not lessons and topic_text:
        lessons = learning.get_recent_lessons(limit=limit, category=None)
    decisions = reasoning_tree.get_recent(limit=limit)

    layers = [
        {
            "layer": "L1",
            "source": "session",
            "summary": (
                f"L1 session | topic={topic_text or 'global'} | "
                f"utc={clock.get('server_utc')} | drift={clock.get('drift_ms')}ms | synced={clock.get('synced')}"
            ),
            "items": [
                {
                    "kind": "clock",
                    "server_utc": clock.get("server_utc"),
                    "drift_ms": clock.get("drift_ms"),
                    "synced": clock.get("synced"),
                },
                {"kind": "topic", "value": topic_text or "global"},
            ],
        },
        {
            "layer": "L2",
            "source": "lessons",
            "summary": f"L2 lessons | {len(lessons)} item | {_summarize_lessons(min(limit, 3))}",
            "items": lessons,
        },
        {
            "layer": "L3",
            "source": "decisions",
            "summary": f"L3 decisions | {len(decisions)} item | {_summarize_decisions()}",
            "items": decisions,
        },
        {
            "layer": "L4",
            "source": "durable",
            "summary": (
                "L4 durable | cross-session recall ready | "
                f"lessons={len(lessons)} decisions={len(decisions)}"
            ),
            "items": [
                {"kind": "lesson_digest", "text": _summarize_lessons(limit or 1)},
                {"kind": "decision_digest", "text": _summarize_decisions()},
            ],
        },
    ]

    payload = {
        "event": "retrieval_snapshot",
        "timestamp_utc": _utc_iso(),
        "topic": topic_text,
        "limit": limit,
        "layers": layers,
    }
    _append_jsonl(RETRIEVAL_LOG, payload)
    return payload


def format_retrieval_layers(snapshot: dict) -> str:
    """Render a compact prompt-safe representation of a retrieval snapshot."""
    lines = []
    for layer in snapshot.get("layers", []):
        lines.append(f"{layer.get('layer')}: {layer.get('summary')}")
    return "\n".join(lines)


__all__ = ["RETRIEVAL_LOG", "build_retrieval_layers", "format_retrieval_layers"]
