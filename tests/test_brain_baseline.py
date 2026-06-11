import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def test_collect_baseline_snapshot_includes_ops_and_persona(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    profile = tmp_path / ".hermes" / "jeff-profile.json"
    profile.parent.mkdir(parents=True, exist_ok=True)
    profile.write_text(
        json.dumps(
            {
                "identity": {
                    "name": "Jeff",
                    "official_name": "Hermes Agent v2",
                    "master": "Bilal",
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("brain.persona.PERSONA_PROFILE_PATH", profile)

    from brain.baseline import collect_baseline_snapshot

    snapshot = collect_baseline_snapshot(
        test_count=610,
        services={"gateway": True, "embedding": True, "headroom": True, "n8n": False},
    )

    assert snapshot["tests"]["collected"] == 610
    assert snapshot["persona"]["primary_name"] == "Jeff"
    assert snapshot["persona"]["technical_name"] == "Hermes Agent v2"
    assert snapshot["ops"]["services"]["gateway"] is True
    assert snapshot["ops"]["status"] in {"ok", "degraded"}


def test_import_legacy_memory_records_messages(tmp_path, monkeypatch):
    from brain.legacy_memory import import_legacy_memory

    monkeypatch.setenv("HOME", str(tmp_path))
    payload = {
        "messages": [
            {"role": "user", "content": "Geçen hafta finans konuşmuştuk."},
            {"role": "assistant", "content": "Denizbank acil demiştik."},
        ]
    }
    source = tmp_path / "history.json"
    source.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    result = import_legacy_memory(source)

    assert result["imported"] == 2
    assert result["skipped"] == 0
    assert result["source"] == str(source)
