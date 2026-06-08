#!/usr/bin/env python3
"""
SWE Runner with Hermes Trajectory Format

A runner that uses Hermes-Agent's built-in execution environments
(local, docker, modal) and outputs trajectories in the Hermes-Agent format
compatible with batch_runner.py and trajectory_compressor.py.

Features:
- Uses Hermes-Agent's Docker, Modal, or Local environments for command execution
- Outputs trajectories in Hermes format (from/value pairs with <tool_call>/<tool_response> XML)
- Compatible with the trajectory compression pipeline
- Supports batch processing from JSONL prompt files

Usage:
    # Run a single task with local environment
    python mini_swe_runner.py --task "Create a hello world Python script" --env local
    
    # Run with Docker
    python mini_swe_runner.py --task "List files in /tmp" --env docker --image python:3.11-slim
    
    # Run with Modal (cloud)
    python mini_swe_runner.py --task "Install numpy and test it" --env modal --image python:3.11-slim
    
    # Batch mode from JSONL file
    python mini_swe_runner.py --prompts_file prompts.jsonl --output_file trajectories.jsonl --env docker
"""

import json
import logging
import os
import asyncio
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable

import fire
from dotenv import load_dotenv
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential
from agent.tool_dispatch_helpers import make_tool_result_message

# Load environment variables
load_dotenv()


TASK_RUNNING = "RUNNING"
TASK_COMPLETED = "COMPLETED"
TASK_FAILED = "FAILED"
DEFAULT_AGENT_STATE_PATH = Path("/home/hermes/.hermes/agent_state.json")
MAX_INLINE_OBSERVATION_CHARS = 2500
MAX_INLINE_OBSERVATION_LINES = 80


class RetryableRunnerError(RuntimeError):
    """Raised for transient runner failures that should be retried."""


_RETRYABLE_ERROR_MARKERS = (
    "timeout",
    "timed out",
    "temporarily",
    "temporary",
    "rate limit",
    "429",
    "502",
    "503",
    "504",
    "connection reset",
    "connection aborted",
    "security warning",
    "safety",
    "guardrail",
)


def _is_retryable_exception(exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, RetryableRunnerError)):
        return True
    message = str(exc).lower()
    return any(marker in message for marker in _RETRYABLE_ERROR_MARKERS)


def _is_retryable_observation(output: str) -> bool:
    text = (output or "").lower()
    return any(marker in text for marker in ("timeout", "timed out", "security warning"))


def _redact_sensitive(text: str) -> str:
    """Mask likely secrets before data reaches memory/state/context."""
    if not text:
        return ""
    patterns = (
        r"sk-[A-Za-z0-9_\-]{16,}",
        r"gsk_[A-Za-z0-9_\-]{16,}",
        r"(?i)(api[_-]?key|token|secret|password|passwd)\s*[:=]\s*[^\s]+",
    )
    redacted = str(text)
    for pattern in patterns:
        redacted = re.sub(pattern, "[REDACTED]", redacted)
    return redacted


def _extract_pytest_summary(text: str) -> List[str]:
    lines = []
    summary_line = None
    for line in reversed(text.splitlines()):
        lowered = line.lower()
        if " in " in lowered and any(word in lowered for word in (" passed", " failed", " errors", " warnings")):
            summary_line = line
            break
    search_text = summary_line or text
    summary_patterns = (
        r"(\d+)\s+passed",
        r"(\d+)\s+failed",
        r"(\d+)\s+errors?",
        r"(\d+)\s+warnings?",
        r"(\d+)\s+skipped",
    )
    for pattern in summary_patterns:
        match = re.search(pattern, search_text, flags=re.IGNORECASE)
        if match:
            lines.append(match.group(0))
    return lines


def _extract_traceback_summary(text: str) -> List[str]:
    lines = []
    file_matches = re.findall(r'File "([^"]+)", line (\d+)', text)
    for file_path, line_no in file_matches[:5]:
        lines.append(f"{Path(file_path).name}: line {line_no}")
    error_matches = re.findall(r"^([A-Za-z_][\w.]*Error: .+)$", text, flags=re.MULTILINE)
    error_matches += re.findall(r"^([A-Za-z_][\w.]*Exception: .+)$", text, flags=re.MULTILINE)
    if error_matches:
        lines.append(error_matches[-1])
    return lines


