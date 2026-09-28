#!/usr/bin/env python3
"""Jeff Brain v2 — conversation startup hook. Loads context, checks health, sets tone."""
import sys, json
sys.path.insert(0, '/home/hermes/.hermes')

from brain import check_health, get_budget_left, get_relevant_context, detect_tone

health = check_health()
budget = get_budget_left()
context = get_relevant_context("startup")
tone = detect_tone()

report = {
    "health": health["status"],
    "budget": budget,
    "tone": tone,
    "context_preview": context[:200]
}
print(json.dumps(report, indent=2, ensure_ascii=False))
