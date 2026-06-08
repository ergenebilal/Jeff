import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def test_health_report_has_required_fields(monkeypatch):
    import brain.reporter as reporter

    monkeypatch.setattr(reporter, "_check_services", lambda: {"gateway": True, "embedding": True, "headroom": True, "n8n": False})

    report = reporter.generate_health_report()

    assert "HERMES DURUM RAPORU" in report
    assert "UTC" in report
    assert "Servisler" in report
    assert "Dersler" in report


def test_generate_change_report_returns_none_when_unchanged():
    from brain.reporter import generate_change_report

    state = {"services": {"gateway": True}, "token_usage": 0.1, "decision_count": 2}

    assert generate_change_report(state, dict(state)) is None


def test_generate_change_report_lists_changes():
    from brain.reporter import generate_change_report

    text = generate_change_report(
        {"services": {"gateway": True}, "token_usage": 0.1, "decision_count": 2},
        {"services": {"gateway": False}, "token_usage": 0.2, "decision_count": 4},
    )

    assert "gateway" in text
    assert "Token" in text
    assert "+2 yeni karar" in text


def test_collect_state_shape(monkeypatch):
    import brain.reporter as reporter

    monkeypatch.setattr(reporter, "_check_services", lambda: {"gateway": True})
    state = reporter.collect_state()

    assert "services" in state
    assert "token_usage" in state
    assert "decision_count" in state
    assert "lesson_count" in state


def test_send_report_dry_run_does_not_call_subprocess(monkeypatch):
    import brain.reporter as reporter

    called = []
    monkeypatch.setattr(reporter.subprocess, "run", lambda *a, **kw: called.append((a, kw)))

    result = reporter.send_report("hello", dry_run=True)

    assert result["dry_run"] is True
    assert called == []
