"""Mode router: auto-detect mode from message, support !override commands."""

import re
from typing import Optional

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


def detect_mode(message: str) -> str:
    """Detect the appropriate mode from a user message.

    Priority:
    1. !override command (e.g., !deep)
    2. Manual override via set_mode()
    3. Keyword-based detection

    Returns: "quick", "deep", or "background"
    """
    # Check for override command in message
    override_match = OVERRIDE_PATTERN.match(message.strip())
    if override_match:
        return override_match.group(1).lower()

    # Check manual override
    if _active_mode != "auto":
        return _active_mode

    # Keyword-based detection
    msg_lower = message.lower()

    # Count keyword matches for each mode
    quick_score = sum(1 for kw in QUICK_KEYWORDS if kw in msg_lower)
    deep_score = sum(1 for kw in DEEP_KEYWORDS if kw in msg_lower)
    bg_score = sum(1 for kw in BACKGROUND_KEYWORDS if kw in msg_lower)

    # Decision logic
    if deep_score > quick_score and deep_score >= bg_score:
        return "deep"
    if bg_score > quick_score and bg_score > deep_score:
        return "background"

    # Default to quick for short messages, deep for long ones
    if len(message.split()) <= 10:
        return "quick"

    return "quick"  # safe default


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
