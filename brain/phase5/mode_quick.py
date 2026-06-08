"""Quick mode: low-latency, core-only tool set, short context (20K token)."""

from typing import Any

# Quick mode token limits
SOFT_LIMIT = 20_000
HARD_LIMIT = 40_000

# Core-only tool set allowed in quick mode
CORE_TOOLS = {"bash", "read", "write", "edit", "glob", "grep", "web_search", "web_fetch"}


class QuickMode:
    """Quick mode executor — minimal overhead for small maintenance tasks."""

    def __init__(self, context_limit: int = SOFT_LIMIT):
        self.context_limit = context_limit
        self.mode_name = "quick"

    def check_tool_allowed(self, tool_name: str) -> bool:
        """Check if a tool is allowed in quick mode."""
        return tool_name in CORE_TOOLS

    def get_allowed_tools(self) -> set:
        """Return the set of tools allowed in quick mode."""
        return CORE_TOOLS.copy()

    def estimate_context_fit(self, current_tokens: int) -> dict:
        """Check if current context fits within quick mode limits."""
        return {
            "mode": "quick",
            "current": current_tokens,
            "soft_limit": SOFT_LIMIT,
            "hard_limit": HARD_LIMIT,
            "within_soft": current_tokens <= SOFT_LIMIT,
            "within_hard": current_tokens <= HARD_LIMIT,
        }

    def run(self, task: str, executor: Any = None) -> dict:
        """Execute a task in quick mode.

        Args:
            task: The task description or input.
            executor: Optional callable to execute the task.

        Returns:
            Dict with task result and mode metadata.
        """
        if executor:
            result = executor(task)
        else:
            result = {"output": f"Quick mode processed: {task[:100]}", "status": "ok"}

        return {
            "mode": "quick",
            "task": task,
            "result": result,
            "context_limit": self.context_limit,
        }
