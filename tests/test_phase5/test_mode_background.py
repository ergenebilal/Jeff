"""Tests for Phase 5 BackgroundMode."""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture
def isolated_output():
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


def test_background_mode_init(isolated_output):
    from brain.phase5.mode_background import BackgroundMode

    mode = BackgroundMode(output_dir=isolated_output)
    assert mode.mode_name == "background"
    assert mode.context_limit == 40_000


def test_background_mode_context_fit():
    from brain.phase5.mode_background import BackgroundMode

    mode = BackgroundMode()
    result = mode.estimate_context_fit(30_000)
    assert result["within_soft"] is True
    assert result["within_hard"] is True
    assert result["mode"] == "background"


def test_background_mode_context_exceed():
    from brain.phase5.mode_background import BackgroundMode

    mode = BackgroundMode()
    result = mode.estimate_context_fit(50_000)
    assert result["within_soft"] is False
    assert result["within_hard"] is True


def test_background_run_job_success(isolated_output):
    from brain.phase5.mode_background import BackgroundMode

    mode = BackgroundMode(output_dir=isolated_output)
    result = mode.run_job("test-job-1", "do something")
    assert result["success"] is True
    assert result["job_id"] == "test-job-1"
    assert result["attempt"] == 1


def test_background_run_job_with_executor(isolated_output):
    from brain.phase5.mode_background import BackgroundMode

    mode = BackgroundMode(output_dir=isolated_output)

    def executor(task):
        return {"processed": True, "data": task}

    result = mode.run_job("exec-job", "task data", executor=executor)
    assert result["success"] is True
    assert result["result"]["processed"] is True
    assert result["result"]["data"] == "task data"


def test_background_run_job_retry_then_fail(isolated_output):
    from brain.phase5.mode_background import BackgroundMode

    mode = BackgroundMode(output_dir=isolated_output)
    attempts = [0]

    def failing(task):
        attempts[0] += 1
        raise RuntimeError("simulated failure")

    result = mode.run_job("fail-job", "x", executor=failing, retries=2)
    assert result["success"] is False
    assert "simulated failure" in result["error"]
    # First attempt + 2 retries = 3 total
    assert attempts[0] == 3


def test_background_run_job_saves_output(isolated_output):
    from brain.phase5.mode_background import BackgroundMode

    mode = BackgroundMode(output_dir=isolated_output)
    mode.run_job("save-test", "test data")
    output_file = isolated_output / "save-test.json"
    assert output_file.exists()
    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["job_id"] == "save-test"
    assert data["success"] is True


def test_background_get_job_output(isolated_output):
    from brain.phase5.mode_background import BackgroundMode

    mode = BackgroundMode(output_dir=isolated_output)
    mode.run_job("get-test", "data")
    result = mode.get_job_output("get-test")
    assert result is not None
    assert result["task"] == "data"


def test_background_get_job_output_missing(isolated_output):
    from brain.phase5.mode_background import BackgroundMode

    mode = BackgroundMode(output_dir=isolated_output)
    result = mode.get_job_output("nonexistent")
    assert result is None


def test_background_list_jobs(isolated_output):
    from brain.phase5.mode_background import BackgroundMode

    mode = BackgroundMode(output_dir=isolated_output)
    mode.run_job("job-a", "a")
    mode.run_job("job-b", "b")
    jobs = mode.list_jobs()
    assert len(jobs) == 2
    job_ids = {j["job_id"] for j in jobs}
    assert job_ids == {"job-a", "job-b"}
