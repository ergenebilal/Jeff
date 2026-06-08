"""Tests for Phase 5 cron_summary module."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from brain.phase5.cron_summary import (
    check_critical_failures,
    generate_session_start_report,
)


def _seed_cron_output(dir_path: Path, jobs: list):
    dir_path.mkdir(parents=True, exist_ok=True)
    for job in jobs:
        fname = f"{job['job_id']}.json"
        (dir_path / fname).write_text(json.dumps(job["data"]), encoding="utf-8")


def test_generate_session_start_report_empty(monkeypatch, tmp_path):
    fake_dir = tmp_path / "cron" / "output"
    monkeypatch.setattr("brain.phase5.cron_summary.CRON_OUTPUT_DIR", fake_dir)

    report = generate_session_start_report(hours=24)

    assert report["total_jobs"] == 0
    assert "bulunamadı" in report["summary"]


def test_generate_session_start_report_with_jobs(monkeypatch, tmp_path):
    fake_dir = tmp_path / "cron" / "output"
    monkeypatch.setattr("brain.phase5.cron_summary.CRON_OUTPUT_DIR", fake_dir)

    now = datetime.now(timezone.utc)
    _seed_cron_output(fake_dir, [
        {"job_id": "health_check_001", "data": {
            "status": "completed", "source": "health", "timestamp": now.isoformat()}},
        {"job_id": "eval_001", "data": {
            "status": "completed", "source": "eval", "timestamp": now.isoformat()}},
        {"job_id": "failed_job_001", "data": {
            "status": "failed", "source": "data_sync",
            "error": "connection refused", "timestamp": now.isoformat()}},
    ])

    report = generate_session_start_report(hours=24)

    assert report["total_jobs"] == 3
    assert report["success"] == 2
    assert report["failed"] == 1


def test_critical_failure_detected(monkeypatch, tmp_path):
    fake_dir = tmp_path / "cron" / "output"
    monkeypatch.setattr("brain.phase5.cron_summary.CRON_OUTPUT_DIR", fake_dir)

    now = datetime.now(timezone.utc)
    _seed_cron_output(fake_dir, [
        {"job_id": "health_check_failed", "data": {
            "status": "failed", "source": "health",
            "error": "gateway timeout", "timestamp": now.isoformat()}},
    ])

    report = generate_session_start_report(hours=24)

    assert len(report["critical_failures"]) == 1
    assert report["critical_failures"][0]["job_id"] == "health_check_failed"


def test_check_critical_failures_empty(monkeypatch, tmp_path):
    fake_dir = tmp_path / "cron" / "output"
    monkeypatch.setattr("brain.phase5.cron_summary.CRON_OUTPUT_DIR", fake_dir)

    now = datetime.now(timezone.utc)
    _seed_cron_output(fake_dir, [
        {"job_id": "gateway_check", "data": {
            "status": "completed", "source": "gateway", "timestamp": now.isoformat()}},
    ])

    failures = check_critical_failures(hours=24)
    assert failures == []


def test_old_jobs_filtered(monkeypatch, tmp_path):
    fake_dir = tmp_path / "cron" / "output"
    monkeypatch.setattr("brain.phase5.cron_summary.CRON_OUTPUT_DIR", fake_dir)

    old_ts = (datetime.now(timezone.utc) - timedelta(hours=48)).isoformat()
    now = datetime.now(timezone.utc).isoformat()
    _seed_cron_output(fake_dir, [
        {"job_id": "old_job", "data": {"status": "completed", "timestamp": old_ts}},
        {"job_id": "new_job", "data": {"status": "completed", "timestamp": now}},
    ])

    report = generate_session_start_report(hours=24)

    assert report["total_jobs"] == 1