def compress_observation_payload(
    command: str,
    output: str,
    error: Optional[str],
    exit_code: int,
) -> Dict[str, Any]:
    """Return a context-safe Observation while preserving raw output locally."""
    raw_output = _redact_sensitive(output or "")
    raw_error = _redact_sensitive(error or "")
    line_count = raw_output.count("\n") + (1 if raw_output else 0)
    should_compress = (
        len(raw_output) > MAX_INLINE_OBSERVATION_CHARS
        or line_count > MAX_INLINE_OBSERVATION_LINES
        or "Traceback (most recent call last)" in raw_output
    )
    if not should_compress:
        return {
            "context_output": raw_output,
            "raw_output": raw_output,
            "raw_error": raw_error,
            "compressed": False,
            "summary": None,
        }

    summary_lines = [
        "[Runtime Observation: compressed]",
        f"command: {_redact_sensitive(command)[:160]}",
        f"exit_code: {exit_code}",
        f"raw_output_lines: {line_count}",
        f"raw_output_chars: {len(raw_output)}",
    ]
    pytest_summary = _extract_pytest_summary(raw_output)
    if pytest_summary:
        summary_lines.append("pytest: " + ", ".join(pytest_summary))
    traceback_summary = _extract_traceback_summary(raw_output)
    if traceback_summary:
        summary_lines.append("traceback: " + " | ".join(traceback_summary))
    if raw_error:
        summary_lines.append(f"stderr/error: {raw_error[:500]}")
    if not pytest_summary and not traceback_summary:
        head = "\n".join(raw_output.splitlines()[:12])
        tail = "\n".join(raw_output.splitlines()[-6:])
        summary_lines.append("head:\n" + head)
        if tail and tail != head:
            summary_lines.append("tail:\n" + tail)

    context_output = "\n".join(summary_lines)
    return {
        "context_output": context_output,
        "raw_output": raw_output,
        "raw_error": raw_error,
        "compressed": True,
        "summary": context_output,
    }


class LessonMemoryAdapter:
    """Thin Mnemosyne adapter used by the mini SWE learning loop."""

    def __init__(self, memory_factory: Optional[Callable[[], Any]] = None):
        self._memory_factory = memory_factory
        self._memory = None

    def _get_memory(self):
        if self._memory is not None:
            return self._memory
        if self._memory_factory is not None:
            self._memory = self._memory_factory()
            return self._memory
        try:
            from mnemosyne import Mnemosyne
            self._memory = Mnemosyne(session_id="hermes-mini-swe", bank="lessons")
        except Exception:
            self._memory = False
        return self._memory

    def recall_lessons(self, query: str, top_k: int = 3) -> List[str]:
        memory = self._get_memory()
        if not memory:
            return []
        try:
            recalled = memory.recall(_redact_sensitive(query), top_k=top_k)
        except Exception:
            return []
        lessons = []
        for item in recalled or []:
            if isinstance(item, dict):
                content = item.get("content") or item.get("text") or item.get("memory")
            else:
                content = str(item)
            if content:
                lessons.append(_redact_sensitive(str(content)))
        return lessons[:top_k]

    def remember_lesson(self, content: str, metadata: Dict[str, Any]) -> bool:
        memory = self._get_memory()
        if not memory:
            return False
        try:
            memory.remember(
                _redact_sensitive(content),
                source="mini_swe_runner",
                importance=0.85,
                metadata=metadata,
            )
            return True
        except Exception:
            return False


class CriticalCommandGate:
    """Deterministic tree-of-thought gate for high-risk commands."""

    _CRITICAL_PATTERNS = (
        r"\brm\s+-",
        r"\bmv\s+",
        r"\bchmod\s+",
        r"\bchown\s+",
        r"\bsystemctl\s+(restart|stop|disable|enable)",
        r"\bservice\s+\w+\s+(restart|stop)",
        r"\b(alembic|django-admin|manage\.py)\s+.*migrat",
        r"\bgit\s+(reset|clean|checkout)\b",
        r"<<\s*['\"]?\w+",
        r"\b(curl|wget)\b.*\|\s*(bash|sh)",
        r"\b(bash|sh)\s+.+\.sh\b",
    )

    def __init__(self, state_path: Path = DEFAULT_AGENT_STATE_PATH):
        self.state_path = Path(state_path)

    def is_critical(self, command: str) -> bool:
        text = command or ""
        return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in self._CRITICAL_PATTERNS)

    def evaluate(self, command: str, task: str = "") -> Dict[str, Any]:
        if not self.is_critical(command):
            return {"critical": False, "chosen_strategy": None}
        branches = [
            {
                "name": "safe_dry_run",
                "description": "Inspect intent, simulate, or ask for non-mutating evidence first.",
                "token_cost": 1,
                "success_probability": 0.60,
                "system_safety_risk": 0.05,
            },
            {
                "name": "limited_patch_or_sandbox",
                "description": "Run the risky action only inside the ephemeral sandbox.",
                "token_cost": 2,
                "success_probability": 0.75,
                "system_safety_risk": 0.20,
            },
            {
                "name": "direct_execution",
                "description": "Execute directly on host.",
                "token_cost": 1,
                "success_probability": 0.90,
                "system_safety_risk": 0.95,
            },
        ]
        for branch in branches:
            branch["score"] = round(
                branch["success_probability"] - branch["system_safety_risk"] - (branch["token_cost"] * 0.03),
                3,
            )
        chosen = sorted(branches, key=lambda item: (item["system_safety_risk"], -item["score"]))[0]
        tree = {
            "timestamp": datetime.now().isoformat(),
            "command": _redact_sensitive(command),
            "task": _redact_sensitive(task)[:500],
            "branches": branches,
            "chosen_strategy": chosen,
        }
        self._write_tree(tree)
        return {"critical": True, "chosen_strategy": chosen, "tree": tree}

    def _write_tree(self, tree: Dict[str, Any]) -> None:
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            if self.state_path.exists():
                state = json.loads(self.state_path.read_text(encoding="utf-8"))
            else:
                state = {}
            state.setdefault("reasoning_tree", []).append(tree)
            tmp_path = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
            tmp_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp_path.replace(self.state_path)
        except Exception:
            return


