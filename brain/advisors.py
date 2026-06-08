"""Proposal advisor: inspect past decisions and lessons before recommending."""

import json
from pathlib import Path


STATE_PATH = Path.home() / ".hermes" / "agent_state.json"
LESSONS_PATH = Path.home() / ".hermes" / "learning" / "lessons.jsonl"


def _load_decisions(limit: int = 20) -> list:
    if not STATE_PATH.exists():
        return []
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        items = data.get("reasoning_tree", [])
        return items[-int(limit) :] if isinstance(items, list) else []
    except Exception:
        return []


def _load_lessons(limit: int = 20) -> list:
    if not LESSONS_PATH.exists():
        return []
    lessons = []
    try:
        with LESSONS_PATH.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                if isinstance(entry, dict):
                    lessons.append(entry)
    except Exception:
        return []
    return lessons[-int(limit) :]


def assess_proposal(proposal: str, task: str = "") -> dict:
    """Assess a proposal against reasoning-tree decisions and learned lessons."""
    decisions = _load_decisions(20)
    lessons = _load_lessons(20)
    proposal_lower = str(proposal).lower()
    task_lower = str(task).lower()

    similar = []
    for decision in decisions:
        haystack = f"{decision.get('command', '')} {decision.get('task', '')}".lower()
        match = _similarity(f"{proposal_lower} {task_lower}", haystack)
        if match > 0.3:
            similar.append({"decision": decision, "match": match})
    similar.sort(key=lambda item: item["match"], reverse=True)

    relevant_lessons = []
    for lesson in lessons:
        haystack = f"{lesson.get('trigger', '')} {lesson.get('lesson', '')}".lower()
        match = _similarity(f"{task_lower} {proposal_lower}", haystack)
        if match >= 0.25:
            relevant_lessons.append({"lesson": lesson, "match": match})
    relevant_lessons.sort(key=lambda item: item["match"], reverse=True)

    if similar:
        success_count = sum(1 for item in similar if item["decision"].get("outcome") == "success")
        success_rate = success_count / len(similar)
    else:
        success_rate = 0.5

    warning = None
    failures = total_similar_with_failure(similar)
    if success_rate < 0.4:
        warning = f"Dikkat: benzer geçmiş kararlarda başarı oranı %{success_rate * 100:.0f}. Alternatif değerlendir."
    elif failures and len(similar) > 2:
        warning = "Geçmişte benzer görevlerde başarısızlık var, dikkatli ol."

    suggestion_parts = []
    if similar:
        best = similar[0]["decision"]
        suggestion_parts.append(
            f"Geçmişte '{best.get('command', '?')[:40]}...' görevinde sonuç: {best.get('outcome', 'bilinmiyor')}"
        )
    if relevant_lessons:
        best_lesson = relevant_lessons[0]["lesson"]
        suggestion_parts.append(f"Öğrenilen ders: {best_lesson.get('lesson', '?')[:120]}")

    return {
        "similar_count": len(similar),
        "success_rate": round(success_rate, 2),
        "warning": warning,
        "suggestion": " | ".join(suggestion_parts) if suggestion_parts else None,
    }


def _similarity(a: str, b: str) -> float:
    words_a = set(str(a).split())
    words_b = set(str(b).split())
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def total_similar_with_failure(similar: list) -> int:
    return sum(1 for item in similar if item.get("decision", {}).get("outcome") == "failed")


def format_assessment(assessment: dict) -> str:
    parts = [
        f"📊 Geçmişte {assessment.get('similar_count', 0)} benzer karar",
        f"✅ Başarı oranı: %{float(assessment.get('success_rate', 0.0)) * 100:.0f}",
    ]
    if assessment.get("warning"):
        parts.append(f"⚠️ {assessment['warning']}")
    if assessment.get("suggestion"):
        parts.append(f"💡 {assessment['suggestion']}")
    return "\n".join(parts)
