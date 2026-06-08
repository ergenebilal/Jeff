import importlib
import json
import os
import sys
import tempfile
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def isolated_home(monkeypatch):
    """Isolate brain.learning by monkeypatching LESSONS_FILE directly.

    Path.home() cannot be relied upon for isolation because brain/__init__.py
    caches the 'brain.learning' reference at import time.  We override the
    module-level path constants instead.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        fake_lessons = tmp_path / ".hermes" / "learning" / "lessons.jsonl"
        fake_lessons.parent.mkdir(parents=True, exist_ok=True)

        # Pop cached modules so they get reimported with our patches
        for mod_name in ["brain.learning", "brain.context_loader"]:
            sys.modules.pop(mod_name, None)

        # Import fresh and patch paths
        learning = importlib.import_module("brain.learning")
        monkeypatch.setattr(learning, "LESSONS_FILE", fake_lessons)
        monkeypatch.setattr(learning, "LEARNING_DIR", fake_lessons.parent)

        yield tmp_path

    for mod_name in ["brain.learning", "brain.context_loader"]:
        sys.modules.pop(mod_name, None)


def test_save_lesson_clamps_importance_and_appends_jsonl(isolated_home):
    learning = importlib.import_module("brain.learning")
    entry = learning.save_lesson("preference", "format", "Kisa ozet once gelir", 1.7, source="test")
    assert entry["importance"] == 1.0
    assert entry["applied_count"] == 0
    stored = json.loads(learning.LESSONS_FILE.read_text(encoding="utf-8").strip())
    assert stored["lesson"] == "Kisa ozet once gelir"
    assert stored["source"] == "test"


def test_recent_lessons_are_newest_first_and_filter_by_category(isolated_home):
    learning = importlib.import_module("brain.learning")
    learning.save_lesson("preference", "format", "once ozet", 0.8)
    learning.save_lesson("fact", "identity", "Bilal insan, Hermes ajan", 0.9)
    learning.save_lesson("preference", "tone", "anlasilir dil", 0.7)

    recent = learning.get_recent_lessons(limit=2)
    assert [item["trigger"] for item in recent] == ["tone", "identity"]
    preferences = learning.get_recent_lessons(limit=10, category="preference")
    assert [item["trigger"] for item in preferences] == ["tone", "format"]


def test_lessons_summary_is_conversation_ready(isolated_home):
    learning = importlib.import_module("brain.learning")
    assert learning.get_lessons_summary(3) == "Henüz öğrenilmiş ders yok."
    learning.save_lesson("workflow", "spec", "once test sonra patch", 0.85)
    summary = learning.get_lessons_summary(3)
    assert "[workflow ^(0.85)]" in summary
    assert "spec -> once test sonra patch" in summary


def test_mark_applied_increments_matching_trigger(isolated_home):
    learning = importlib.import_module("brain.learning")
    learning.save_lesson("pattern", "risk", "risk korumasi ekle", 0.75)
    learning.mark_applied("risk")
    [lesson] = learning.get_recent_lessons(1)
    assert lesson["applied_count"] == 1


def test_sync_all_to_mnemosyne_returns_count(isolated_home, monkeypatch):
    learning = importlib.import_module("brain.learning")
    monkeypatch.setattr(learning, "_push_to_mnemosyne", lambda entry: True)
    learning.save_lesson("test", "one", "bir", 0.5)
    learning.save_lesson("test", "two", "iki", 0.5)
    assert learning.sync_all_to_mnemosyne() == "2 ders Mnemosyne'e senkronize edildi."


def test_push_to_mnemosyne_prefers_python_client(monkeypatch):
    learning = importlib.import_module("brain.learning")
    calls = []

    class FakeMnemosyne:
        def __init__(self, session_id, bank):
            calls.append(("init", session_id, bank))
        def remember(self, content, source, importance, metadata=None):
            calls.append(("remember", content, source, importance, metadata))

    monkeypatch.setitem(sys.modules, "mnemosyne", types.SimpleNamespace(Mnemosyne=FakeMnemosyne))
    assert learning._push_to_mnemosyne({"category": "test", "trigger": "x", "lesson": "y", "importance": 0.7})
    assert calls[0] == ("init", "hermes-learning", "lessons")
    assert calls[1][2] == "learning"


def test_context_loader_includes_lessons_time_and_reasoning(isolated_home, monkeypatch):
    learning = importlib.import_module("brain.learning")
    learning.save_lesson("preference", "format", "kisa ozet", 0.9)
    context_loader = importlib.import_module("brain.context_loader")
    monkeypatch.setattr("brain.reasoning_tree.summarize", lambda: "3 karar | son karar basarili")
    context = context_loader.get_relevant_context("format")
    assert "Öğrendiklerim" in context
    assert "kisa ozet" in context
    assert "3 karar | son karar basarili" in context


def test_learning_facade_exports_public_api():
    import brain
    assert callable(brain.save_lesson)
    assert callable(brain.get_recent_lessons)
    assert callable(brain.get_relevant_context)


def test_system_prompt_volatile_tier_includes_learning_context(monkeypatch):
    """Skip if the installed agent doesn't have the required modules."""
    try:
        import run_agent
    except ImportError:
        pytest.skip("run_agent not available in this environment")
    try:
        from agent import system_prompt
    except ImportError:
        pytest.skip("agent.system_prompt not available in this environment")

    from brain.learning import save_lesson

    monkeypatch.setattr(run_agent, "load_soul_md", lambda: "")
    monkeypatch.setattr(run_agent, "build_nous_subscription_prompt", lambda tools: "")
    monkeypatch.setattr(run_agent, "build_context_files_prompt", lambda **kwargs: "")
    monkeypatch.setattr(run_agent, "build_environment_hints", lambda: "")
    monkeypatch.setattr("brain.learning._push_to_mnemosyne", lambda entry: True)
    save_lesson("preference", "prompt", "conversation start must recall lessons", 0.8)

    class Agent:
        load_soul_identity = False
        skip_context_files = True
        valid_tool_names = []
        _task_completion_guidance = True
        _kanban_worker_guidance = ""
        _tool_use_enforcement = "auto"
        _environment_probe = False
        platform = ""
        provider = ""
        model = ""
        pass_session_id = False
        session_id = ""
        _memory_store = None
        _memory_enabled = False
        _user_profile_enabled = False
        _memory_manager = None

    parts = system_prompt.build_system_prompt_parts(Agent())
    assert "Hermes learned context" in parts["volatile"]
    assert "conversation start must recall lessons" in parts["volatile"]
