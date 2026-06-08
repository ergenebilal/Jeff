"""Tone adaptation for Hermes responses."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


TONES = {
    "keskin": {"description": "Night/early morning — short and direct", "style": "short_and_direct"},
    "enerjik": {"description": "Morning — motivated and positive", "style": "detailed_and_positive"},
    "analitik": {"description": "Work hours — data driven and focused", "style": "analytic_and_focused"},
    "rahat": {"description": "Evening — warm and conversational", "style": "casual_and_warm"},
    "koruyucu": {"description": "Critical state — protective and alert", "style": "protective_and_alert"},
}


def detect_tone(now: Optional[datetime] = None) -> str:
    """Select a tone from critical state and UTC hour."""
    if _is_critical():
        return "koruyucu"
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    hour = current.astimezone(timezone.utc).hour
    if 0 <= hour < 6:
        return "keskin"
    if 6 <= hour < 12:
        return "enerjik"
    if 12 <= hour < 18:
        return "analitik"
    return "rahat"


def get_style_guide(tone: Optional[str] = None) -> dict:
    """Return the style guide for a tone."""
    selected = tone or detect_tone()
    return TONES.get(selected, TONES["rahat"])


def format_by_tone(message: str, tone: Optional[str] = None) -> str:
    """Apply a small deterministic formatting rule for the selected tone."""
    selected = tone or detect_tone()
    text = str(message)
    if selected == "keskin":
        return text[:150] + "..." if len(text) > 150 else text
    if selected == "koruyucu":
        return f"⚠️ {text[:200]}"
    return text


def _is_critical() -> bool:
    """Return True when local state suggests a protective tone."""
    try:
        from brain.token import TokenGuard

        guard = TokenGuard.check()
        if guard.get("status") in {"stop", "flash"}:
            return True
    except Exception:
        pass

    try:
        state_path = Path.home() / ".hermes" / "agent_state.json"
        if state_path.exists():
            data = json.loads(state_path.read_text(encoding="utf-8"))
            if data.get("last_gateway_check") == "dead":
                return True
    except Exception:
        pass
    return False


def get_tone_context() -> str:
    """Return a compact prompt-safe tone context line."""
    tone = detect_tone()
    style = get_style_guide(tone)
    return f"Ton: {tone} | style={style.get('style')} | {style.get('description')}"
