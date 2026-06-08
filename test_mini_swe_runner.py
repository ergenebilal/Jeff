from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import json
import pytest


@pytest.mark.asyncio
async def test_run_task_kimi_omits_temperature():
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

        result = await runner.run_task_async("2+2")

    assert result["completed"] is True
    assert "temperature" not in client.chat.completions.create.call_args.kwargs


@pytest.mark.asyncio
async def test_run_task_public_moonshot_kimi_k2_5_omits_temperature():
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

        result = await runner.run_task_async("2+2")

    assert result["completed"] is True
    assert "temperature" not in client.chat.completions.create.call_args.kwargs


@pytest.mark.asyncio
async def test_run_task_retries_transient_api_timeout():
    with patch("openai.OpenAI") as mock_openai:
        client = MagicMock()
        client.chat.completions.create.side_effect = [
            TimeoutError("timeout while waiting for provider"),
            SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="done", tool_calls=[]))]
            ),
        ]
        mock_openai.return_value = client

        from mini_swe_runner import MiniSWERunner

        runner = MiniSWERunner(
            model="test-model",
            base_url="https://example.invalid/v1",
            api_key="test-key",
            env_type="local",
            max_iterations=1,
        )
        runner._create_env = MagicMock()
        runner._cleanup_env = MagicMock()

        result = await runner.run_task_async("2+2")

    assert result["completed"] is True
    assert result["task_status"] == "COMPLETED"
    assert client.chat.completions.create.call_count == 2


@pytest.mark.asyncio
async def test_api_retry_is_recorded_as_recovery_event(tmp_path):
    with patch("openai.OpenAI") as mock_openai:
        client = MagicMock()
        client.chat.completions.create.side_effect = [
            TimeoutError("timeout while waiting for provider"),
            SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="done", tool_calls=[]))]
            ),
        ]
        mock_openai.return_value = client

        from mini_swe_runner import MiniSWERunner

        memory = MagicMock()
        memory.recall_lessons.return_value = []
        runner = MiniSWERunner(
            model="test-model",
            base_url="https://example.invalid/v1",
            api_key="test-key",
            env_type="local",
            max_iterations=1,
            memory_adapter=memory,
            state_path=tmp_path / "agent_state.json",
        )
        runner._create_env = MagicMock()
        runner._cleanup_env = MagicMock()

        result = await runner.run_task_async("2+2")

    assert result["completed"] is True
    assert any(
        event["kind"] == "api_retry"
        for event in result["metadata"]["recovery_events"]
    )
    memory.remember_lesson.assert_called_once()


@pytest.mark.asyncio
async def test_execute_command_retries_timeout_observation():
    with patch("openai.OpenAI") as mock_openai:
        mock_openai.return_value = MagicMock()

        from mini_swe_runner import MiniSWERunner

        runner = MiniSWERunner(
            model="test-model",
            base_url="https://example.invalid/v1",
            api_key="test-key",
            env_type="local",
        )
        fake_env = MagicMock()
        fake_env.execute.side_effect = [
            {"output": "timeout from sandbox", "returncode": 124},
            {"output": "ok", "returncode": 0},
        ]
        runner.env = fake_env

        result = runner._execute_command("echo ok", timeout=1)

    assert result["output"] == "ok"
    assert result["exit_code"] == 0
    assert result["recovery_events"][0]["kind"] == "command_retry"
    assert fake_env.execute.call_count == 2


