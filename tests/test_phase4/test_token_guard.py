"""Tests for Phase 4 token_guard module."""

import json
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def isolated_log():
    """Isolate BUDGET_LOG to a temp path."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


def _import_and_patch(monkeypatch, tmp_path):
    """Import token module and patch BUDGET_LOG."""
    import brain.phase4.token_guard as tg
    fake_log = tmp_path / "token_budget.jsonl"
    fake_log.parent.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(tg, "BUDGET_LOG", fake_log)
    return tg


def test_token_budget_check_quick_mode():
    from brain.phase4.token_guard import token_budget_check

    result = token_budget_check("quick")
    assert result["mode"] == "quick"
    assert result["soft"] == 20_000
    assert result["hard"] == 40_000
    assert result["status"] in ("ok", "warn", "hard")


def test_token_budget_check_deep_mode():
    from brain.phase4.token_guard import token_budget_check

    result = token_budget_check("deep")
    assert result["soft"] == 60_000
    assert result["hard"] == 100_000


def test_token_budget_check_background_mode():
    from brain.phase4.token_guard import token_budget_check

    result = token_budget_check("background")
    assert result["soft"] == 40_000
    assert result["hard"] == 80_000


def test_token_budget_check_warn_status(monkeypatch):
    tg = _import_and_patch(monkeypatch, Path(tempfile.mkdtemp()))

    tg.log_token_usage(25_000, "quick", "test")
    result = tg.token_budget_check("quick")
    assert result["status"] == "warn"
    assert result["remaining"] > 0


def test_token_budget_check_hard_status(monkeypatch):
    tg = _import_and_patch(monkeypatch, Path(tempfile.mkdtemp()))

    tg.log_token_usage(45_000, "quick", "test")
    result = tg.token_budget_check("quick")
    assert result["status"] == "hard"
    assert result["remaining"] == 0


def test_log_token_usage_appends(monkeypatch):
    tg = _import_and_patch(monkeypatch, Path(tempfile.mkdtemp()))

    tg.log_token_usage(1000, "deep", "eval")
    assert tg.BUDGET_LOG.exists()
    lines = tg.BUDGET_LOG.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["tokens"] == 1000
    assert entry["mode"] == "deep"
    assert entry["action"] == "eval"


def test_token_guard_check_delegates(monkeypatch):
    tg = _import_and_patch(monkeypatch, Path(tempfile.mkdtemp()))
    result = tg.TokenGuard.check("quick")
    assert "status" in result
    assert "mode" in result


def test_token_guard_guard_returns_bool(monkeypatch):
    tg = _import_and_patch(monkeypatch, Path(tempfile.mkdtemp()))
    assert tg.TokenGuard.guard("quick") is True


def test_chunk_compressor_short_text():
    from brain.phase4.token_guard import ChunkCompressor

    text = "Hello, world!"
    result = ChunkCompressor.compress(text)
    assert result == text


def test_chunk_compressor_long_text():
    from brain.phase4.token_guard import ChunkCompressor

    text = "Line " * 500
    result = ChunkCompressor.compress(text, max_chars=500)
    assert len(result) < len(text)
    assert "[... " in result


def test_chunk_compressor_chunk():
    from brain.phase4.token_guard import ChunkCompressor

    text = "A" * 5000
    chunks = ChunkCompressor.chunk(text, max_chunk=2000)
    assert len(chunks) == 3
    assert all(len(c) <= 2000 for c in chunks)


def test_chunk_compressor_summarize_errors():
    from brain.phase4.token_guard import ChunkCompressor

    middle = "\n".join([
        "INFO: starting",
        "ERROR: something broke",
        "DEBUG: var=42",
        "Traceback (most recent call last):",
        "FAIL: test_foo",
        "ok line",
    ])
    summary = ChunkCompressor._summarize_middle(middle)
    assert "ERROR" in summary
    assert "Traceback" in summary
    assert "FAIL" in summary
