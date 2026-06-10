"""Lesson miner: extract lessons from eval results + forensics.

Feeds lessons.jsonl with structured entries from:
  - eval_daily.jsonl (failed/passing scenarios)
  - agent_runs.jsonl (failure patterns)
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from brain.learning import LESSONS_FILE, save_lesson

EVAL_DAILY_LOG = Path.home() / ".hermes" / "logs" / "eval_daily.jsonl"
AGENT_RUNS_LOG = Path.home() / ".hermes" / "logs" / "agent_runs.jsonl"


def _read_jsonl(path: Path) -> list:
    """Read a JSONL file, returning list of dicts."""
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


def mine_from_eval() -> int:
    """Extract lessons from failed eval scenarios."""
    entries = _read_jsonl(EVAL_DAILY_LOG)
    count = 0
    for entry in entries:
        if entry.get("success"):
            continue
        category = entry.get("category", "unknown")
        error = entry.get("error", "No details")
        save_lesson(
            category="eval_" + category,
            trigger=f"eval_{category}_failure",
            lesson=f"Eval senaryo basarisiz: {category}. Hata: {error}",
            importance=0.7,
            source="lesson_miner_eval",
        )
        count += 1
    return count


def mine_from_runs() -> int:
    """Extract lessons from failed agent runs."""
    entries = _read_jsonl(AGENT_RUNS_LOG)
    count = 0
    seen_errors = set()
    for entry in entries:
        error = entry.get("error")
        if not error:
            continue
        # Deduplicate similar errors
        error_key = error[:100]
        if error_key in seen_errors:
            continue
        seen_errors.add(error_key)

        source = entry.get("source", "terminal")
        save_lesson(
            category="run_error",
            trigger=f"error_in_{source}",
            lesson=f"Run hatasi ({source}): {error[:200]}",
            importance=0.6,
            source="lesson_miner_runs",
        )
        count += 1
    return count


def run_full_mine() -> dict:
    """Run both miners and return summary."""
    eval_count = mine_from_eval()
    run_count = mine_from_runs()
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "eval_lessons": eval_count,
        "run_lessons": run_count,
        "total": eval_count + run_count,
    }
