from pathlib import Path

import brain.n8n_gate as gate


def test_enable_write_sets_ttl_and_health(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    gate.GATE_PATH = tmp_path / "n8n_write_gate.json"
    gate.LOG_PATH = tmp_path / "logs" / "n8n_write.log"

    payload = gate.enable_write(minutes=60, reason="manual", actor="hq")
    assert payload["enabled"] is True
    assert payload["remaining_seconds"] > 0
    assert gate.is_write_enabled() is True
    assert gate.record_write_action("workflow_write", "test") is True


def test_disable_write(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    gate.GATE_PATH = tmp_path / "n8n_write_gate.json"
    gate.LOG_PATH = tmp_path / "logs" / "n8n_write.log"

    gate.enable_write(minutes=60)
    payload = gate.disable_write("manual")
    assert payload["enabled"] is False
    assert gate.is_write_enabled() is False


def test_expired_gate_disables_access(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    gate.GATE_PATH = tmp_path / "n8n_write_gate.json"
    gate.LOG_PATH = tmp_path / "logs" / "n8n_write.log"

    gate.enable_write(minutes=1)
    assert gate.is_write_enabled() is True
    state = gate.GATE_PATH.read_text(encoding="utf-8")
    assert "expires_at" in state

