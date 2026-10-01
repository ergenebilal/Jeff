"""Phase 1 testleri: creation, persist, recovery (+ validatorlar)."""

import json
import tempfile
from pathlib import Path

import pytest

from jeff_cognitive import CognitiveState, CognitiveStore


@pytest.fixture()
def store():
    with tempfile.TemporaryDirectory() as tmp:
        yield CognitiveStore(Path(tmp) / "cognitive.db")


def test_goal_creation_minimum_fields():
    s = CognitiveState(objective="Ilk odemeli musteri")
    assert s.goal_id
    assert s.objective == "Ilk odemeli musteri"
    assert s.current_phase == "GOAL"
    assert s.success_criteria == []
    assert s.confidence == 0.0
    assert s.created_at and s.updated_at


def test_state_serializable():
    s = CognitiveState(objective="X", success_criteria=["a", "b"])
    payload = s.to_json()
    assert isinstance(payload, str)
    s2 = CognitiveState.from_json(payload)
    assert s2.to_dict() == s.to_dict()
    # tum alanlar JSON-safe
    json.dumps(s.to_dict(), ensure_ascii=False)


def test_store_create_save_load(store):
    s = store.create(
        objective="Bursa emlak audit satilabilir mi?",
        success_criteria=["10 ofis denetle", "2/10 odeme niyeti"],
        session_id="sess-1",
        external_refs={"goals_db": {"session_id": "sess-1"}},
    )
    loaded = store.load(s.goal_id)
    assert loaded.goal_id == s.goal_id
    assert loaded.objective.startswith("Bursa")
    assert loaded.external_refs["goals_db"]["session_id"] == "sess-1"


def test_state_recovery_after_reopen():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "cognitive.db"
        store1 = CognitiveStore(db)
        s = store1.create(objective="resume testi", session_id="sess-r")
        store1.transition(s, "UNDERSTAND", reason="hedef alindi")
        # yeni connection = process restart simulasyonu
        store2 = CognitiveStore(db)
        resumed = store2.load(s.goal_id)
        assert resumed.current_phase == "UNDERSTAND"
        assert store2.transitions(s.goal_id)[0]["reason"] == "hedef alindi"
        assert [x.goal_id for x in store2.list_open("sess-r")] == [s.goal_id]


def test_list_open_excludes_done(store):
    a = store.create(objective="acik", session_id="s")
    b = store.create(objective="kapali", session_id="s")
    store.transition(b, "DONE", reason="bitti")
    ids = [x.goal_id for x in store.list_open("s")]
    assert a.goal_id in ids and b.goal_id not in ids


def test_evidence_defaults_unknown_and_validates():
    s = CognitiveState(objective="X")
    ev = s.add_evidence("gozlem", source="saha")
    assert ev["level"] == "UNKNOWN"  # sessiz TRUE yok
    with pytest.raises(ValueError):
        s.add_evidence("x", level="TRUE")


def test_confidence_risk_phase_validation():
    with pytest.raises(ValueError):
        CognitiveState(objective="X", confidence=1.5)
    with pytest.raises(ValueError):
        CognitiveState(objective="X", risk_level="extreme")
    with pytest.raises(ValueError):
        CognitiveState(objective="X", current_phase="MAGIC")


def test_budget_tracking():
    s = CognitiveState(objective="X", budget={"limit": 10.0, "spent": 0.0, "currency": "USD"})
    s.spend(2.5)
    assert s.budget["spent"] == pytest.approx(2.5)


def test_load_missing_raises(store):
    with pytest.raises(KeyError):
        store.load("yok-123")
