"""Reasoning tree manager for critical Hermes decisions."""

import json
from datetime import datetime, timezone
from pathlib import Path


STATE_PATH = Path.home() / ".hermes" / "agent_state.json"
MNEMOSYNE_AVAILABLE = True


def _load_tree() -> dict:
    if STATE_PATH.exists():
        try:
            data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            if isinstance(data.get("reasoning_tree"), list):
                return data
        except Exception:
            pass
    return {"reasoning_tree": []}


def _save_tree(data: dict):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(STATE_PATH.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(STATE_PATH)


def add_decision(command: str, task: str, chosen_branch: str, branches: list, outcome: str = "pending") -> dict:
    tree = _load_tree()
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "command": command,
        "task": task,
        "chosen_branch": chosen_branch,
        "branches": branches,
        "outcome": outcome,
    }
    tree.setdefault("reasoning_tree", []).append(entry)
    _save_tree(tree)
    if MNEMOSYNE_AVAILABLE:
        _push_to_mnemosyne(entry)
    return entry


def get_recent(limit: int = 10) -> list:
    tree = _load_tree()
    return tree.get("reasoning_tree", [])[-int(limit):]


def summarize() -> str:
    entries = _load_tree().get("reasoning_tree", [])
    if not entries:
        return "Henüz karar kaydı yok."
    total = len(entries)
    succeeded = sum(1 for item in entries if item.get("outcome") == "success")
    failed = sum(1 for item in entries if item.get("outcome") == "failed")
    last = entries[-1]
    return (
        f"🧠 {total} karar | ✅ {succeeded} başarılı | ❌ {failed} başarısız\n"
        f"Son: {str(last.get('command', ''))[:50]}... → {last.get('outcome', 'pending')}"
    )


def _push_to_mnemosyne(entry: dict):
    try:
        from mnemosyne import Mnemosyne

        memory = Mnemosyne(session_id="hermes-reasoning-tree", bank="reasoning")
        memory.remember(
            json.dumps(entry, ensure_ascii=False),
            source="reasoning_tree",
            importance=0.7,
            metadata={"outcome": entry.get("outcome"), "chosen_branch": entry.get("chosen_branch")},
        )
    except Exception:
        return
