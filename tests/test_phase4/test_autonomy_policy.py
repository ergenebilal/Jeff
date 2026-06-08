"""Tests for Phase 4 autonomy_policy module."""

from brain.phase4.autonomy_policy import (
    ACTION_RISK,
    RISK_LEVELS,
    evaluate_action,
    format_ask_message,
    get_risk_level,
    self_audit,
)


def test_get_risk_level_read():
    assert get_risk_level("read_file") == "read"


def test_get_risk_level_write():
    assert get_risk_level("write_file") == "write"


def test_get_risk_level_destructive():
    assert get_risk_level("delete_file") == "destructive"


def test_get_risk_level_unknown_defaults_to_ask():
    assert get_risk_level("unknown_action") == "ask"


def test_evaluate_action_allow():
    result = evaluate_action("read_file", resource="/tmp/test.txt")

    assert result["policy_decision"] == "allow"
    assert result["action_type"] == "read_file"
    assert result["resource"] == "/tmp/test.txt"


def test_evaluate_action_ask():
    result = evaluate_action("edit_config", resource="~/.hermes/config.yaml")

    assert result["policy_decision"] == "ask"


def test_evaluate_action_deny():
    result = evaluate_action("delete_file", resource="/opt/hermes/data")

    assert result["policy_decision"] == "deny"


def test_evaluate_action_with_context():
    result = evaluate_action("write_file", resource="/tmp/test.txt",
                             context={"user_message": "update config"})

    assert result["context"]["user_message"] == "update config"


def test_self_audit_returns_structure():
    result = self_audit()
    assert "total_decisions" in result
    assert "timestamp" in result


def test_format_ask_message():
    evaluation = evaluate_action("edit_config", resource="config.yaml")
    msg = format_ask_message(evaluation)

    assert "edit_config" in msg
    assert "config.yaml" in msg
    assert "Seçenekler" in msg
    assert "1." in msg


def test_all_risk_levels_have_labels():
    for level, info in RISK_LEVELS.items():
        assert "label" in info
        assert "default" in info
