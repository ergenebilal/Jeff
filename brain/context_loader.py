"""Conversation-start context loader for Hermes."""

from .clock_keeper import TimeSyncGuard, utc_now
from .learning import get_lessons_summary
from . import retrieval


def get_relevant_context(topic: str = "") -> str:
    """Return compact context Hermes should review before a new conversation."""
    parts = []
    try:
        clock = TimeSyncGuard().check()
        status = "synced" if clock.get("synced") else "ok"
        drift = clock.get("drift_ms")
        drift_text = "missing" if drift is None else f"{float(drift):.3f}ms"
        parts.append(f"⏱️ Clock Keeper: {status} | drift={drift_text} | UTC {clock.get('server_utc')}")
    except Exception:
        parts.append(f"⏱️ Clock Keeper: unavailable | UTC {utc_now().isoformat().replace('+00:00', 'Z')}")

    lessons = get_lessons_summary(10)
    parts.append("📚 Öğrendiklerim:\n" + lessons)

    parts.append(f"🕐 UTC {utc_now().isoformat().replace('+00:00', 'Z')}")

    try:
        from .reasoning_tree import summarize as tree_summary

        parts.append("🧠 " + tree_summary())
    except Exception:
        pass

    try:
        from .mood import get_tone_context

        parts.append("🎚️ " + get_tone_context())
    except Exception:
        pass

    try:
        from .advisors import assess_proposal, format_assessment

        assessment = assess_proposal(topic or "conversation_start", topic or "conversation_start")
        parts.append("🧭 Öneri disiplini:\n" + format_assessment(assessment))
    except Exception:
        pass

    try:
        snapshot = retrieval.build_retrieval_layers(topic or "", limit=5)
        parts.append("🔎 L1-L4 Retrieval:\n" + retrieval.format_retrieval_layers(snapshot))
    except Exception:
        pass

    if topic:
        parts.append(f"🎯 Konu: {topic}")
    return "\n\n".join(parts)


if __name__ == "__main__":
    print(get_relevant_context())
