import importlib
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def test_retrieval_layers_expose_l1_to_l4_and_log_them(tmp_path, monkeypatch):
    import brain.retrieval as retrieval

    monkeypatch.setattr(retrieval, "RETRIEVAL_LOG", tmp_path / "retrieval_trace.jsonl")
    monkeypatch.setattr(retrieval.learning, "get_recent_lessons", lambda limit=5, category=None: [
        {"category": "preference", "trigger": "format", "lesson": "kisa ozet once", "importance": 0.9},
        {"category": "workflow", "trigger": "spec", "lesson": "once test sonra patch", "importance": 0.8},
    ])
    monkeypatch.setattr(retrieval.reasoning_tree, "get_recent", lambda limit=5: [
        {"command": "gateway restart", "task": "ops", "outcome": "success"},
        {"command": "token guard", "task": "budget", "outcome": "failed"},
    ])
    monkeypatch.setattr(retrieval.reasoning_tree, "summarize", lambda: "2 karar | son karar success")
    monkeypatch.setattr(retrieval.learning, "get_lessons_summary", lambda limit=10: "lesson-summary")

    result = retrieval.build_retrieval_layers(topic="format")

    assert result["topic"] == "format"
    assert [layer["layer"] for layer in result["layers"]] == ["L1", "L2", "L3", "L4"]
    assert [layer["source"] for layer in result["layers"]] == ["session", "lessons", "decisions", "durable"]
    assert result["layers"][0]["summary"].startswith("L1")
    assert result["layers"][1]["items"][0]["lesson"] == "kisa ozet once"
    assert result["layers"][2]["summary"].startswith("L3")
    assert result["layers"][3]["summary"].startswith("L4")
    assert retrieval.RETRIEVAL_LOG.exists()

    rows = [json.loads(line) for line in retrieval.RETRIEVAL_LOG.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows[-1]["topic"] == "format"
    assert [layer["layer"] for layer in rows[-1]["layers"]] == ["L1", "L2", "L3", "L4"]


def test_context_loader_includes_layer_labels(monkeypatch):
    import brain.context_loader as context_loader
    import brain.retrieval as retrieval

    monkeypatch.setattr(retrieval, "build_retrieval_layers", lambda topic="", limit=5: {
        "topic": topic,
        "layers": [
            {"layer": "L1", "source": "session", "summary": "L1 session", "items": []},
            {"layer": "L2", "source": "lessons", "summary": "L2 lessons", "items": []},
            {"layer": "L3", "source": "decisions", "summary": "L3 decisions", "items": []},
            {"layer": "L4", "source": "durable", "summary": "L4 durable", "items": []},
        ],
    })

    context = context_loader.get_relevant_context("format")

    assert "L1" in context
    assert "L2" in context
    assert "L3" in context
    assert "L4" in context
    assert "format" in context


def test_brain_facade_exports_retrieval_api():
    import brain

    assert callable(brain.build_retrieval_layers)
