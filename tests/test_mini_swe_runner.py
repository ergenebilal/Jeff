from types import SimpleNamespace
from unittest.mock import MagicMock, patch


def test_run_task_kimi_omits_temperature():
    """Kimi models should NOT have client-side temperature overrides.

    The Kimi gateway selects the correct temperature server-side.
    """
    with patch("openai.OpenAI") as mock_openai:
        client = MagicMock()
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="done", tool_calls=[]))]
        )
        mock_openai.return_value = client

        from mini_swe_runner import MiniSWERunner

        runner = MiniSWERunner(
            model="kimi-for-coding",
            base_url="https://api.kimi.com/coding/v1",
            api_key="test-key",
            env_type="local",
            max_iterations=1,
        )
        runner._create_env = MagicMock()
        runner._cleanup_env = MagicMock()

        result = runner.run_task("2+2")

    assert result["completed"] is True
    assert "temperature" not in client.chat.completions.create.call_args.kwargs


def test_run_task_public_moonshot_kimi_k2_5_omits_temperature():
    """kimi-k2.5 on the public Moonshot API should not get a forced temperature."""
    with patch("openai.OpenAI") as mock_openai:
        client = MagicMock()
        client.base_url = "https://api.moonshot.ai/v1"
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="done", tool_calls=[]))]
        )
        mock_openai.return_value = client

        from mini_swe_runner import MiniSWERunner

        runner = MiniSWERunner(
            model="kimi-k2.5",
            base_url="https://api.moonshot.ai/v1",
            api_key="test-key",
            env_type="local",
            max_iterations=1,
        )
        runner._create_env = MagicMock()
        runner._cleanup_env = MagicMock()

        result = runner.run_task("2+2")

    assert result["completed"] is True
    assert "temperature" not in client.chat.completions.create.call_args.kwargs
from types import SimpleNamespace
from unittest.mock import MagicMock, patch


def test_execute_command_blocks_critical_command_and_records_reasoning_tree(monkeypatch):
    from mini_swe_runner import MiniSWERunner

    decisions = []
    autonomy = []
    monkeypatch.setattr(
        "brain.reasoning_tree.add_decision",
        lambda command, task, chosen_branch, branches, outcome="pending": decisions.append(
            {
                "command": command,
                "task": task,
                "chosen_branch": chosen_branch,
                "branches": branches,
                "outcome": outcome,
            }
        ) or decisions[-1],
    )
    monkeypatch.setattr(
        "brain.observability.record_autonomy_decision",
        lambda **kwargs: autonomy.append(kwargs) or kwargs,
    )

    with patch("openai.OpenAI") as mock_openai:
        mock_openai.return_value = MagicMock()
        runner = MiniSWERunner(base_url="https://example.test/v1", api_key="test", env_type="local")

    runner.env = MagicMock()
    result = runner._execute_command("rm -rf /tmp/hermes-danger")

    assert result["exit_code"] == -1
    assert result["error"] == "critical_command_blocked"
    runner.env.execute.assert_not_called()
    assert decisions
    assert decisions[-1]["chosen_branch"] == "safe_dry_run"
    assert len(decisions[-1]["branches"]) == 3
    assert decisions[-1]["outcome"] == "blocked"
    assert autonomy[-1]["risk"] == "high"


def test_execute_command_allows_read_only_command_without_reasoning_tree(monkeypatch):
    from mini_swe_runner import MiniSWERunner

    decisions = []
    monkeypatch.setattr("brain.reasoning_tree.add_decision", lambda *args, **kwargs: decisions.append((args, kwargs)))

    with patch("openai.OpenAI") as mock_openai:
        mock_openai.return_value = MagicMock()
        runner = MiniSWERunner(base_url="https://example.test/v1", api_key="test", env_type="local")

    runner.env = MagicMock()
    runner.env.execute.return_value = {"output": "ok", "returncode": 0}

    result = runner._execute_command("ls -la /tmp")

    assert result == {"output": "ok", "exit_code": 0, "error": None}
    runner.env.execute.assert_called_once()
    assert decisions == []