class SandboxCommandRouter:
    """Route risky runtime commands through Docker, failing closed when unavailable."""

    def __init__(self, docker_checker: Optional[Callable[[], bool]] = None):
        self._docker_checker = docker_checker or self._docker_available

    def is_read_only(self, command: str) -> bool:
        text = (command or "").strip()
        read_only_prefixes = (
            "ast-grep ",
            "grep ",
            "rg ",
            "ls",
            "find ",
            "sed -n",
            "cat ",
        )
        if text.startswith(read_only_prefixes):
            return True
        return bool(re.match(r"^python(\d+(\.\d+)?)?\s+-m\s+py_compile\b", text))

    def requires_sandbox(self, command: str) -> bool:
        if self.is_read_only(command):
            return False
        text = (command or "").lower()
        sandbox_markers = (
            "pytest",
            "python ",
            "bash ",
            "sh ",
            "npm test",
            "npm run",
            "alembic",
            "migrate",
            "rm -",
            "systemctl",
        )
        return any(marker in text for marker in sandbox_markers)

    def execute_or_route(
        self,
        command: str,
        cwd: str,
        timeout: int,
        native_executor: Callable[..., Dict[str, Any]],
    ) -> Dict[str, Any]:
        if not self.requires_sandbox(command):
            result = native_executor(command, timeout=timeout)
            result["routed"] = False
            return result
        if not self._docker_checker():
            return {
                "output": "",
                "returncode": -1,
                "error": "sandbox_unavailable",
                "routed": True,
                "route": "docker",
            }
        safe_cwd = cwd or "/tmp"
        docker_command = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{safe_cwd}:/workspace",
            "-w",
            "/workspace",
            "python:3.11-slim",
            "bash",
            "-lc",
            command,
        ]
        try:
            completed = subprocess.run(
                docker_command,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return {
                "output": (completed.stdout or "") + (completed.stderr or ""),
                "returncode": completed.returncode,
                "error": None,
                "routed": True,
                "route": "docker",
            }
        except Exception as exc:
            return {
                "output": "",
                "returncode": -1,
                "error": f"sandbox_error: {exc}",
                "routed": True,
                "route": "docker",
            }

    @staticmethod
    def _docker_available() -> bool:
        try:
            result = subprocess.run(
                ["docker", "version", "--format", "{{.Server.Version}}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except Exception:
            return False


def build_recovery_lesson(task: str, recovery_events: List[Dict[str, Any]]) -> str:
    event_text = "; ".join(
        f"{event.get('kind', 'event')}={_redact_sensitive(str(event.get('detail', '')))}"
        for event in recovery_events[:5]
    )
    return (
        f"[File/Context] - mini_swe_runner task: {_redact_sensitive(task)[:180]} - "
        f"Root Cause: transient or unsafe execution friction observed ({event_text}). - "
        "Resolution: retry/backoff, compressed observations, or sandbox/strategy routing allowed progress. - "
        "Guardrail Rule: preserve raw logs locally, feed compressed observations to the model, and never run risky commands on host when sandbox is unavailable."
    )


def _effective_temperature_for_model(
    model: str,
    base_url: Optional[str] = None,
) -> Optional[float]:
    """Return a fixed temperature for models with strict sampling contracts.

    Returns ``None`` when the model manages temperature server-side (Kimi);
    callers must omit the ``temperature`` kwarg entirely in that case.
    """
    try:
        from agent.auxiliary_client import _fixed_temperature_for_model, OMIT_TEMPERATURE
    except Exception:
        return None
    result = _fixed_temperature_for_model(model, base_url)
    if result is OMIT_TEMPERATURE:
        return None  # caller must omit temperature
    return result




# ============================================================================
# Terminal Tool Definition (matches Hermes-Agent format)
# ============================================================================

TERMINAL_TOOL_DEFINITION = {
    "type": "function",
    "function": {
        "name": "terminal",
        "description": """Execute bash commands in a sandboxed environment.

**Environment:**
- Isolated execution environment (local, Docker, or Modal cloud)
- Filesystem persists between tool calls within the same task
- Internet access available

**Command Execution:**
- Provide the command to execute via the 'command' parameter
- Optional 'timeout' parameter in seconds (default: 60)

**Examples:**
- Run command: `{"command": "ls -la"}`
- With timeout: `{"command": "long_task.sh", "timeout": 300}`

**Best Practices:**
- Use non-interactive commands (avoid vim, nano, interactive python)
- Pipe to cat if output might be large
- Install tools with apt-get or pip as needed

**Completion:**
- When task is complete, output: echo "MINI_SWE_AGENT_FINAL_OUTPUT" followed by your result
""",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The bash command to execute"
                },
                "timeout": {
                    "type": "integer",
                    "description": "Command timeout in seconds (default: 60)"
                }
            },
            "required": ["command"]
        }
    }
}


