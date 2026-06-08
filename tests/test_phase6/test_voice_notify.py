"""Tests for Phase 6 Voice Notification module."""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def vn(monkeypatch):
    """Import voice_notify and isolate config path."""
    import brain.phase6.voice_notify as vn
    fake_config = Path(tempfile.mkdtemp()) / "config" / "voice.json"
    fake_config.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(vn, "VOICE_CONFIG", fake_config)
    return vn


def test_voice_config_defaults(vn):
    config = vn.VoiceConfig.load()
    assert config["enabled"] is False
    assert config["voice"] == "tr-TR-EmelNeural"
    assert "quick" in config["allowed_modes"]


def test_voice_config_save_and_load(vn):
    assert vn.VoiceConfig.save({"enabled": True}) is True
    config = vn.VoiceConfig.load()
    assert config["enabled"] is True


def test_voice_config_enable(vn):
    assert vn.VoiceConfig.enable() is True
    assert vn.VoiceConfig.is_enabled() is True


def test_voice_config_disable(vn):
    vn.VoiceConfig.enable()
    assert vn.VoiceConfig.disable() is True
    assert vn.VoiceConfig.is_enabled() is False


def test_voice_notify_disabled_by_default(vn):
    notifier = vn.VoiceNotify()
    result = notifier.notify("test message", mode="quick")
    assert result["success"] is False
    assert "disabled" in result["reason"]


def test_voice_notify_mode_not_allowed(vn):
    vn.VoiceConfig.enable()
    notifier = vn.VoiceNotify()
    result = notifier.notify("test", mode="deep")
    assert result["success"] is False
    assert "not allowed" in result["reason"]


def test_voice_notify_edge_tts_not_installed(vn):
    vn.VoiceConfig.enable()
    notifier = vn.VoiceNotify()

    with patch.object(notifier, "is_available", return_value=False):
        result = notifier.notify("test", mode="quick")
        assert result["success"] is False
        assert "edge-tts not installed" in result["reason"]


def test_voice_notify_edge_tts_success(vn):
    vn.VoiceConfig.enable()
    notifier = vn.VoiceNotify()

    with patch.object(notifier, "is_available", return_value=True):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")

            result = notifier.notify("Merhaba, test bildirimi.", mode="quick")
            assert result["success"] is True
            call_args = mock_run.call_args[0][0]
            assert "edge-tts" in call_args
            assert "--voice" in call_args


def test_voice_notify_notification_types(vn):
    vn.VoiceConfig.enable()
    notifier = vn.VoiceNotify()

    with patch.object(notifier, "is_available", return_value=True):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            result = notifier.notify_critical("Kritik hata!")
            assert result["notification_type"] == "critical"

            result = notifier.notify_reminder("Toplantı var.")
            assert result["notification_type"] == "reminder"


def test_voice_notify_job_notifications(vn):
    vn.VoiceConfig.enable()
    notifier = vn.VoiceNotify()

    with patch.object(notifier, "is_available", return_value=True):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            result = notifier.notify_job_done("Veri analizi")
            assert result["success"] is True
            assert "tamamlandı" in result["message"]

            result = notifier.notify_job_failed("Veri analizi", "timeout")
            assert result["success"] is True
            assert "başarısız" in result["message"]


def test_voice_notify_default_message_from_type(vn):
    vn.VoiceConfig.enable()
    notifier = vn.VoiceNotify()

    with patch.object(notifier, "is_available", return_value=True):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            result = notifier.notify("", notification_type="critical", mode="quick")
            assert result["success"] is True


def test_voice_notify_reload_config(vn):
    notifier = vn.VoiceNotify()
    assert notifier.can_notify("quick") is False

    vn.VoiceConfig.enable()
    notifier.reload_config()
    assert notifier.can_notify("quick") is True


def test_convenience_notify_function(vn):
    vn.VoiceConfig.enable()
    with patch("brain.phase6.voice_notify.VoiceNotify.is_available",
               return_value=True):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stderr="")
            result = vn.notify("test", mode="quick")
            assert "success" in result


def test_voice_config_file_created_on_save(vn):
    vn.VoiceConfig.save({"enabled": False})
    assert vn.VOICE_CONFIG.exists()
    data = json.loads(vn.VOICE_CONFIG.read_text(encoding="utf-8"))
    assert data["enabled"] is False
    assert data["voice"] == "tr-TR-EmelNeural"


def test_is_available_checks_edge_tts(vn):
    notifier = vn.VoiceNotify()
    result = notifier.is_available()
    assert isinstance(result, bool)
