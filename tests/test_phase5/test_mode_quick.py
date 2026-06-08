"""Tests for Phase 5 QuickMode."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))


def test_quick_mode_init():
    from brain.phase5.mode_quick import QuickMode

    mode = QuickMode()
    assert mode.mode_name == "quick"
    assert mode.context_limit == 20_000


def test_quick_mode_core_tools():
    from brain.phase5.mode_quick import QuickMode

    mode = QuickMode()
    assert mode.check_tool_allowed("bash") is True
    assert mode.check_tool_allowed("read") is True
    assert mode.check_tool_allowed("write") is True
    assert mode.check_tool_allowed("edit") is True


def test_quick_mode_tool_not_allowed():
    from brain.phase5.mode_quick import QuickMode

    mode = QuickMode()
    assert mode.check_tool_allowed("some_unknown_tool") is False


def test_quick_mode_get_allowed_tools():
    from brain.phase5.mode_quick import QuickMode, CORE_TOOLS

    mode = QuickMode()
    allowed = mode.get_allowed_tools()
    assert allowed == CORE_TOOLS


def test_quick_mode_context_fit_within():
    from brain.phase5.mode_quick import QuickMode

    mode = QuickMode()
    result = mode.estimate_context_fit(5_000)
    assert result["within_soft"] is True
    assert result["within_hard"] is True


def test_quick_mode_context_fit_exceed_soft():
    from brain.phase5.mode_quick import QuickMode

    mode = QuickMode()
    result = mode.estimate_context_fit(25_000)
    assert result["within_soft"] is False
    assert result["within_hard"] is True


def test_quick_mode_run_default():
    from brain.phase5.mode_quick import QuickMode

    mode = QuickMode()
    result = mode.run("test task")
    assert result["mode"] == "quick"
    assert "test task" in result["task"]


def test_quick_mode_run_with_executor():
    from brain.phase5.mode_quick import QuickMode

    mode = QuickMode()

    def executor(task):
        return {"output": f"executed: {task}", "status": "done"}

    result = mode.run("my task", executor=executor)
    assert result["result"]["output"] == "executed: my task"