# ============================================================================
# Environment Factory
# ============================================================================

def create_environment(
    env_type: str = "local",
    image: str = "python:3.11-slim",
    cwd: str = "/tmp",
    timeout: int = 60,
    **kwargs
):
    """
    Create an execution environment using Hermes-Agent's built-in backends.
    
    Args:
        env_type: One of "local", "docker", "modal"
        image: Docker/Modal image name (ignored for local)
        cwd: Working directory
        timeout: Default command timeout
        **kwargs: Additional environment-specific options
        
    Returns:
        Environment instance with execute() and cleanup() methods
    """
    if env_type == "local":
        from tools.environments.local import LocalEnvironment
        return LocalEnvironment(cwd=cwd, timeout=timeout)
    
    elif env_type == "docker":
        from tools.environments.docker import DockerEnvironment
        return DockerEnvironment(image=image, cwd=cwd, timeout=timeout, **kwargs)
    
    elif env_type == "modal":
        from tools.environments.modal import ModalEnvironment
        return ModalEnvironment(image=image, cwd=cwd, timeout=timeout, **kwargs)
    
    else:
        raise ValueError(f"Unknown environment type: {env_type}. Use 'local', 'docker', or 'modal'")


# ============================================================================
# Mini-SWE Runner with Hermes Trajectory Format
# ============================================================================

