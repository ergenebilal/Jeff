import json
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def test_detect_tone_uses_utc_hour(monkeypatch):
    import brain.mood as mood

    class FakeDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 6, 6, 7, 0, tzinfo=tz)

    monkeypatch.setattr(mood, "datetime", FakeDateTime)
    monkeypatch.setattr(mood, "_is_critical", lambda: False)

    assert mood.detect_tone() == "enerjik"


def test_tone_is_valid():
    from brain.mood import detect_tone

    assert detect_tone() in {"keskin", "enerjik", "analitik", "rahat", "koruyucu"}


def test_format_shortens_sharp_tone():
    from brain.mood import format_by_tone

    result = format_by_tone("a" * 300, tone="keskin")

    assert len(result) <= 160
    assert result.endswith("...")


def test_protective_adds_warning():
    from brain.mood import format_by_tone

    assert format_by_tone("Token limiti asildi", tone="koruyucu").startswith("⚠️")


def test_critical_gateway_state_selects_protective(tmp_path, monkeypatch):
    import brain.mood as mood

    state_dir = tmp_path / ".hermes"
    state_dir.mkdir()
    (state_dir / "agent_state.json").write_text(json.dumps({"last_gateway_check": "dead"}), encoding="utf-8")
    monkeypatch.setenv("HOME", str(tmp_path))

    monkeypatch.setattr(mood, "_is_critical", lambda: True)
    assert mood.detect_tone() == "koruyucu"
