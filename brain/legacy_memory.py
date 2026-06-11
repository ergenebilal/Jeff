"""Legacy memory import helpers for exported JSON histories."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from .learning import save_lesson


def import_legacy_memory(source: Path | str | dict[str, Any] | list[Any]) -> dict[str, Any]:
    """Import legacy conversation history into the lesson store.

    Supports:
      - JSON file path
      - dict with a ``messages`` list
      - raw list of message dicts
    """
    records = _load_records(source)
    imported = 0
    skipped = 0
    for index, record in enumerate(records):
        role = str(record.get("role", "unknown")).strip() if isinstance(record, dict) else "unknown"
        content = _extract_content(record)
        if not content:
            skipped += 1
            continue
        trigger = f"{role}_{index}"
        category = f"legacy_{role}" if role else "legacy_message"
        save_lesson(
            category=category,
            trigger=trigger,
            lesson=content,
            importance=0.5,
            source="legacy_import",
        )
        imported += 1
    return {
        "source": str(source) if not isinstance(source, (dict, list)) else "in_memory",
        "imported": imported,
        "skipped": skipped,
    }


def _load_records(source: Path | str | dict[str, Any] | list[Any]) -> list[dict[str, Any]]:
    if isinstance(source, list):
        return [item for item in source if isinstance(item, dict)]
    if isinstance(source, dict):
        messages = source.get("messages")
        if isinstance(messages, list):
            return [item for item in messages if isinstance(item, dict)]
        return [source]
    path = Path(source)
    if not path.exists():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]
    if isinstance(raw, dict):
        messages = raw.get("messages")
        if isinstance(messages, list):
            return [item for item in messages if isinstance(item, dict)]
        return [raw]
    return []


def _extract_content(record: dict[str, Any]) -> str:
    for key in ("content", "text", "message", "value", "body"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""

