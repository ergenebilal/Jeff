"""Continuous learning helpers backed by a local JSONL lesson log."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LEARNING_DIR = Path.home() / ".hermes" / "learning"
LESSONS_FILE = LEARNING_DIR / "lessons.jsonl"


def _ensure_dir() -> None:
    LEARNING_DIR.mkdir(parents=True, exist_ok=True)


def save_lesson(
    conversation: str,
    category: str,
    trigger: str,
    lesson: str,
    importance: float = 0.7,
    source: str = "brain",
) -> dict[str, Any]:
    _ensure_dir()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "conversation": str(conversation),
        "category": str(category),
        "trigger": str(trigger),
        "lesson": str(lesson)[:2000],
        "importance": max(0.0, min(1.0, float(importance))),
        "source": str(source),
        "applied_count": 0,
    }
    with LESSONS_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return entry


def get_recent_lessons(limit: int = 10, category: str | None = None) -> list[dict[str, Any]]:
    if not LESSONS_FILE.exists():
        return []
    items: list[dict[str, Any]] = []
    with LESSONS_FILE.open("r", encoding="utf-8") as handle:
        for line in handle:
            try:
                item = json.loads(line)
            except Exception:
                continue
            if isinstance(item, dict):
                items.append(item)
    if category:
        needle = str(category).lower()
        filtered = [
            item
            for item in items
            if needle in str(item.get("category", "")).lower()
            or needle in str(item.get("trigger", "")).lower()
            or needle in str(item.get("lesson", "")).lower()
        ]
        if filtered:
            items = filtered
    return items[-max(0, int(limit)) :]


def get_lessons_summary(limit: int = 10) -> str:
    lessons = get_recent_lessons(limit)
    if not lessons:
        return "Kayitli ders yok."
    return "\n".join(f"- {x.get('category','genel')}: {x.get('lesson','')}" for x in lessons)


def mark_applied(*args: Any, **kwargs: Any) -> bool:
    return True


def sync_all_to_mnemosyne() -> dict[str, Any]:
    return {"synced": 0, "status": "best_effort"}
