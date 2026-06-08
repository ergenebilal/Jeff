import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def test_tool_policy_snapshot_separates_core_mcp_plugin_and_logs(tmp_path, monkeypatch):
    import brain.tool_policy as policy

    monkeypatch.setattr(policy, "POLICY_LOG", tmp_path / "tool_policy.jsonl")

    snapshot = policy.build_tool_policy_snapshot(
        tool_defs=[
            {"type": "function", "function": {"name": "terminal", "description": "shell"}},
            {"type": "function", "function": {"name": "mcp_github_search_code", "description": "search code"}},
            {"type": "function", "function": {"name": "plugin_magic_note", "description": "note"}},
            {"type": "function", "function": {"name": "mystery_helper", "description": "misc"}},
        ],
        tool_search_policy={"enabled": "on", "threshold_pct": 10},
        context_length=200_000,
    )

    assert snapshot["policy_mode"] == "bridge"
    assert snapshot["bridge_active"] is True
    assert snapshot["source_breakdown"] == {"core": 1, "mcp": 1, "plugin": 1, "other": 1}
    assert snapshot["visible_names"] == ["terminal", "mystery_helper"]
    assert snapshot["deferred_names"] == ["mcp_github_search_code", "plugin_magic_note"]
    assert snapshot["policy_lines"][0].startswith("🧩 Tool policy")
    assert policy.POLICY_LOG.exists()

    rows = [json.loads(line) for line in policy.POLICY_LOG.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows[-1]["policy_mode"] == "bridge"
    assert rows[-1]["deferred_names"] == ["mcp_github_search_code", "plugin_magic_note"]


def test_context_loader_includes_tool_policy_summary(monkeypatch):
    import brain.context_loader as context_loader
    import brain.tool_policy as policy

    monkeypatch.setattr(policy, "build_tool_policy_snapshot", lambda **kwargs: {
        "policy_mode": "bridge",
        "bridge_active": True,
        "source_breakdown": {"core": 1, "mcp": 1, "plugin": 0, "other": 0},
        "visible_names": ["terminal"],
        "deferred_names": ["mcp_github_search_code"],
        "policy_lines": ["🧩 Tool policy: bridge | visible=1 | deferred=1"],
    })

    context = context_loader.get_relevant_context("github")

    assert "🧩 Tool policy" in context
    assert "bridge" in context
    assert "mcp_github_search_code" in context


def test_brain_facade_exports_tool_policy_api():
    import brain

    assert callable(brain.build_tool_policy_snapshot)
    assert callable(brain.format_tool_policy_snapshot)
