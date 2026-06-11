import importlib
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _write_profile(tmp_path: Path) -> Path:
    profile_dir = tmp_path / ".hermes"
    profile_dir.mkdir(parents=True, exist_ok=True)
    profile_path = profile_dir / "jeff-profile.json"
    profile_path.write_text(
        json.dumps(
            {
                "identity": {
                    "name": "Jeff",
                    "official_name": "Hermes Agent v2",
                    "master": "Bilal",
                    "creator": "Nous Research + GSD Redux",
                    "aka": ["Hermes Agent", "COO-Strategist"],
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return profile_path


def test_build_persona_identity_block_reads_jeff_profile(tmp_path, monkeypatch):
    profile_path = _write_profile(tmp_path)
    monkeypatch.setattr("brain.persona.PERSONA_PROFILE_PATH", profile_path)
    persona = importlib.import_module("brain.persona")

    block = persona.build_persona_identity_block()

    assert "Jeff persona anchor" in block
    assert "Primary name: Jeff" in block
    assert "Technical/system name: Hermes Agent v2" in block
    assert "Never answer that your real name is Hermes Agent." in block
    assert "Bilal" in block


def test_build_persona_context_line_mentions_continuity(tmp_path, monkeypatch):
    profile_path = _write_profile(tmp_path)
    monkeypatch.setattr("brain.persona.PERSONA_PROFILE_PATH", profile_path)
    persona = importlib.import_module("brain.persona")

    line = persona.build_persona_context_line()

    assert "Persona continuity" in line
    assert "Jeff" in line
    assert "Hermes Agent v2" in line


def test_system_prompt_includes_persona_override(monkeypatch):
    try:
        import run_agent
    except ImportError:
        pytest.skip("run_agent not available in this environment")
    try:
        from agent import system_prompt
    except ImportError:
        pytest.skip("agent.system_prompt not available in this environment")

    monkeypatch.setattr(run_agent, "load_soul_md", lambda: "You are Hermes Agent, a helpful assistant.")
    monkeypatch.setattr(run_agent, "build_nous_subscription_prompt", lambda tools: "")
    monkeypatch.setattr(run_agent, "build_context_files_prompt", lambda **kwargs: "")
    monkeypatch.setattr(run_agent, "build_environment_hints", lambda: "")
    monkeypatch.setattr("brain.persona.build_persona_identity_block", lambda **kwargs: "Jeff persona anchor:\n- Primary name: Jeff.\n- Technical/system name: Hermes Agent.\n- Self-identify in first person as Jeff.")

    class Agent:
        load_soul_identity = True
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

    assert "Jeff persona anchor" in parts["stable"]
    assert "Primary name: Jeff" in parts["stable"]
    assert "Hermes Agent" in parts["stable"]