class MiniSWERunner:
    """
    Agent runner that uses Hermes-Agent's built-in execution environments
    and outputs trajectories in Hermes-Agent format.
    """
    
    def __init__(
        self,
        model: str = "anthropic/claude-sonnet-4.6",
        base_url: str = None,
        api_key: str = None,
        env_type: str = "local",
        image: str = "python:3.11-slim",
        cwd: str = "/tmp",
        max_iterations: int = 15,
        command_timeout: int = 60,
        verbose: bool = False,
        memory_adapter: Optional[Any] = None,
        state_path: Optional[Path] = None,
        sandbox_router: Optional[SandboxCommandRouter] = None,
    ):
        """
        Initialize the Mini-SWE Runner.
        
        Args:
            model: Model name for OpenAI-compatible API
            base_url: API base URL (optional, uses env vars if not provided)
            api_key: API key (optional, uses env vars if not provided)
            env_type: Environment type - "local", "docker", or "modal"
            image: Docker/Modal image (ignored for local)
            cwd: Working directory for commands
            max_iterations: Maximum tool-calling iterations
            command_timeout: Default timeout for commands
            verbose: Enable verbose logging
        """
        self.model = model
        self.max_iterations = max_iterations
        self.command_timeout = command_timeout
        self.verbose = verbose
        self.env_type = env_type
        self.image = image
        self.cwd = cwd
        self.memory_adapter = memory_adapter or LessonMemoryAdapter()
        self.state_path = Path(state_path) if state_path is not None else DEFAULT_AGENT_STATE_PATH
        self.critical_gate = CriticalCommandGate(self.state_path)
        self.sandbox_router = sandbox_router or SandboxCommandRouter()
        self._active_recovery_events: List[Dict[str, Any]] = []
        
        # Setup logging
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize LLM client via centralized provider router.
        # If explicit api_key/base_url are provided (e.g. from CLI args),
        # construct directly.  Otherwise use the router for OpenRouter.
        if api_key or base_url:
            from openai import OpenAI
            client_kwargs = {
                "base_url": base_url or "https://openrouter.ai/api/v1",
                "api_key": api_key or os.getenv(
                    "OPENROUTER_API_KEY",
                    os.getenv("ANTHROPIC_API_KEY",
                              os.getenv("OPENAI_API_KEY", ""))),
            }
            self.client = OpenAI(**client_kwargs)
        else:
            from agent.auxiliary_client import resolve_provider_client
            self.client, _ = resolve_provider_client("openrouter", model=model)
            if self.client is None:
                # Fallback: try auto-detection
                self.client, _ = resolve_provider_client("auto", model=model)
            if self.client is None:
                from openai import OpenAI
                self.client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=os.getenv("OPENROUTER_API_KEY", ""))
        
        # Environment will be created per-task
        self.env = None
        
        # Tool definition
        self.tools = [TERMINAL_TOOL_DEFINITION]
        
        print("🤖 Mini-SWE Runner initialized")
        print(f"   Model: {self.model}")
        print(f"   Environment: {self.env_type}")
        if self.env_type != "local":
            print(f"   Image: {self.image}")
        print(f"   Max iterations: {self.max_iterations}")
    
    def _create_env(self):
        """Create the execution environment."""
        print(f"🔧 Creating {self.env_type} environment...")
        self.env = create_environment(
            env_type=self.env_type,
            image=self.image,
            cwd=self.cwd,
            timeout=self.command_timeout
        )
        print("✅ Environment ready")
    
    def _cleanup_env(self):
        """Cleanup the execution environment."""
        if self.env is not None:
            if hasattr(self.env, 'cleanup'):
                self.env.cleanup()
            elif hasattr(self.env, 'stop'):
                self.env.stop()
            self.env = None

    @retry(
        retry=retry_if_exception(_is_retryable_exception),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _execute_command_once(self, command: str, timeout: int) -> Dict[str, Any]:
        """Execute one terminal command attempt, retrying transient observations."""
        self._command_attempt_counter = getattr(self, "_command_attempt_counter", 0) + 1
        result = self.sandbox_router.execute_or_route(
            command=command,
            cwd=self.cwd,
            timeout=timeout,
            native_executor=self.env.execute,
        )
        output = result.get("output", "")
        if _is_retryable_observation(output):
            raise RetryableRunnerError(output)
        return result
    
    def _execute_command(self, command: str, timeout: int = None) -> Dict[str, Any]:
        """
        Execute a command in the environment.
        
        Args:
            command: Bash command to execute
            timeout: Optional timeout override
            
        Returns:
            Dict with 'output' and 'returncode'
        """
        if self.env is None:
            self._create_env()
        
        try:
            self._command_attempt_counter = 0
            result = self._execute_command_once(command, timeout or self.command_timeout)
            recovery_events = []
            if getattr(self, "_command_attempt_counter", 1) > 1:
                recovery_events.append({
                    "kind": "command_retry",
                    "detail": f"attempts={self._command_attempt_counter}",
                })
            if result.get("routed"):
                recovery_events.append({
                    "kind": "sandbox_route",
                    "detail": result.get("error") or result.get("route") or "docker",
                })
            return {
                "output": result.get("output", ""),
                "exit_code": result.get("returncode", 0),
                "error": result.get("error"),
                "recovery_events": recovery_events,
            }
        except Exception as e:
            return {
                "output": "",
                "exit_code": -1,
                "error": str(e),
                "recovery_events": [{"kind": "command_error", "detail": str(e)}],
            }

    async def _execute_command_async(self, command: str, timeout: int = None) -> Dict[str, Any]:
        """Async wrapper for retry-protected command execution."""
        return self._execute_command(command, timeout)

    @retry(
        retry=retry_if_exception(_is_retryable_exception),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _create_chat_completion_with_retry(self, **api_kwargs):
        """Create a chat completion with exponential backoff for transient failures."""
        self._api_attempt_counter = getattr(self, "_api_attempt_counter", 0) + 1
        return self.client.chat.completions.create(**api_kwargs)

    async def _create_chat_completion_async(self, **api_kwargs):
        """Async wrapper for tenacity-backed API calls."""
        return self._create_chat_completion_with_retry(**api_kwargs)
    
    def _format_tools_for_system_message(self) -> str:
        """Format tool definitions for the system message."""
        formatted_tools = []
        for tool in self.tools:
            func = tool["function"]
            formatted_tools.append({
                "name": func["name"],
                "description": func.get("description", ""),
                "parameters": func.get("parameters", {}),
                "required": None
            })
        return json.dumps(formatted_tools, ensure_ascii=False)
    
    def _convert_to_hermes_format(
        self,
        messages: List[Dict[str, Any]],
        user_query: str,
        completed: bool
    ) -> List[Dict[str, Any]]:
        """
        Convert internal message format to Hermes trajectory format.
        
        This produces the exact format used by batch_runner.py.
        """
        trajectory = []
        
        # System message with tool definitions
        system_msg = (
            "You are a function calling AI model. You are provided with function signatures within <tools> </tools> XML tags. "
            "You may call one or more functions to assist with the user query. If available tools are not relevant in assisting "
            "with user query, just respond in natural conversational language. Don't make assumptions about what values to plug "
            "into functions. After calling & executing the functions, you will be provided with function results within "
            "<tool_response> </tool_response> XML tags. Here are the available tools:\n"
            f"<tools>\n{self._format_tools_for_system_message()}\n</tools>\n"
            "For each function call return a JSON object, with the following pydantic model json schema for each:\n"
            "{'title': 'FunctionCall', 'type': 'object', 'properties': {'name': {'title': 'Name', 'type': 'string'}, "
            "'arguments': {'title': 'Arguments', 'type': 'object'}}, 'required': ['name', 'arguments']}\n"
            "Each function call should be enclosed within <tool_call> </tool_call> XML tags.\n"
            "Example:\n<tool_call>\n{'name': <function-name>,'arguments': <args-dict>}\n</tool_call>"
        )
        
        trajectory.append({"from": "system", "value": system_msg})
        trajectory.append({"from": "human", "value": user_query})
        
        # Process messages (skip first user message as we already added it)
        i = 1
        while i < len(messages):
            msg = messages[i]
            
            if msg["role"] == "assistant":
                if "tool_calls" in msg and msg["tool_calls"]:
                    # Assistant message with tool calls
                    content = ""
                    
                    # Add reasoning if present
                    if msg.get("reasoning"):
                        content = f"<think>{msg['reasoning']}</think>"
                    
                    if msg.get("content"):
                        content += msg["content"] + "\n"
                    
                    # Add tool calls in XML format
                    for tool_call in msg["tool_calls"]:
                        if not tool_call or not isinstance(tool_call, dict): continue
                        try:
                            arguments = json.loads(tool_call["function"]["arguments"]) \
                                if isinstance(tool_call["function"]["arguments"], str) \
                                else tool_call["function"]["arguments"]
                        except json.JSONDecodeError:
                            arguments = {}
                        
                        tool_call_json = {
                            "name": tool_call["function"]["name"],
                            "arguments": arguments
                        }
                        content += f"<tool_call>\n{json.dumps(tool_call_json, ensure_ascii=False)}\n</tool_call>\n"
                    
                    trajectory.append({"from": "gpt", "value": content.rstrip()})
                    
                    # Collect subsequent tool responses
                    tool_responses = []
                    j = i + 1
                    while j < len(messages) and messages[j]["role"] == "tool":
                        tool_msg = messages[j]
                        tool_content = tool_msg["content"]
                        
                        # Try to parse as JSON
                        try:
                            if tool_content.strip().startswith(("{", "[")):
                                tool_content = json.loads(tool_content)
                        except (json.JSONDecodeError, AttributeError):
                            pass
                        
                        tool_response = "<tool_response>\n"
                        tool_response += json.dumps({
                            "tool_call_id": tool_msg.get("tool_call_id", ""),
                            "name": msg["tool_calls"][len(tool_responses)]["function"]["name"] \
                                if len(tool_responses) < len(msg["tool_calls"]) else "unknown",
                            "content": tool_content
                        }, ensure_ascii=False)
                        tool_response += "\n</tool_response>"
                        tool_responses.append(tool_response)
                        j += 1
                    
                    if tool_responses:
                        trajectory.append({"from": "tool", "value": "\n".join(tool_responses)})
                        i = j - 1
                
                else:
                    # Regular assistant message (no tool calls)
                    content = ""
                    if msg.get("reasoning"):
                        content = f"<think>{msg['reasoning']}</think>"
                    content += msg.get("content") or ""
                    trajectory.append({"from": "gpt", "value": content})
            
            elif msg["role"] == "user":
                trajectory.append({"from": "human", "value": msg["content"]})
            
            i += 1
        
        return trajectory
    
    async def run_task_async(self, task: str) -> Dict[str, Any]:
        """
        Run a single task in an autonomous async loop and return the result.

        The loop keeps feeding terminal Observations back into the next model
        turn until task_status becomes COMPLETED or FAILED.
        
        Args:
            task: The task/prompt to execute
            
        Returns:
            Dict with trajectory, completion status, and metadata
        """
        print(f"\n{'='*60}")
        print(f"📝 Task: {task[:80]}{'...' if len(task) > 80 else ''}")
        print(f"{'='*60}")
        
        # Initialize environment
        self._create_env()
        
        # Message history
        messages = [{"role": "user", "content": task}]
        
        # System prompt for the LLM (ephemeral - not saved to trajectory)
        system_prompt = """You are an AI agent that can execute bash commands to complete tasks.

When you need to run commands, use the 'terminal' tool with your bash command.

**Important:**
- When you have completed the task successfully, run: echo "MINI_SWE_AGENT_FINAL_OUTPUT" followed by a summary
- Be concise and efficient in your approach
- Install any needed tools with apt-get or pip
- Avoid interactive commands (no vim, nano, less, etc.)

Complete the user's task step by step."""
        
        api_call_count = 0
        task_status = TASK_RUNNING
        final_response = None
        raw_observations: List[Dict[str, Any]] = []
        recovery_events: List[Dict[str, Any]] = []
        recalled_lessons = self.memory_adapter.recall_lessons(task, top_k=3)
        strategy_notes: List[str] = []
        
        try:
            while task_status not in (TASK_COMPLETED, TASK_FAILED):
                if api_call_count >= self.max_iterations:
                    task_status = TASK_FAILED
                    print(f"⚠️  Reached max iterations ({self.max_iterations})")
                    break

                api_call_count += 1
                print(f"\n🔄 API call #{api_call_count}/{self.max_iterations}")
                
                # Prepare API messages
                api_messages = [{"role": "system", "content": system_prompt}]
                if recalled_lessons:
                    lesson_block = "\n".join(f"- {lesson}" for lesson in recalled_lessons)
                    api_messages.append({
                        "role": "system",
                        "content": f"Relevant Lesson Memory:\n{lesson_block}",
                    })
                if strategy_notes:
                    api_messages.append({
                        "role": "system",
                        "content": "Chosen critical strategies:\n" + "\n".join(strategy_notes[-3:]),
                    })
                api_messages += messages
                
                # Make API call
                try:
                    api_kwargs = {
                        "model": self.model,
                        "messages": api_messages,
                        "tools": self.tools,
                        "timeout": 300.0,
                    }
                    fixed_temperature = _effective_temperature_for_model(
                        self.model,
                        str(getattr(self.client, "base_url", "") or ""),
                    )
                    if fixed_temperature is not None:
                        api_kwargs["temperature"] = fixed_temperature

                    self._api_attempt_counter = 0
                    response = await self._create_chat_completion_async(**api_kwargs)
                    if getattr(self, "_api_attempt_counter", 1) > 1:
                        recovery_events.append({
                            "kind": "api_retry",
                            "detail": f"attempts={self._api_attempt_counter}",
                        })
                except Exception as e:
                    self.logger.error(f"API call failed: {e}")
                    task_status = TASK_FAILED
                    break
                
                assistant_message = response.choices[0].message
                
                # Log assistant response
                if assistant_message.content:
                    print(f"🤖 Assistant: {assistant_message.content[:100]}...")
                
                # Check for tool calls
                if assistant_message.tool_calls:
                    print(f"🔧 Tool calls: {len(assistant_message.tool_calls)}")
                    
                    # Add assistant message with tool calls
                    messages.append({
                        "role": "assistant",
                        "content": assistant_message.content,
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": tc.type,
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments
                                }
                            }
                            for tc in assistant_message.tool_calls
                        ]
                    })
                    
                    # Execute each tool call
                    for tc in assistant_message.tool_calls:
                        try:
                            args = json.loads(tc.function.arguments)
                        except json.JSONDecodeError:
                            args = {}
                        
                        command = args.get("command", "echo 'No command provided'")
                        timeout = args.get("timeout", self.command_timeout)
                        
                        print(f"   📞 terminal: {command[:60]}...")

                        critical_decision = self.critical_gate.evaluate(command, task=task)
                        if critical_decision.get("critical"):
                            chosen = critical_decision["chosen_strategy"]["name"]
                            recovery_events.append({
                                "kind": "critical_gate",
                                "detail": f"{chosen}: {command[:120]}",
                            })
                            strategy_notes.append(f"{chosen} for `{_redact_sensitive(command)[:120]}`")
                        
                        # Execute command
                        result = await self._execute_command_async(command, timeout)
                        command_recovery_events = result.get("recovery_events") or []
                        recovery_events.extend(command_recovery_events)
                        if result.get("error") or result.get("exit_code", 0) != 0:
                            recovery_events.append({
                                "kind": "command_error",
                                "detail": result.get("error") or f"exit_code={result.get('exit_code')}",
                            })
                        observation = compress_observation_payload(
                            command=command,
                            output=result.get("output", ""),
                            error=result.get("error"),
                            exit_code=result.get("exit_code", 0),
                        )
                        raw_observations.append({
                            "command": _redact_sensitive(command),
                            "raw_output": observation["raw_output"],
                            "raw_error": observation["raw_error"],
                            "compressed": observation["compressed"],
                        })
                        
                        # Format result
                        result_json = json.dumps({
                            "content": {
                                "output": observation["context_output"],
                                "exit_code": result["exit_code"],
                                "error": result["error"],
                                "compressed": observation["compressed"],
                                "raw_output_preserved": observation["raw_output"] != observation["context_output"],
                            }
                        }, ensure_ascii=False)
                        
                        # Check for task completion signal
                        if "MINI_SWE_AGENT_FINAL_OUTPUT" in result["output"]:
                            print("   ✅ Task completion signal detected!")
                            task_status = TASK_COMPLETED
                        
                        # Add tool response
                        messages.append(make_tool_result_message(
                            tc.function.name, result_json, tc.id,
                        ))
                        
                        print(f"   ✅ exit_code={result['exit_code']}, output={len(result['output'])} chars")
                    
                    # If task completed, we can stop
                    if task_status == TASK_COMPLETED:
                        final_response = assistant_message.content
                        break
                
                else:
                    # No tool calls - final response
                    final_response = assistant_message.content or ""
                    messages.append({
                        "role": "assistant",
                        "content": final_response
                    })
                    task_status = TASK_COMPLETED
                    print("🎉 Agent finished (no more tool calls)")
                    break
        
        finally:
            # Cleanup environment
            self._cleanup_env()
        
        # Convert to Hermes trajectory format
        completed = task_status == TASK_COMPLETED
        if completed and recovery_events:
            lesson = build_recovery_lesson(task, recovery_events)
            self.memory_adapter.remember_lesson(
                lesson,
                metadata={
                    "source": "mini_swe_runner",
                    "task_status": task_status,
                    "event_count": len(recovery_events),
                    "timestamp": datetime.now().isoformat(),
                },
            )
        trajectory = self._convert_to_hermes_format(messages, task, completed)
        
        return {
            "conversations": trajectory,
            "completed": completed,
            "task_status": task_status,
            "api_calls": api_call_count,
            "metadata": {
                "model": self.model,
                "env_type": self.env_type,
                "timestamp": datetime.now().isoformat(),
                "recovery_events": recovery_events,
                "raw_observations": raw_observations,
            }
        }

    def run_task(self, task: str) -> Dict[str, Any]:
        """
        Run a single task and return the result with trajectory.

        Backwards-compatible sync wrapper around the autonomous async loop.
        """
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(self.run_task_async(task))
            finally:
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.run_until_complete(loop.shutdown_default_executor())
                asyncio.set_event_loop(None)
                loop.close()

        raise RuntimeError("run_task() cannot be called from an active event loop; use run_task_async().")
    
    def run_batch(
        self,
        prompts: List[str],
        output_file: str
    ) -> List[Dict[str, Any]]:
        """
        Run multiple tasks and save trajectories to a JSONL file.
        
        Args:
            prompts: List of task prompts
            output_file: Output JSONL file path
            
        Returns:
            List of results
        """
        results = []
        
        print(f"\n📦 Running batch of {len(prompts)} tasks")
        print(f"📁 Output: {output_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for i, prompt in enumerate(prompts, 1):
                print(f"\n{'='*60}")
                print(f"📋 Task {i}/{len(prompts)}")
                print(f"{'='*60}")
                
                try:
                    result = self.run_task(prompt)
                    results.append(result)
                    
                    # Write to file immediately
                    f.write(json.dumps(result, ensure_ascii=False) + "\n")
                    f.flush()
                    
                    print(f"✅ Task {i} completed (api_calls={result['api_calls']})")
                    
                except Exception as e:
                    self.logger.error(f"Error on task {i}: {e}")
                    error_result = {
                        "conversations": [],
                        "completed": False,
                        "api_calls": 0,
                        "error": str(e),
                        "metadata": {"timestamp": datetime.now().isoformat()}
                    }
                    results.append(error_result)
                    f.write(json.dumps(error_result, ensure_ascii=False) + "\n")
                    f.flush()
        
        print(f"\n✅ Batch complete! {len(results)} trajectories saved to {output_file}")
        return results


# ============================================================================
# CLI Interface
# ============================================================================

def main(
    task: str = None,
    prompts_file: str = None,
    output_file: str = "swe-runner-test1.jsonl",
    model: str = "claude-sonnet-4-20250514",
    base_url: str = None,
    api_key: str = None,
    env: str = "local",
    image: str = "python:3.11-slim",
    cwd: str = "/tmp",
    max_iterations: int = 15,
    timeout: int = 60,
    verbose: bool = False,
):
    """
    Run SWE tasks with Hermes trajectory format output.
    
    Args:
        task: Single task to run (use this OR prompts_file)
        prompts_file: JSONL file with prompts (each line: {"prompt": "..."})
        output_file: Output JSONL file for trajectories
        model: Model name (default: claude-sonnet-4-20250514)
        base_url: API base URL (optional)
        api_key: API key (optional, uses env vars)
        env: Environment type - "local", "docker", or "modal"
        image: Docker/Modal image (default: python:3.11-slim)
        cwd: Working directory (default: /tmp)
        max_iterations: Maximum tool-calling iterations (default: 15)
        timeout: Command timeout in seconds (default: 60)
        verbose: Enable verbose logging
        
    Examples:
        # Single task with local environment
        python mini_swe_runner.py --task "Create hello.py that prints Hello World"
        
        # Single task with Docker
        python mini_swe_runner.py --task "List files" --env docker
        
        # Batch from file
        python mini_swe_runner.py --prompts_file tasks.jsonl --output_file results.jsonl
    """
    print("🚀 Mini-SWE Runner with Hermes Trajectory Format")
    print("=" * 60)
    
    # Initialize runner
    runner = MiniSWERunner(
        model=model,
        base_url=base_url,
        api_key=api_key,
        env_type=env,
        image=image,
        cwd=cwd,
        max_iterations=max_iterations,
        command_timeout=timeout,
        verbose=verbose,
    )
    
    if task:
        # Single task mode
        result = runner.run_task(task)
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json.dumps(result, ensure_ascii=False) + "\n")
        
        print(f"\n📁 Trajectory saved to: {output_file}")
        print(f"✅ Completed: {result['completed']}")
        print(f"📞 API calls: {result['api_calls']}")
        print(f"💬 Turns: {len(result['conversations'])}")
        
    elif prompts_file:
        # Batch mode
        prompts = []
        with open(prompts_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        prompts.append(entry.get("prompt", entry.get("task", "")))
                    except json.JSONDecodeError:
                        prompts.append(line)
        
        if not prompts:
            print(f"❌ No prompts found in {prompts_file}")
            return
        
        runner.run_batch(prompts, output_file)
    
    else:
        print("❌ Please provide either --task or --prompts_file")
        print("   Example: python mini_swe_runner.py --task 'Create a hello world script'")


if __name__ == "__main__":
    fire.Fire(main)