@pytest.mark.asyncio
async def test_async_loop_feeds_observation_into_next_api_call():
    tool_call = SimpleNamespace(
        id="call-1",
        type="function",
        function=SimpleNamespace(
            name="terminal",
            arguments=json.dumps({"command": "printf observation"}),
        ),
    )
    first_message = SimpleNamespace(content="running command", tool_calls=[tool_call])
    second_message = SimpleNamespace(content="finished", tool_calls=[])

    with patch("openai.OpenAI") as mock_openai:
        client = MagicMock()
        client.chat.completions.create.side_effect = [
            SimpleNamespace(choices=[SimpleNamespace(message=first_message)]),
            SimpleNamespace(choices=[SimpleNamespace(message=second_message)]),
        ]
        mock_openai.return_value = client

        from mini_swe_runner import MiniSWERunner

        runner = MiniSWERunner(
            model="test-model",
            base_url="https://example.invalid/v1",
            api_key="test-key",
            env_type="local",
            max_iterations=3,
        )
        runner._create_env = MagicMock()
        runner._cleanup_env = MagicMock()
        runner._execute_command = MagicMock(
            return_value={"output": "OBSERVATION: file created", "exit_code": 0, "error": None}
        )

        result = await runner.run_task_async("create a file")

    assert result["completed"] is True
    assert result["task_status"] == "COMPLETED"
    second_call_messages = client.chat.completions.create.call_args_list[1].kwargs["messages"]
    assert any(
        msg.get("role") == "tool" and "OBSERVATION: file created" in msg.get("content", "")
        for msg in second_call_messages
    )


def test_compress_observation_payload_summarizes_long_pytest_output():
    from mini_swe_runner import compress_observation_payload

    long_output = "\n".join(
        [f"tests/test_example.py::{i} PASSED" for i in range(120)]
        + ["======================= 120 passed in 12.34s ======================="]
    )

    compressed = compress_observation_payload(
        command="pytest tests/",
        output=long_output,
        error=None,
        exit_code=0,
    )

    assert compressed["compressed"] is True
    assert compressed["raw_output"] == long_output
    assert "120 passed" in compressed["context_output"]
    assert len(compressed["context_output"]) < len(long_output)


def test_compress_observation_payload_keeps_short_output_unchanged():
    from mini_swe_runner import compress_observation_payload

    compressed = compress_observation_payload(
        command="echo ok",
        output="ok",
        error=None,
        exit_code=0,
    )

    assert compressed["compressed"] is False
    assert compressed["context_output"] == "ok"


def test_compress_observation_payload_keeps_traceback_file_line_error():
    from mini_swe_runner import compress_observation_payload

    traceback_output = "\n".join([
        "Traceback (most recent call last):",
        '  File "/tmp/app.py", line 7, in <module>',
        "    main()",
        "ValueError: broken",
    ])

    compressed = compress_observation_payload(
        command="python /tmp/app.py",
        output=traceback_output,
        error=None,
        exit_code=1,
    )

    assert "app.py" in compressed["context_output"]
    assert "line 7" in compressed["context_output"]
    assert "ValueError: broken" in compressed["context_output"]


def test_critical_command_records_reasoning_tree(tmp_path):
    from mini_swe_runner import CriticalCommandGate

    state_path = tmp_path / "agent_state.json"
    gate = CriticalCommandGate(state_path=state_path)

    decision = gate.evaluate("rm -rf /tmp/demo", task="clean temp")

    assert decision["critical"] is True
    assert decision["chosen_strategy"]["name"] == "safe_dry_run"
    state = json.loads(state_path.read_text())
    assert len(state["reasoning_tree"]) == 1
    assert len(state["reasoning_tree"][0]["branches"]) == 3


def test_read_only_command_skips_reasoning_tree(tmp_path):
    from mini_swe_runner import CriticalCommandGate

    state_path = tmp_path / "agent_state.json"
    gate = CriticalCommandGate(state_path=state_path)

    decision = gate.evaluate("ast-grep --pattern 'def $F' .", task="inspect")

    assert decision["critical"] is False
    assert not state_path.exists()


def test_sandbox_fails_closed_for_pytest_when_docker_unavailable():
    from mini_swe_runner import SandboxCommandRouter

    router = SandboxCommandRouter(docker_checker=lambda: False)
    fake_env = MagicMock()

    result = router.execute_or_route(
        command="pytest tests/",
        cwd="/tmp/project",
        timeout=60,
        native_executor=fake_env.execute,
    )

    assert result["routed"] is True
    assert result["returncode"] == -1
    assert result["error"] == "sandbox_unavailable"
    fake_env.execute.assert_not_called()


