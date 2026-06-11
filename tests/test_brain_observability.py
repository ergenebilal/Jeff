import json
from pathlib import Path

import brain.observability as obs


def _lines(path: Path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def test_log_run_schema_and_error_budget(tmp_path, monkeypatch):
    monkeypatch.setattr(obs, 'RUN_LOG', tmp_path / 'agent_runs.jsonl')
    monkeypatch.setattr(obs, 'ERROR_BUDGET_LOG', tmp_path / 'error_budget.jsonl')

    first = obs.log_run(task_type='eval', mode='test', status='completed', metrics={'score': 0.91}, context={'topic': 'baseline'})
    second = obs.log_run(task_type='eval', mode='test', status='failed', metrics={'score': 0.12}, context={'topic': 'retry'})

    assert first['event'] == 'run'
    assert first['task_type'] == 'eval'
    assert first['status'] == 'completed'
    assert 'timestamp_utc' in first
    assert obs.RUN_LOG.exists()
    rows = _lines(obs.RUN_LOG)
    assert len(rows) == 2
    assert rows[0]['metrics']['score'] == 0.91
    assert rows[1]['status'] == 'failed'

    budget = obs.compute_error_budget(days=7)
    assert budget['window_days'] == 7
    assert budget['total_runs'] == 2
    assert budget['failed_runs'] == 1
    assert budget['error_rate'] == 0.5
    assert budget['status'] == 'critical'
    assert obs.ERROR_BUDGET_LOG.exists()


def test_step_trace_redacts_secret_and_large_payload(tmp_path, monkeypatch):
    monkeypatch.setattr(obs, 'STEP_LOG', tmp_path / 'step_trace.jsonl')

    payload = {
        'api_key': 'sk-test-1234567890abcdef',
        'nested': {'token': 'Bearer abcdefghijklmnop'},
        'body': 'x' * 2000,
    }
    result = obs.log_step(
        run_id='run-123',
        step='inspect',
        observation='Observed secret token in payload',
        command='echo demo',
        payload=payload,
    )

    assert result['event'] == 'step'
    row = _lines(obs.STEP_LOG)[0]
    assert row['run_id'] == 'run-123'
    assert row['command'] == 'echo demo'
    assert '[REDACTED]' in json.dumps(row, ensure_ascii=False)
    assert 'sk-test' not in json.dumps(row, ensure_ascii=False)
    assert 'Bearer abcdef' not in json.dumps(row, ensure_ascii=False)
    assert 'chars compressed' in row['payload']['body']


def test_token_and_autonomy_logs(tmp_path, monkeypatch):
    monkeypatch.setattr(obs, 'TOKEN_BUDGET_LOG', tmp_path / 'token_budget.jsonl')
    monkeypatch.setattr(obs, 'AUTONOMY_POLICY_LOG', tmp_path / 'autonomy_policy.jsonl')

    token = obs.record_token_budget(session_id='sess-1', usage=0.21, budget_left=0.29, status='warn')
    policy = obs.record_autonomy_decision(
        action='restart_service',
        reason='watchdog requested service restart',
        approved=False,
        risk='high',
        task_type='ops',
        metadata={'ticket': 'HERMES-7'},
    )

    assert token['status'] == 'warn'
    assert policy['approved'] is False
    assert policy['risk'] == 'high'
    token_rows = _lines(obs.TOKEN_BUDGET_LOG)
    policy_rows = _lines(obs.AUTONOMY_POLICY_LOG)
    assert token_rows[0]['session_id'] == 'sess-1'
    assert policy_rows[0]['action'] == 'restart_service'
    assert policy_rows[0]['metadata']['ticket'] == 'HERMES-7'
