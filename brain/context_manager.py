"""Append-only topic context manager for Hermes."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional


CONTEXT_DIR = Path.home() / ".hermes" / "context"
CONTEXT_EVENTS_PATH = CONTEXT_DIR / "topics.jsonl"
CONTEXT_STATE_PATH = CONTEXT_DIR / "topics_state.json"

_DEFAULT_TTLS = {
    "duygusal": 60,
    "sohbet": 180,
    "iş": 1440,
    "is": 1440,
    "iş/karar": 1440,
    "karar": 1440,
    "business": 1440,
    "work": 1440,
}
_DEFAULT_PRIORITIES = {
    "duygusal": 35,
    "sohbet": 45,
    "iş": 80,
    "is": 80,
    "iş/karar": 90,
    "karar": 90,
    "business": 80,
    "work": 80,
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def new_topic(content: str, topic_type: str, ttl_minutes: Optional[int] = None, priority: Optional[int] = None) -> dict[str, Any]:
    """Create a new active topic and persist it."""
    normalized_content = str(content or "").strip()
    normalized_type = _normalize_topic_type(topic_type)
    if not normalized_content:
        raise ValueError("content cannot be empty")

    now = utc_now()
    state = _load_state()
    topics = _purge_expired(state.get("topics", []), now)
    next_id = int(state.get("next_id", 1))
    resolved_ttl = int(ttl_minutes) if ttl_minutes is not None else _DEFAULT_TTLS.get(normalized_type, 240)
    resolved_priority = int(priority) if priority is not None else _DEFAULT_PRIORITIES.get(normalized_type, 50)

    topic = _build_topic(
        topic_id=next_id,
        content=normalized_content,
        topic_type=normalized_type,
        priority=resolved_priority,
        ttl_minutes=resolved_ttl,
        now=now,
    )

    max_active_priority = max(
        (int(item.get("priority", 0)) for item in topics if item.get("active")),
        default=None,
    )
    if max_active_priority is not None and resolved_priority > max_active_priority:
        for item in topics:
            if item.get("active") and int(item.get("priority", 0)) < resolved_priority:
                _background_topic(item, now)

    topics.append(topic)
    _save_state({"next_id": next_id + 1, "topics": topics})
    _append_event({"event": "new_topic", "topic": topic})
    return deepcopy(topic)


def close_topic(topic_id: Any) -> Optional[dict[str, Any]]:
    """Close one topic by id or by 'son konu'."""
    state = _load_state()
    topics = _purge_expired(state.get("topics", []), utc_now())
    target = _resolve_topic_id(topic_id, topics)
    if target is None:
        return None

    now = utc_now()
    updated = None
    for item in topics:
        if int(item.get("id", -1)) == target and item.get("active"):
            _close_topic(item, now)
            updated = deepcopy(item)
            break
    if updated is None:
        return None

    _save_state({"next_id": int(state.get("next_id", 1)), "topics": topics})
    _append_event({"event": "close_topic", "topic": updated})
    return updated


def list_topics(active_only: bool = True) -> list[dict[str, Any]]:
    """List topics, optionally only active ones."""
    state = _load_state()
    topics = _purge_expired(state.get("topics", []), utc_now())
    if not topics:
        _save_state({"next_id": int(state.get("next_id", 1)), "topics": []})
        return []

    _save_state({"next_id": int(state.get("next_id", 1)), "topics": topics})
    items = [deepcopy(item) for item in topics if not active_only or item.get("active")]
    for item in items:
        item["kalan_zaman"] = _remaining_minutes(item, utc_now())
    return sorted(items, key=lambda item: int(item.get("id", 0)))


def recall_topic(topic_id: Any) -> str:
    """Return a short summary for a topic."""
    state = _load_state()
    topics = _purge_expired(state.get("topics", []), utc_now())
    item = _find_topic(topic_id, topics)
    if not item:
        return ""
    remaining = _remaining_minutes(item, utc_now())
    return (
        f"#{item.get('id')} [{item.get('type')}] {item.get('content')} | "
        f"priority={item.get('priority')} | active={item.get('active')} | kalan_zaman={remaining}dk"
    )


def get_active_topic() -> Optional[dict[str, Any]]:
    """Return the highest-priority active topic."""
    topics = list_topics(active_only=True)
    if not topics:
        return None
    return deepcopy(max(topics, key=lambda item: (int(item.get("priority", 0)), int(item.get("id", 0)))))


def _normalize_topic_type(topic_type: Any) -> str:
    value = str(topic_type or "").strip().lower()
    mapping = {
        "iş": "iş",
        "is": "is",
        "karar": "karar",
        "sohbet": "sohbet",
        "duygusal": "duygusal",
        "business": "business",
        "work": "work",
    }
    return mapping.get(value, value or "sohbet")


def _build_topic(topic_id: int, content: str, topic_type: str, priority: int, ttl_minutes: int, now: datetime) -> dict[str, Any]:
    expires_at = now + timedelta(minutes=max(ttl_minutes, 1))
    return {
        "id": topic_id,
        "content": content,
        "type": topic_type,
        "priority": max(0, int(priority)),
        "ttl_minutes": max(1, int(ttl_minutes)),
        "active": True,
        "status": "active",
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "closed_at": None,
    }


def _close_topic(topic: dict[str, Any], now: datetime, status: str = "closed") -> None:
    topic["active"] = False
    topic["status"] = status
    topic["updated_at"] = now.isoformat()
    topic["closed_at"] = now.isoformat()


def _background_topic(topic: dict[str, Any], now: datetime) -> None:
    topic["active"] = False
    topic["status"] = "backgrounded"
    topic["updated_at"] = now.isoformat()


def _expires_at(topic: dict[str, Any]) -> Optional[datetime]:
    raw = topic.get("expires_at")
    if not raw:
        return None
    try:
        value = datetime.fromisoformat(str(raw))
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _remaining_minutes(topic: dict[str, Any], now: datetime) -> int:
    expiry = _expires_at(topic)
    if expiry is None:
        return 0
    remaining = int((expiry - now).total_seconds() // 60)
    return max(0, remaining)


def _purge_expired(topics: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
    changed = False
    normalized = []
    for item in topics:
        topic = deepcopy(item) if isinstance(item, dict) else {}
        if not topic:
            continue
        expiry = _expires_at(topic)
        if topic.get("active") and expiry is not None and now >= expiry:
            _close_topic(topic, now, status="expired")
            changed = True
            _append_event({"event": "expire_topic", "topic": deepcopy(topic)})
        normalized.append(topic)
    if changed:
        return normalized
    return normalized


def _resolve_topic_id(topic_id: Any, topics: list[dict[str, Any]]) -> Optional[int]:
    if isinstance(topic_id, str) and topic_id.strip().lower() == "son konu":
        active = [item for item in topics if item.get("active")]
        if not active:
            return None
        return int(max(active, key=lambda item: int(item.get("id", 0))).get("id"))
    try:
        return int(topic_id)
    except Exception:
        return None


def _find_topic(topic_id: Any, topics: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    resolved = _resolve_topic_id(topic_id, topics)
    if resolved is None:
        return None
    for item in topics:
        if int(item.get("id", -1)) == resolved:
            return item
    return None


def _load_state() -> dict[str, Any]:
    try:
        if CONTEXT_STATE_PATH.exists():
            raw = CONTEXT_STATE_PATH.read_text(encoding="utf-8")
            data = json.loads(raw)
            if isinstance(data, dict):
                data.setdefault("topics", [])
                data.setdefault("next_id", 1)
                return data
    except Exception:
        pass

    topics: list[dict[str, Any]] = []
    next_id = 1
    try:
        if CONTEXT_EVENTS_PATH.exists():
            for line in CONTEXT_EVENTS_PATH.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                payload = json.loads(line)
                if not isinstance(payload, dict):
                    continue
                event = payload.get("event")
                topic = payload.get("topic")
                if not isinstance(topic, dict):
                    continue
                topic_id = int(topic.get("id", 0))
                next_id = max(next_id, topic_id + 1)
                if event == "new_topic":
                    topics.append(deepcopy(topic))
                elif event in {"close_topic", "expire_topic"}:
                    _upsert_topic(topics, topic)
    except Exception:
        pass
    return {"next_id": next_id, "topics": topics}


def _upsert_topic(topics: list[dict[str, Any]], topic: dict[str, Any]) -> None:
    topic_id = int(topic.get("id", 0))
    for idx, item in enumerate(topics):
        if int(item.get("id", 0)) == topic_id:
            topics[idx] = deepcopy(topic)
            return
    topics.append(deepcopy(topic))


def _save_state(state: dict[str, Any]) -> None:
    try:
        CONTEXT_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = CONTEXT_STATE_PATH.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(CONTEXT_STATE_PATH)
    except Exception:
        pass


def _append_event(event: dict[str, Any]) -> None:
    try:
        CONTEXT_EVENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
        with CONTEXT_EVENTS_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception:
        pass
