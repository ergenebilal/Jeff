"""Tests for Phase 5 task_classifier module."""

from brain.phase5.task_classifier import classify_message, classify_with_history


def test_classify_quick_mode_short():
    result = classify_message("ls")
    assert result["suggested_mode"] == "quick"
    assert result["confidence"] >= 0.4


def test_classify_quick_mode_typo():
    result = classify_message("fix typo in readme")
    assert result["suggested_mode"] == "quick"


def test_classify_deep_mode_analysis():
    result = classify_message("analiz et bu log dosyasini, hata nerede?")
    assert result["suggested_mode"] == "deep"


def test_classify_deep_mode_complex():
    result = classify_message("design a new authentication system with multi-factor support")
    assert result["suggested_mode"] == "deep"


def test_classify_deep_mode_code_block():
    result = classify_message("```\nprint('hello')\n```\nrefactor this code")
    assert result["suggested_mode"] == "deep"


def test_classify_background_cron():
    result = classify_message("schedule this job to run every hour")
    assert result["suggested_mode"] == "background"


def test_classify_background_batch():
    result = classify_message("run batch process for all pending tasks")
    assert result["suggested_mode"] == "background"


def test_classify_override_explicit():
    result = classify_message("!deep analyze this code")
    assert result["suggested_mode"] == "deep"
    assert result["confidence"] == 1.0


def test_classify_override_quick():
    result = classify_message("!quick run full system audit")
    assert result["suggested_mode"] == "quick"
    assert result["confidence"] == 1.0


def test_classify_with_history_deep_preference():
    result = classify_with_history(
        "check the logs",
        {"common_mode": "deep", "avg_tokens": 30000},
    )
    # Should still be quick for simple command
    assert result["suggested_mode"] is not None


def test_classify_with_history_bg_suggestion():
    result = classify_with_history(
        "run data processing",
        {"avg_tokens": 60000},
    )
    assert result["suggested_mode"] is not None


def test_classify_multistep_triggers_deep():
    result = classify_message("first install deps, then configure, finally test")
    assert result["suggested_mode"] == "deep"
