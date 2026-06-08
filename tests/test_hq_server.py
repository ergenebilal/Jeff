import json
import platform

import pytest


def test_hq_api_handler_status_shape():
    from hq.server import HQAPIHandler

    status = HQAPIHandler._build_full_status()

    assert "timestamp" in status
    assert "health" in status
    assert "tokens" in status
    assert "decisions" in status
    assert isinstance(status["decisions"], list)


def test_hq_health_does_not_expose_secrets():
    from hq.server import HQAPIHandler

    payload = json.dumps(HQAPIHandler._build_full_status(), ensure_ascii=False)

    forbidden = ["DEEPSEEK_API_KEY", "GROQ_API_KEY", "OPENROUTER", "sk-", "gsk_"]
    assert not any(item in payload for item in forbidden)


def test_hq_index_is_self_contained():
    from brain.environment import Environment

    env = Environment()
    html = env.resolve_abs("/opt/hermes/hq/index.html").read_text(encoding="utf-8")

    assert "ERGENEAI KOMUTA MERKEZI" in html
    assert "https://" not in html
    assert "http://" not in html
    assert "#81e36f" in html


def test_hq_command_rejects_disallowed_command():
    from hq.server import _run_allowed_command

    result, status = _run_allowed_command("rm -rf /")

    assert status == 403
    assert result["error"] == "Bu komuta izin verilmiyor"



def test_hq_command_allows_safe_uptime():
    from hq.server import _run_allowed_command

    if platform.system().lower() == "windows":
        pytest.skip("uptime is a Linux-only command")

    result, status = _run_allowed_command("uptime")

    assert status == 200
    assert result["command"] == "uptime"
    assert "exit_code" in result


def test_hq_token_limit_actions():
    from hq.server import _handle_token_limit

    reset, reset_status = _handle_token_limit({"action": "reset"})
    set_payload, set_status = _handle_token_limit({"action": "set", "limit": 0.75})
    bad, bad_status = _handle_token_limit({"action": "bad"})

    assert reset_status == 200
    assert reset["status"] == "reset_requested"
    assert set_status == 200
    assert set_payload["new_limit"] == 0.75
    assert bad_status == 400


def test_hq_index_has_interactive_controls():
    from brain.environment import Environment

    env = Environment()
    html = env.resolve_abs("/opt/hermes/hq/index.html").read_text(encoding="utf-8")

    assert "restartService" in html
    assert "resetTokenLimit" in html
    assert "commandBox" in html
    assert "btn-small" in html
