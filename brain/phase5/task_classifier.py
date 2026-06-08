"""Task classifier: reason about mode selection from user input + run stats.

Uses heuristics and historical run data to suggest the optimal mode
(quick/deep/background) with a confidence score.

Priority chain: user !override > classifier > default (quick)
"""

import re
from typing import Optional

# Complexity indicators
CODE_BLOCK_PATTERN = re.compile(r"```")
MULTI_STEP_PATTERN = re.compile(
    r"(önce|sonra|ardından|first|then|after that|next|adım|step\s*\d)",
    re.IGNORECASE,
)
ANALYSIS_PATTERN = re.compile(
    r"(analiz|et|incele|investigate|audit|forensic|root.cause|why did|neden|sebep|analysis|debug|trace)",
    re.IGNORECASE,
)
PLAN_PATTERN = re.compile(
    r"(plan|tasarım|design|architecture|refactor|yeniden.yap|migrate)",
    re.IGNORECASE,
)
BACKGROUND_PATTERN = re.compile(
    r"(cron|schedule|zamanla|tetikle|trigger|batch|background|arka.plan|job)",
    re.IGNORECASE,
)
QUICK_PATTERN = re.compile(
    r"(hızlı|quick|basit|simple|typo|fix\s+small|ls\s|echo|status|check\s+quick)",
    re.IGNORECASE,
)
CRON_OUTPUT_PATTERN = re.compile(r"cron/output", re.IGNORECASE)

# Confidence thresholds
HIGH_CONFIDENCE = 0.8
MEDIUM_CONFIDENCE = 0.6
LOW_CONFIDENCE = 0.4


def classify_message(message: str) -> dict:
    """Classify a user message into a suggested mode.

    Args:
        message: The raw user input message.

    Returns:
        Dict with suggested_mode, confidence (0-1), and reasons.
    """
    msg_lower = message.lower()
    word_count = len(message.split())
    reasons = []

    # Check for explicit !override (highest priority)
    if message.strip().startswith("!"):
        override = message.strip().split()[0][1:].lower()
        if override in ("quick", "deep", "background"):
            return {
                "suggested_mode": override,
                "confidence": 1.0,
                "scores": {"quick": 0, "deep": 0, "background": 0},
                "reasons": [f"User !override: {override}"],
            }

    # Score each mode
    scores = {"quick": 0, "deep": 0, "background": 0}

    # Background indicators
    if BACKGROUND_PATTERN.search(msg_lower):
        scores["background"] += 3
        reasons.append("background keyword match")
    if CRON_OUTPUT_PATTERN.search(msg_lower):
        scores["background"] += 2
        reasons.append("cron output reference")

    # Deep mode indicators
    if ANALYSIS_PATTERN.search(msg_lower):
        scores["deep"] += 3
        reasons.append("analysis/forensic keyword match")
    if PLAN_PATTERN.search(msg_lower):
        scores["deep"] += 2
        reasons.append("plan/design keyword match")
    if MULTI_STEP_PATTERN.search(msg_lower):
        scores["deep"] += 2
        reasons.append("multi-step instruction detected")
    if word_count > 50:
        scores["deep"] += 2
        reasons.append(f"long message ({word_count} words)")
    if CODE_BLOCK_PATTERN.search(message):
        scores["deep"] += 1
        reasons.append("code block detected")

    # Quick mode indicators
    if QUICK_PATTERN.search(msg_lower):
        scores["quick"] += 2
        reasons.append("quick mode keyword match")
    if word_count <= 10:
        scores["quick"] += 2
        reasons.append(f"short message ({word_count} words)")

    # Default quick for very short
    if word_count <= 3:
        return {
            "suggested_mode": "quick",
            "confidence": HIGH_CONFIDENCE,
            "scores": {"quick": 2, "deep": 0, "background": 0},
            "reasons": ["very short message"],
        }

    # Determine winner (deep wins ties — better to be thorough)
    if scores["deep"] >= scores["quick"] and scores["deep"] >= scores["background"]:
        suggested = "deep"
    elif scores["background"] > scores["quick"] and scores["background"] > scores["deep"]:
        suggested = "background"
    else:
        suggested = "quick"

    # Calculate confidence based on score differential
    total = sum(scores.values()) or 1
    winner_score = scores[suggested]
    ratio = winner_score / total if total > 0 else 0

    if ratio > 0.6:
        confidence = HIGH_CONFIDENCE
    elif ratio > 0.4:
        confidence = MEDIUM_CONFIDENCE
    else:
        confidence = LOW_CONFIDENCE

    return {
        "suggested_mode": suggested,
        "confidence": round(confidence, 2),
        "scores": scores,
        "reasons": reasons,
    }


def classify_with_history(message: str, run_stats: Optional[dict] = None) -> dict:
    """Classify mode using both message content and historical run stats.

    Args:
        message: User input message.
        run_stats: Optional dict with keys like common_mode, avg_tokens, etc.

    Returns:
        Dict with suggested_mode, confidence, reasons.
    """
    result = classify_message(message)

    # If history is available, adjust based on past behavior
    if run_stats:
        common_mode = run_stats.get("common_mode", "")
        avg_tokens = run_stats.get("avg_tokens", 0)

        # If user consistently uses deep mode for similar messages, boost deep
        if common_mode == "deep" and result["confidence"] < HIGH_CONFIDENCE:
            result["scores"]["deep"] = result["scores"].get("deep", 0) + 1
            result["reasons"].append("historical preference for deep mode")

        # If avg token usage suggests background, nudge that way
        if avg_tokens > 50000 and result["suggested_mode"] != "background":
            result["scores"]["background"] = result["scores"].get("background", 0) + 1
            result["reasons"].append("high avg token usage suggests background mode")

    # Recalculate winner after history adjustments (deep wins ties)
    scores = result["scores"]
    if scores["deep"] >= scores["quick"] and scores["deep"] >= scores["background"]:
        result["suggested_mode"] = "deep"
    elif scores["background"] > scores["quick"] and scores["background"] > scores["deep"]:
        result["suggested_mode"] = "background"
    else:
        result["suggested_mode"] = "quick"

    return result
