import importlib
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def ctx(tmp_path, monkeypatch):
    cm = importlib.import_module("brain.context_manager")
    monkeypatch.setattr(cm, "CONTEXT_EVENTS_PATH", tmp_path / "topics.jsonl")
    monkeypatch.setattr(cm, "CONTEXT_STATE_PATH", tmp_path / "topics_state.json")
    base = datetime(2026, 6, 11, 12, 0, tzinfo=timezone.utc)
    clock = {"now": base}
    monkeypatch.setattr(cm, "utc_now", lambda: clock["now"])
    return cm, clock


def test_new_topic_creates_active_topic(ctx):
    cm, _ = ctx
    topic = cm.new_topic("Denizbank odemesini takip et", "iş")
    assert topic["id"] == 1
    assert topic["active"] is True
    assert topic["type"] == "iş"


def test_list_topics_returns_active_topics(ctx):
    cm, _ = ctx
    cm.new_topic("Toplantı hazırlığı", "iş")
    items = cm.list_topics()
    assert len(items) == 1
    assert items[0]["active"] is True
    assert items[0]["kalan_zaman"] > 0


def test_close_topic_by_id_deactivates_topic(ctx):
    cm, _ = ctx
    topic = cm.new_topic("Duygusal konuşma", "duygusal")
    closed = cm.close_topic(topic["id"])
    assert closed["active"] is False
    assert cm.list_topics() == []


def test_close_last_topic_closes_most_recent(ctx):
    cm, _ = ctx
    first = cm.new_topic("Birinci iş", "iş")
    second = cm.new_topic("İkinci iş", "iş")
    closed = cm.close_topic("son konu")
    assert closed["id"] == second["id"]
    items = cm.list_topics(active_only=False)
    assert any(item["id"] == first["id"] and item["active"] for item in items)
    assert any(item["id"] == second["id"] and not item["active"] for item in items)


def test_topic_expires_automatically(ctx):
    cm, clock = ctx
    topic = cm.new_topic("Kısa görüşme", "sohbet", ttl_minutes=1)
    clock["now"] = clock["now"].replace(minute=clock["now"].minute + 2)
    items = cm.list_topics()
    assert items == []
    assert cm.recall_topic(topic["id"]).startswith("#1")


def test_low_priority_topic_goes_background_on_new_topic(ctx):
    cm, _ = ctx
    first = cm.new_topic("Eski sohbet", "sohbet", priority=40)
    second = cm.new_topic("Yeni iş görevi", "iş", priority=80)
    items = cm.list_topics(active_only=False)
    assert any(item["id"] == first["id"] and item["active"] is False for item in items)
    assert any(item["id"] == second["id"] and item["active"] is True for item in items)


def test_get_active_topic_returns_highest_priority(ctx):
    cm, _ = ctx
    cm.new_topic("Düşük öncelik", "sohbet", priority=30)
    high = cm.new_topic("Yüksek öncelik", "karar", priority=90)
    active = cm.get_active_topic()
    assert active["id"] == high["id"]
    assert active["priority"] == 90


def test_recall_topic_returns_summary(ctx):
    cm, _ = ctx
    topic = cm.new_topic("Geçen hafta konuşulan finans", "iş")
    summary = cm.recall_topic(topic["id"])
    assert "Geçen hafta konuşulan finans" in summary
    assert "iş" in summary


def test_list_topics_can_include_inactive(ctx):
    cm, _ = ctx
    topic = cm.new_topic("Kapanacak konu", "iş")
    cm.close_topic(topic["id"])
    items = cm.list_topics(active_only=False)
    assert len(items) == 1
    assert items[0]["active"] is False


def test_close_unknown_topic_returns_none(ctx):
    cm, _ = ctx
    assert cm.close_topic(9999) is None

