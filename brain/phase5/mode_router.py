"""Mode router: auto-detect mode from message with task classifier.

Priority:
1. User !override (e.g., !deep)
2. Manual override via set_mode()
3. Task classifier (heuristic + optional run stats)
4. Default: quick
"""

import re
from typing import Optional
from brain.phase5.task_classifier import classify_message

# Override command patterns
OVERRIDE_PATTERN = re.compile(r"^!(quick|deep|background)\b", re.IGNORECASE)

# Keywords that trigger each mode
QUICK_KEYWORDS = ["hızlı", "quick", "basit", "simple", "küçük", "small", "fix",
                  "typo", "imla", "ls", "echo", "status", "check"]
DEEP_KEYWORDS = ["deep", "derin", "analiz", "analysis", "forensic", "audit",
                 "investigate", "soruştur", "patch", "karmaşık", "complex",
                 "planla", "plan", "tasarım", "design", "refactor"]
BACKGROUND_KEYWORDS = ["background", "arkaplan", "cron", "schedule", "zamanla",
                       "tetikle", "trigger", "job", "task", "batch", "toplu"]

# Currently active mode (can be overridden)
_active_mode = "auto"  # auto | quick | deep | background


def set_mode(mode: str) -> dict:
    """Manually override mode. Use 'auto' for automatic detection."""
    global _active_mode
    valid_modes = {"auto", "quick", "deep", "background"}
    if mode not in valid_modes:
        return {"error": f"Invalid mode: {mode}. Valid: {valid_modes}", "success": False}
    _active_mode = mode
    return {"mode": mode, "success": True}


def get_mode() -> str:
    """Get the currently active mode setting."""
    return _active_mode


def detect_mode(message: str, run_stats: Optional[dict] = None) -> str:
    """Detect the appropriate mode from a user message.

    Priority:
    1. !override command (e.g., !deep)
    2. Manual override via set_mode()
    3. Task classifier with heuristic + optional run stats
    4. Default: quick

    Args:
        message: User input message.
        run_stats: Optional historical run statistics for better classification.

    Returns: "quick", "deep", or "background"
    """
    # Check for override command in message
    override_match = OVERRIDE_PATTERN.match(message.strip())
    if override_match:
        return override_match.group(1).lower()

    # Check manual override
    if _active_mode != "auto":
        return _active_mode

    # Use task classifier
    if run_stats:
        from brain.phase5.task_classifier import classify_with_history
        result = classify_with_history(message, run_stats)
    else:
        result = classify_message(message)

    return result["suggested_mode"]


class ModeRouter:
    """Route tasks to the appropriate mode executor."""

    def __init__(self, quick=None, deep=None, background=None):
        from .mode_quick import QuickMode
        from .mode_deep import DeepMode
        from .mode_background import BackgroundMode

        self.quick_mode = quick or QuickMode()
        self.deep_mode = deep or DeepMode()
        self.background_mode = background or BackgroundMode()

    def route(self, message: str, executor=None) -> dict:
        """Detect mode and execute the message in that mode.

        Args:
            message: User input message.
            executor: Optional callable for execution.

        Returns:
            Dict with mode, result, and metadata.
        """
        mode = detect_mode(message)

        if mode == "deep":
            result = self.deep_mode.run_full(message)
        elif mode == "background":
            import uuid
            job_id = str(uuid.uuid4())[:8]
            result = self.background_mode.run_job(job_id, message, executor)
        else:
            result = self.quick_mode.run(message, executor)

        return {
            "mode": mode,
            "message": message,
            "result": result,
            "routed": True,
        }

    def route_with_override(self, message: str, executor=None) -> dict:
        """Route with !quick, !deep, !background override support."""
        return self.route(message, executor)