def test_sandbox_allows_ast_grep_to_run_native():
    from mini_swe_runner import SandboxCommandRouter

    router = SandboxCommandRouter(docker_checker=lambda: False)
    fake_env = MagicMock()
    fake_env.execute.return_value = {"output": "match", "returncode": 0}

    result = router.execute_or_route(
        command="ast-grep --pattern 'def $F' .",
        cwd="/tmp/project",
        timeout=60,
        native_executor=fake_env.execute,
    )

    assert result["routed"] is False
    assert result["output"] == "match"
    fake_env.execute.assert_called_once()


@pytest.mark.asyncio
async def test_learning_loop_writes_lesson_after_recovery(tmp_path):
    tool_call = SimpleNamespace(
        id="call-1",
        type="function",
        function=SimpleNamespace(
            name="terminal",
            arguments=json.dumps({"command": "echo MINI_SWE_AGENT_FINAL_OUTPUT fixed"}),
        ),
    )
    first_message = SimpleNamespace(content="running command", tool_calls=[tool_call])

    class Memory:
        def __init__(self):
            self.remember_calls = []

        def recall_lessons(self, query, top_k=3):
            return []

        def remember_lesson(self, content, metadata):
            self.remember_calls.append((content, metadata))
            return True

    with patch("openai.OpenAI") as mock_openai:
        client = MagicMock()
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=first_message)]
        )
        mock_openai.return_value = client

        from mini_swe_runner import MiniSWERunner

        memory = Memory()
        runner = MiniSWERunner(
            model="test-model",
            base_url="https://example.invalid/v1",
            api_key="test-key",
            env_type="local",
            max_iterations=1,
            memory_adapter=memory,
            state_path=tmp_path / "agent_state.json",
        )
        runner._create_env = MagicMock()
        runner._cleanup_env = MagicMock()
        runner._execute_command = MagicMock(
            return_value={
                "output": "MINI_SWE_AGENT_FINAL_OUTPUT fixed",
                "exit_code": 0,
                "error": None,
                "recovery_events": [{"kind": "command_retry", "detail": "timeout"}],
            }
        )

        result = await runner.run_task_async("fix flaky test")

    assert result["completed"] is True
    assert memory.remember_calls
    lesson, metadata = memory.remember_calls[0]
    assert "[File/Context]" in lesson
    assert "Root Cause:" in lesson
    assert "Resolution:" in lesson
    assert "Guardrail Rule:" in lesson
    assert metadata["source"] == "mini_swe_runner"


@pytest.mark.asyncio
async def test_learning_loop_does_not_write_lesson_without_recovery(tmp_path):
    with patch("openai.OpenAI") as mock_openai:
        client = MagicMock()
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="done", tool_calls=[]))]
        )
        mock_openai.return_value = client

        from mini_swe_runner import MiniSWERunner

        memory = MagicMock()
        memory.recall_lessons.return_value = []
        runner = MiniSWERunner(
            model="test-model",
            base_url="https://example.invalid/v1",
            api_key="test-key",
            env_type="local",
            max_iterations=1,
            memory_adapter=memory,
            state_path=tmp_path / "agent_state.json",
        )
        runner._create_env = MagicMock()
        runner._cleanup_env = MagicMock()

        result = await runner.run_task_async("simple answer")

    assert result["completed"] is True
    memory.remember_lesson.assert_not_called()


@pytest.mark.asyncio
async def test_recalled_lesson_is_injected_into_api_messages(tmp_path):
    with patch("openai.OpenAI") as mock_openai:
        client = MagicMock()
        client.chat.completions.create.return_value = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="done", tool_calls=[]))]
        )
        mock_openai.return_value = client

        from mini_swe_runner import MiniSWERunner

        memory = MagicMock()
        memory.recall_lessons.return_value = ["Use py_compile before pytest on parser edits."]
        runner = MiniSWERunner(
            model="test-model",
            base_url="https://example.invalid/v1",
            api_key="test-key",
            env_type="local",
            max_iterations=1,
            memory_adapter=memory,
            state_path=tmp_path / "agent_state.json",
        )
        runner._create_env = MagicMock()
        runner._cleanup_env = MagicMock()

        await runner.run_task_async("edit parser")

    api_messages = client.chat.completions.create.call_args.kwargs["messages"]
    assert any(
        msg["role"] == "system" and "Relevant Lesson Memory" in msg["content"]
        for msg in api_messages
    )
