"""Tests for Phase 5 ModeRouter and detect_mode."""

import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))


def test_detect_mode_override_deep():
    from brain.phase5.mode_router import detect_mode

    assert detect_mode("!deep analyze this system") == "deep"


def test_detect_mode_override_quick():
    from brain.phase5.mode_router import detect_mode

    assert detect_mode("!quick run status check") == "quick"


def test_detect_mode_override_background():
    from brain.phase5.mode_router import detect_mode

    assert detect_mode("!background run backup job") == "background"


def test_detect_mode_keyword_deep():
    from brain.phase5.mode_router import detect_mode

    assert detect_mode("We need a deep analysis of the logs") == "deep"


def test_detect_mode_keyword_background():
    from brain.phase5.mode_router import detect_mode

    assert detect_mode("schedule a background cron job") == "background"


def test_detect_mode_short_message_default_quick():
    from brain.phase5.mode_router import detect_mode

    assert detect_mode("hi") == "quick"
    assert detect_mode("ls") == "quick"
    assert detect_mode("status") == "quick"


def test_set_mode_and_get_mode():
    from brain.phase5.mode_router import set_mode, get_mode

    old = get_mode()
    result = set_mode("deep")
    assert result["success"] is True
    assert get_mode() == "deep"
    # Reset
    set_mode(old)


def test_set_mode_invalid():
    from brain.phase5.mode_router import set_mode

    result = set_mode("invalid")
    assert result["success"] is False


def test_mode_router_route_quick():
    from brain.phase5.mode_router import ModeRouter

    router = ModeRouter()
    result = router.route("hello")
    assert result["mode"] == "quick"
    assert result["routed"] is True


def test_mode_router_route_deep():
    from brain.phase5.mode_router import ModeRouter

    router = ModeRouter()
    result = router.route("!deep investigate the outage")
    assert result["mode"] == "deep"
    assert isinstance(result["result"], list)
    assert len(result["result"]) == 4


def test_mode_router_route_background():
    from brain.phase5.mode_router import ModeRouter

    router = ModeRouter()
    result = router.route("!background run report")
    assert result["mode"] == "background"
    assert result["result"]["success"] is True


def test_mode_router_with_executor():
    from brain.phase5.mode_router import ModeRouter

    router = ModeRouter()

    def executor(task):
        return {"output": f"executed: {task}", "status": "ok"}

    result = router.route("!quick test", executor=executor)
    assert result["mode"] == "quick"
    # Quick mode passes the full message to the executor
    assert result["result"]["result"]["output"] == "executed: !quick test"


def test_route_with_override():
    from brain.phase5.mode_router import ModeRouter

    router = ModeRouter()
    result = router.route_with_override("!background sync data")
    assert result["mode"] == "background"
