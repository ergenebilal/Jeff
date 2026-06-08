import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def test_assess_empty_history_is_neutral(tmp_path, monkeypatch):
    import brain.advisors as advisors

    monkeypatch.setattr(advisors, "STATE_PATH", tmp_path / "agent_state.json")
    monkeypatch.setattr(advisors, "LESSONS_PATH", tmp_path / "lessons.jsonl")

    result = advisors.assess_proposal("yeni bir is yap", "bilinmeyen")

    assert result["similar_count"] == 0
    assert result["success_rate"] == 0.5
    assert result["warning"] is None


def test_assess_proposal_uses_reasoning_tree_and_lessons(tmp_path, monkeypatch):
    import brain.advisors as advisors

    state_path = tmp_path / "agent_state.json"
    lessons_path = tmp_path / "lessons.jsonl"
    state_path.write_text(
        json.dumps(
            {
                "reasoning_tree": [
                    {"command": "systemctl restart gateway", "task": "gateway restart", "outcome": "success"},
                    {"command": "systemctl restart gateway", "task": "gateway restart", "outcome": "failed"},
                ]
            }
        ),
        encoding="utf-8",
    )
    lessons_path.write_text(
        json.dumps({"category": "workflow", "trigger": "gateway restart", "lesson": "once health kontrol et"}) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(advisors, "STATE_PATH", state_path)
    monkeypatch.setattr(advisors, "LESSONS_PATH", lessons_path)

    result = advisors.assess_proposal("gateway restart yap", "gateway restart")

    assert result["similar_count"] == 2
    assert result["success_rate"] == 0.5
    assert "once health kontrol et" in result["suggestion"]


def test_low_success_rate_warns(tmp_path, monkeypatch):
    import brain.advisors as advisors

    state_path = tmp_path / "agent_state.json"
    state_path.write_text(
        json.dumps(
            {
                "reasoning_tree": [
                    {"command": "docker compose down n8n", "task": "n8n servis", "outcome": "failed"},
                    {"command": "docker compose restart n8n", "task": "n8n servis", "outcome": "failed"},
                    {"command": "systemctl restart n8n", "task": "n8n servis", "outcome": "success"},
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(advisors, "STATE_PATH", state_path)
    monkeypatch.setattr(advisors, "LESSONS_PATH", tmp_path / "lessons.jsonl")

    result = advisors.assess_proposal("n8n servis restart", "n8n servis")

    assert result["success_rate"] < 0.4
    assert result["warning"]


def test_format_assessment_is_readable():
    from brain.advisors import format_assessment

    text = format_assessment({"similar_count": 3, "success_rate": 0.66, "warning": None, "suggestion": "test"})

    assert "66" in text
    assert "test" in text


def test_advisor_compatibility_module_exports_same_api():
    from brain.advisor import assess_proposal

    assert callable(assess_proposal)
