import json


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
    from pathlib import Path

    html = Path("/opt/hermes/hq/index.html").read_text(encoding="utf-8")

    assert "ERGENEAI KOMUTA MERKEZI" in html
    assert "https://" not in html
    assert "http://" not in html
    assert "#81e36f" in html
