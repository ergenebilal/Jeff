"""Deterministic tone helpers for Jeff/Hermes responses."""

from __future__ import annotations

from datetime import datetime, timezone

TONES = {
    "analytic_and_focused": {"style": "net, teknik, odakli"},
    "casual_and_warm": {"style": "sicak, kisa, dogal"},
    "protective_and_alert": {"style": "koruyucu, risk odakli"},
}


def detect_tone(now: datetime | None = None) -> str:
    current = now or datetime.now(timezone.utc)
    hour = current.astimezone(timezone.utc).hour
    if 6 <= hour < 18:
        return "analytic_and_focused"
    return "casual_and_warm"


def get_style_guide(tone: str | None = None) -> dict[str, str]:
    return TONES.get(tone or detect_tone(), TONES["analytic_and_focused"])


def format_by_tone(message: str, tone: str | None = None) -> str:
    return str(message)


def get_tone_context() -> str:
    tone = detect_tone()
    return f"Ton: {tone} | style={get_style_guide(tone).get('style')}"
