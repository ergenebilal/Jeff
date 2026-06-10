"""Continuous learning layer for Hermes conversations."""

import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


LEARNING_DIR = Path.home() / ".hermes" / "learning"
LESSONS_FILE = LEARNING_DIR / "lessons.jsonl"
MNEMOSYNE_URL = "http://localhost:8767/memory"


def _ensure_dir():
    LEARNING_DIR.mkdir(parents=True, exist_ok=True)


def save_lesson(
    category: str,
    trigger: str,
    lesson: str,
    importance: float = 0.6,
    source: str = "conversation",
) -> dict:
    """Save one lesson locally and best-effort sync it to Mnemosyne."""
    _ensure_dir()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "category": str(category),
        "trigger": str(trigger),
        "lesson": str(lesson),
        "importance": min(max(float(importance), 0.0), 1.0),
        "source": str(source),
        "applied_count": 0,
    }
    with LESSONS_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    _push_to_mnemosyne(entry)
    return entry


def get_recent_lessons(limit: int = 10, category: Optional[str] = None) -> list:
    """Return recent lessons, newest first."""
    if not LESSONS_FILE.exists():
        return []
    lessons = []
    with LESSONS_FILE.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue
            if isinstance(entry, dict):
                lessons.append(entry)
    lessons.reverse()
    if category:
        lessons = [item for item in lessons if item.get("category") == category]
    return lessons[: max(int(limit), 0)]


def get_lessons_summary(limit: int = 10) -> str:
    """Build a compact conversation-start lesson summary."""
    lessons = get_recent_lessons(limit)
    if not lessons:
        return "Henüz öğrenilmiş ders yok."
    lines = []
    for item in lessons:
        category = item.get("category", "?")
        importance = item.get("importance", 0.5)
        trigger = item.get("trigger", "?")
        lesson = item.get("lesson", "?")
        lines.append(f"[{category} ^({importance})] {trigger} -> {lesson}")
    return "\n".join(lines)


def mark_applied(trigger: str):
    """Mark lessons with the matching trigger as applied."""
    if not LESSONS_FILE.exists():
        return
    updated = False
    lessons = []
    with LESSONS_FILE.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except Exception:
                continue
            if not isinstance(entry, dict):
                continue
            if entry.get("trigger") == trigger:
                entry["applied_count"] = int(entry.get("applied_count", 0)) + 1
                updated = True
                _push_to_mnemosyne(entry)
            lessons.append(entry)
    if updated:
        with LESSONS_FILE.open("w", encoding="utf-8") as handle:
            for entry in lessons:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def sync_all_to_mnemosyne():
    """Best-effort sync the latest 100 lessons to Mnemosyne."""
    count = 0
    for entry in get_recent_lessons(limit=100):
        if _push_to_mnemosyne(entry):
            count += 1
    return f"{count} ders Mnemosyne'e senkronize edildi."


def _push_to_mnemosyne(entry: dict) -> bool:
    try:
        from mnemosyne import Mnemosyne

        memory = Mnemosyne(session_id="hermes-learning", bank="lessons")
        memory.remember(
            json.dumps(entry, ensure_ascii=False),
            source="learning",
            importance=entry.get("importance", 0.6),
            metadata={
                "category": entry.get("category"),
                "trigger": entry.get("trigger"),
                "source": entry.get("source", "conversation"),
            },
        )
        return True
    except Exception:
        pass

    payload = json.dumps(
        {
            "content": json.dumps(entry, ensure_ascii=False),
            "source": "learning",
            "importance": entry.get("importance", 0.6),
            "bank": "lessons",
        },
        ensure_ascii=False,
    ).encode("utf-8")
    try:
        request = urllib.request.Request(
            MNEMOSYNE_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(request, timeout=3)
        return True
    except Exception:
        return False


if __name__ == "__main__":
    save_lesson(
        category="preference",
        trigger="format",
        lesson="Bilal wants brief summary first, then details if needed",
        importance=0.85,
        source="manual",
    )
    print(get_lessons_summary(5))
    print(sync_all_to_mnemosyne())
