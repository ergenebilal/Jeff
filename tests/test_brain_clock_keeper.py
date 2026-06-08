import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def test_guard_updates_missing_last_sync(tmp_path):
    from brain.clock_keeper import TimeSyncGuard

    now = datetime(2026, 6, 6, 22, 30, 0, tzinfo=timezone.utc)
    state_path = tmp_path / "agent_state.json"

    result = TimeSyncGuard(state_path=state_path, now_fn=lambda: now).check()

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert result["synced"] is True
    assert state["last_sync"] == "2026-06-06T22:30:00Z"
    assert state["clock_keeper"]["server_utc"] == "2026-06-06T22:30:00Z"


def test_guard_repairs_drift_above_100ms(tmp_path):
    from brain.clock_keeper import TimeSyncGuard

    now = datetime(2026, 6, 6, 22, 30, 0, tzinfo=timezone.utc)
    state_path = tmp_path / "agent_state.json"
    state_path.write_text(json.dumps({"last_sync": "2026-06-06T22:29:59.800000Z"}), encoding="utf-8")

    result = TimeSyncGuard(state_path=state_path, now_fn=lambda: now).check()

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert result["synced"] is True
    assert result["drift_ms"] == 200.0
    assert state["last_sync"] == "2026-06-06T22:30:00Z"


def test_guard_keeps_logic_time_when_drift_under_threshold(tmp_path):
    from brain.clock_keeper import TimeSyncGuard

    now = datetime(2026, 6, 6, 22, 30, 0, tzinfo=timezone.utc)
    previous = now - timedelta(milliseconds=50)
    state_path = tmp_path / "agent_state.json"
    state_path.write_text(json.dumps({"last_sync": previous.isoformat().replace("+00:00", "Z")}), encoding="utf-8")

    result = TimeSyncGuard(state_path=state_path, now_fn=lambda: now).check()

    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert result["synced"] is False
    assert result["drift_ms"] == 50.0
    assert state["last_sync"] == previous.isoformat().replace("+00:00", "Z")


def test_context_loader_runs_clock_guard_and_uses_utc(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    import brain.context_loader as context_loader

    calls = []
    monkeypatch.setattr(context_loader, "get_lessons_summary", lambda limit: "lesson-summary")

    class FakeGuard:
        def check(self):
            calls.append("checked")
            return {"server_utc": "2026-06-06T22:30:00Z", "synced": True, "drift_ms": 150.0}

    monkeypatch.setattr(context_loader, "TimeSyncGuard", FakeGuard)
    monkeypatch.setattr(context_loader, "utc_now", lambda: datetime(2026, 6, 6, 22, 30, 0, tzinfo=timezone.utc))

    context = context_loader.get_relevant_context("clock")

    assert calls == ["checked"]
    assert "UTC 2026-06-06T22:30:00Z" in context
    assert "Clock Keeper: synced" in context


def test_run_clock_keeper_returns_utc_status(monkeypatch, tmp_path):
    import brain.clock_keeper as clock_keeper

    state_path = tmp_path / "agent_state.json"
    monkeypatch.setattr(clock_keeper, "STATE_PATH", state_path)
    monkeypatch.setattr(clock_keeper, "utc_now", lambda: datetime(2026, 6, 6, 22, 30, 0, tzinfo=timezone.utc))

    status = clock_keeper.run_clock_keeper()

    assert "Clock Keeper: synced" in status
    assert "utc=2026-06-06T22:30:00Z" in status
