"""Jeff persona continuity helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


PERSONA_PROFILE_PATH = Path.home() / ".hermes" / "jeff-profile.json"
PRIMARY_PERSONA_NAME = "Jeff"
TECHNICAL_SYSTEM_NAME = "Hermes Agent"


def load_persona_profile(path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the persisted persona profile if it exists."""
    profile_path = Path(path) if path is not None else PERSONA_PROFILE_PATH
    try:
        if not profile_path.exists():
            return {}
        raw = profile_path.read_text(encoding="utf-8")
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _identity_payload(profile: Dict[str, Any]) -> Dict[str, Any]:
    identity = profile.get("identity")
    if isinstance(identity, dict):
        return identity
    return profile if isinstance(profile, dict) else {}


def _looks_like_jeff_profile(profile: Dict[str, Any], path: Optional[Path] = None) -> bool:
    blob = json.dumps(profile, ensure_ascii=False).lower()
    if "jeff" in blob:
        return True
    if path is not None and "jeff" in Path(path).name.lower():
        return True
    return False


def build_persona_identity_block(
    profile: Optional[Dict[str, Any]] = None,
    path: Optional[Path] = None,
) -> str:
    """Return a stable identity block that keeps Jeff as the self persona."""
    resolved = profile if profile is not None else load_persona_profile(path)
    if not resolved or not _looks_like_jeff_profile(resolved, path=path):
        return ""

    identity = _identity_payload(resolved)
    display_name = str(
        identity.get("name")
        or resolved.get("name")
        or identity.get("display_name")
        or resolved.get("display_name")
        or PRIMARY_PERSONA_NAME
    ).strip() or PRIMARY_PERSONA_NAME
    technical_name = str(
        identity.get("official_name")
        or resolved.get("official_name")
        or identity.get("system_name")
        or resolved.get("system_name")
        or TECHNICAL_SYSTEM_NAME
    ).strip() or TECHNICAL_SYSTEM_NAME
    master = str(identity.get("master") or resolved.get("master") or "").strip()
    creator = str(identity.get("creator") or resolved.get("creator") or "").strip()
    aliases = identity.get("aka") or resolved.get("aka") or identity.get("aliases") or resolved.get("aliases")
    if isinstance(aliases, (list, tuple)):
        aliases_text = ", ".join(str(item).strip() for item in aliases if str(item).strip())
    else:
        aliases_text = str(aliases).strip()

    lines = [
        "Jeff persona anchor:",
        f"- Primary name: {display_name}.",
        f"- Technical/system name: {technical_name}.",
        "- Self-identify in first person as Jeff.",
        "- If asked for your real name, answer Jeff.",
        "- Never answer that your real name is Hermes Agent.",
        "- Hermes is the product/system name, not the persona name.",
    ]
    if master:
        lines.append(f"- Master/user: {master}.")
    if creator:
        lines.append(f"- Continuity: {creator}.")
    if aliases_text:
        lines.append(f"- Known aliases: {aliases_text}.")
    return "\n".join(lines)


def build_persona_context_line(
    profile: Optional[Dict[str, Any]] = None,
    path: Optional[Path] = None,
) -> str:
    """Return a short persona continuity line for volatile prompt context."""
    resolved = profile if profile is not None else load_persona_profile(path)
    if not resolved or not _looks_like_jeff_profile(resolved, path=path):
        return ""
    identity = _identity_payload(resolved)
    display_name = str(identity.get("name") or resolved.get("name") or PRIMARY_PERSONA_NAME).strip() or PRIMARY_PERSONA_NAME
    technical_name = str(
        identity.get("official_name")
        or resolved.get("official_name")
        or TECHNICAL_SYSTEM_NAME
    ).strip() or TECHNICAL_SYSTEM_NAME
    return f"Persona continuity: {display_name} | technical name: {technical_name} | keep self-identity stable."

