"""Voice notification via Edge TTS (optional, quick mode only).

No chatterbox — only critical alerts, reminders, completed background jobs.
"""

import json
import subprocess
from pathlib import Path
from typing import Optional

# Config path
VOICE_CONFIG = Path.home() / ".hermes" / "config" / "voice.json"
VOICE_CONFIG.parent.mkdir(parents=True, exist_ok=True)

# Default voice config
DEFAULT_CONFIG = {
    "enabled": False,           # Opt-in by default
    "voice": "tr-TR-EmelNeural",  # Turkish voice
    "rate": "+0%",
    "volume": "+0%",
    "pitch": "+0Hz",
    "min_interval_sec": 30,    # Min seconds between notifications
    "allowed_modes": ["quick"], # Only quick mode notifications
}


class VoiceConfig:
    """Manage voice notification configuration."""

    @staticmethod
    def load() -> dict:
        """Load voice config from file."""
        if not VOICE_CONFIG.exists():
            return dict(DEFAULT_CONFIG)
        try:
            config = json.loads(VOICE_CONFIG.read_text(encoding="utf-8"))
            # Merge with defaults for any missing keys
            merged = dict(DEFAULT_CONFIG)
            merged.update(config)
            return merged
        except (json.JSONDecodeError, OSError):
            return dict(DEFAULT_CONFIG)

    @staticmethod
    def save(config: dict) -> bool:
        """Save voice config to file."""
        try:
            merged = dict(DEFAULT_CONFIG)
            merged.update(config)
            VOICE_CONFIG.write_text(
                json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            return True
        except OSError:
            return False

    @staticmethod
    def enable():
        """Enable voice notifications."""
        config = VoiceConfig.load()
        config["enabled"] = True
        return VoiceConfig.save(config)

    @staticmethod
    def disable():
        """Disable voice notifications."""
        config = VoiceConfig.load()
        config["enabled"] = False
        return VoiceConfig.save(config)

    @staticmethod
    def is_enabled() -> bool:
        """Check if voice notifications are enabled."""
        return VoiceConfig.load().get("enabled", False)


class VoiceNotify:
    """Send voice notifications via Edge TTS.

    Only for critical alerts, reminders, and completed background jobs.
    No chatterbox — keeps notifications minimal and useful.
    """

    NOTIFICATION_TYPES = {
        "critical": "Uyarı: Kritik bir durum tespit edildi.",
        "reminder": "Hatırlatıcı: Bir görev hatırlatması var.",
        "job_done": "Background görevi tamamlandı.",
        "job_failed": "Background görevi başarısız oldu.",
    }

    def __init__(self, config: Optional[dict] = None):
        self.config = config or VoiceConfig.load()

    def reload_config(self):
        """Reload config from file."""
        self.config = VoiceConfig.load()

    def is_available(self) -> bool:
        """Check if edge-tts is installed."""
        try:
            result = subprocess.run(
                ["edge-tts", "--help"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def can_notify(self, mode: str = "quick") -> bool:
        """Check if notification is allowed based on config and mode."""
        if not self.config.get("enabled", False):
            return False
        allowed_modes = self.config.get("allowed_modes", ["quick"])
        if mode not in allowed_modes:
            return False
        return True

    def notify(self, message: str, notification_type: str = "job_done",
               mode: str = "quick") -> dict:
        """Send a voice notification.

        Args:
            message: The text to speak.
            notification_type: Type of notification (critical, reminder, job_done, job_failed).
            mode: The current mode (only quick mode allowed by default).

        Returns:
            Dict with success status and details.
        """
        if not self.can_notify(mode):
            return {
                "success": False,
                "reason": "Voice notifications disabled or mode not allowed",
                "notification_type": notification_type,
            }

        if not self.is_available():
            return {
                "success": False,
                "reason": "edge-tts not installed. Run: pip install edge-tts",
                "notification_type": notification_type,
            }

        # Use template if no custom message
        if not message:
            message = self.NOTIFICATION_TYPES.get(
                notification_type, "Bildirim."
            )

        try:
            result = subprocess.run(
                [
                    "edge-tts",
                    "--voice", self.config.get("voice", "tr-TR-EmelNeural"),
                    "--rate", self.config.get("rate", "+0%"),
                    "--volume", self.config.get("volume", "+0%"),
                    "--pitch", self.config.get("pitch", "+0Hz"),
                    "--text", message,
                ],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stderr": result.stderr,
                "notification_type": notification_type,
                "message": message,
            }
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            return {
                "success": False,
                "reason": str(e),
                "notification_type": notification_type,
            }

    def notify_critical(self, message: str, mode: str = "quick") -> dict:
        """Send a critical alert notification."""
        return self.notify(message, notification_type="critical", mode=mode)

    def notify_reminder(self, message: str, mode: str = "quick") -> dict:
        """Send a reminder notification."""
        return self.notify(message, notification_type="reminder", mode=mode)

    def notify_job_done(self, job_name: str, mode: str = "quick") -> dict:
        """Notify that a background job completed."""
        message = f"{job_name} görevi tamamlandı."
        return self.notify(message, notification_type="job_done", mode=mode)

    def notify_job_failed(self, job_name: str, error: str = "",
                          mode: str = "quick") -> dict:
        """Notify that a background job failed."""
        message = f"{job_name} görevi başarısız oldu."
        if error:
            message += f" Hata: {error}"
        return self.notify(message, notification_type="job_failed", mode=mode)


# ── Convenience function ───────────────────────────────────────────────────

def notify(message: str, notification_type: str = "job_done",
           mode: str = "quick") -> dict:
    """Quick one-shot notification using default config."""
    notifier = VoiceNotify()
    return notifier.notify(message, notification_type, mode)
