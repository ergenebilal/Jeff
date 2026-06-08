import json


def test_reasoning_tree_add_read_summarize(tmp_path, monkeypatch):
    import brain.reasoning_tree as rt

    state_path = tmp_path / "agent_state.json"
    monkeypatch.setattr(rt, "STATE_PATH", state_path)
    monkeypatch.setattr(rt, "MNEMOSYNE_AVAILABLE", False)

    before = len(rt.get_recent(100))
    entry = rt.add_decision(
        command="rm -rf /tmp/demo",
        task="critical gate smoke",
        chosen_branch="safe_dry_run",
        branches=[{"name": "safe_dry_run", "score": 0.52}],
        outcome="success",
    )
    after = rt.get_recent(100)

    assert len(after) == before + 1
    assert entry["chosen_branch"] == "safe_dry_run"
    assert "1 karar" in rt.summarize()
    assert json.loads(state_path.read_text())["reasoning_tree"][0]["outcome"] == "success"


def test_reasoning_tree_missing_file_is_empty(tmp_path, monkeypatch):
    import brain.reasoning_tree as rt

    monkeypatch.setattr(rt, "STATE_PATH", tmp_path / "missing.json")

    assert rt.get_recent() == []
    assert "Henüz karar" in rt.summarize()
