"""Self-improvement advisor: reads lessons + logs, produces patch plans.

Analyzes:
  - lessons.jsonl for recurring failure patterns
  - skills logs for low-performing skills
  - token reports for expensive patterns
  - eval scores for weak categories

Outputs structured patch plans (files/prompts/policies to change).
"""

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from brain.learning import LESSONS_FILE, get_lessons_summary, get_recent_lessons

SKILLS_LOG = Path.home() / ".hermes" / "logs" / "skills.jsonl"


def _read_jsonl(path: Path) -> list:
    if not path.exists():
        return []
    entries = []
    try:
        for line in path.read_text(encoding="utf-8").strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except OSError:
        pass
    return entries


def analyze_lessons() -> dict:
    """Analyze lessons for recurring patterns."""
    lessons = get_recent_lessons(limit=100)
    if not lessons:
        return {"patterns": [], "total_lessons": 0}

    category_counts = Counter(l.get("category", "unknown") for l in lessons)
    top_categories = [{"category": cat, "count": cnt}
                      for cat, cnt in category_counts.most_common(5)]

    return {
        "total_lessons": len(lessons),
        "top_categories": top_categories,
    }


def analyze_skills() -> dict:
    """Analyze skills for low performers and gaps."""
    entries = _read_jsonl(SKILLS_LOG)
    if not entries:
        return {"weak_skills": [], "total": 0}

    skill_success = defaultdict(lambda: {"total": 0, "fail": 0})
    for e in entries:
        name = e.get("name", "unknown")
        skill_success[name]["total"] += 1
        if e.get("stage") in ("error", "failed"):
            skill_success[name]["fail"] += 1

    weak_skills = []
    for name, stats in skill_success.items():
        if stats["total"] >= 3:
            fail_rate = stats["fail"] / stats["total"]
            if fail_rate > 0.5:
                weak_skills.append({
                    "skill": name,
                    "fail_rate": round(fail_rate, 2),
                    "total_runs": stats["total"],
                })

    return {"weak_skills": weak_skills, "total": len(skill_success)}


def generate_patch_plan() -> dict:
    """Generate a structured patch plan based on analysis.

    Returns dict with:
      - summary: high-level findings
      - patches: list of suggested patches (file/target + change)
      - priority: high/medium/low
    """
    lesson_analysis = analyze_lessons()
    skill_analysis = analyze_skills()

    patches = []
    priority = "low"

    # Generate patches from lesson patterns
    for cat in lesson_analysis.get("top_categories", []):
        if cat["count"] >= 3:
            patches.append({
                "target": f"category:{cat['category']}",
                "issue": f"{cat['count']} lesson entries in {cat['category']}",
                "suggested_action": f"Review and update handling for {cat['category']} failures",
                "patch_type": "prompt",
            })
            priority = "medium"

    # Generate patches from weak skills
    for ws in skill_analysis.get("weak_skills", []):
        patches.append({
            "target": f"skill:{ws['skill']}",
            "issue": f"High failure rate ({ws['fail_rate']:.0%}) in {ws['skill']}",
            "suggested_action": f"Review skill implementation or deprecate {ws['skill']}",
            "patch_type": "skill",
        })
        priority = "high"

    if not patches:
        patches.append({
            "target": "general",
            "issue": "No significant issues detected",
            "suggested_action": "Continue monitoring",
            "patch_type": "info",
        })

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_lessons": lesson_analysis.get("total_lessons", 0),
            "weak_skills": len(skill_analysis.get("weak_skills", [])),
            "patches_proposed": len(patches),
        },
        "patches": patches,
        "priority": priority,
    }
