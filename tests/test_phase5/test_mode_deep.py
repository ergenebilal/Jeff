"""Tests for Phase 5 DeepMode."""

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))


def test_deep_mode_init():
    from brain.phase5.mode_deep import DeepMode

    mode = DeepMode()
    assert mode.mode_name == "deep"
    assert mode.context_limit == 60_000
    assert mode.phases == ["discovery", "plan", "execute", "verify"]


def test_deep_mode_context_fit():
    from brain.phase5.mode_deep import DeepMode

    mode = DeepMode()
    result = mode.estimate_context_fit(50_000)
    assert result["within_soft"] is True
    assert result["within_hard"] is True
    assert result["mode"] == "deep"


def test_deep_mode_run_phase_valid():
    from brain.phase5.mode_deep import DeepMode

    mode = DeepMode()
    result = mode.run_phase("discovery", "find root cause")
    assert result["success"] is True
    assert result["phase"] == "discovery"


def test_deep_mode_run_phase_invalid():
    from brain.phase5.mode_deep import DeepMode

    mode = DeepMode()
    result = mode.run_phase("invalid", "task")
    assert result["success"] is False
    assert "error" in result


def test_deep_mode_run_full_sequence():
    from brain.phase5.mode_deep import DeepMode

    mode = DeepMode()
    results = mode.run_full("audit system")
    assert len(results) == 4
    assert results[0]["phase"] == "discovery"
    assert results[1]["phase"] == "plan"
    assert results[2]["phase"] == "execute"
    assert results[3]["phase"] == "verify"


def test_deep_mode_run_full_with_executors():
    from brain.phase5.mode_deep import DeepMode

    mode = DeepMode()

    def discovery(task, ctx):
        return {"output": "discovered", "status": "ok"}

    def plan(task, ctx):
        return {"output": "planned", "status": "ok"}

    executors = {"discovery": discovery, "plan": plan}
    results = mode.run_full("test", phase_executors=executors)
    assert results[0]["result"]["output"] == "discovered"
    assert results[1]["result"]["output"] == "planned"


def test_deep_mode_integrate_runner():
    from brain.phase5.mode_deep import DeepMode

    mode = DeepMode()

    class FakeRunner:
        async def run_task_async(self, task):
            return {"completed": True, "output": "done"}

    result = mode.integrate_with_autonomous_runner(FakeRunner(), "fix bug")
    assert result["completed"] is True
    assert len(result["phases"]) == 4
