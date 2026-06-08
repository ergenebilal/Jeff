def test_token_filter_levels_and_compression():
    from brain.token import compress_message, estimate_tokens, set_log_level, should_log

    set_log_level("normal")
    assert should_log("critical") is True
    assert should_log("normal") is True
    assert should_log("verbose") is False

    long_text = "A" * 1200
    compressed = compress_message(long_text, max_tokens=500)
    assert "compressed" in compressed
    assert len(compressed) < len(long_text)
    assert estimate_tokens("12345678") == 2


def test_token_guard_check_is_safe(monkeypatch):
    from brain.token import TokenGuard

    result = TokenGuard.check()

    assert result["status"] in {"ok", "warn", "flash", "stop"}
    assert "budget_left" in result


def test_token_usage_helpers_return_safe_shapes():
    from brain.token import get_daily_usage, get_session_breakdown

    daily = get_daily_usage()
    sessions = get_session_breakdown(3)

    assert {"total_tokens", "total_cost"} <= set(daily)
    assert isinstance(sessions, list)


def test_track_usage_falls_back_to_token_state(tmp_path, monkeypatch):
    import brain.token as token

    state = tmp_path / "token_state.json"
    state.write_text(
        '{"session_cost": 0.12, "daily_cost": 0.20, "total_input_tokens": 10, "total_output_tokens": 5}',
        encoding="utf-8",
    )
    monkeypatch.setattr(token, "TOKEN_STATE_FILE", state)
    monkeypatch.setattr(token, "TOKEN_GUARD_SCRIPT", tmp_path / "missing.py")

    usage = token.track_usage()

    assert usage["session_cost"] == 0.12
    assert usage["daily_cost"] == 0.20
