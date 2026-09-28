#!/usr/bin/env python3
"""Brain v3 State Manager — state.json oku, güncelle, yaz."""
import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

STATE_PATH: str = "/tmp/hermes-brain-state.json"
TZ: timezone = timezone(timedelta(hours=3))  # Europe/Istanbul

StateDict = dict[str, Any]


def load() -> StateDict:
    """State.json'dan oku, yoksa default döndür."""
    if not os.path.exists(STATE_PATH):
        return default_state()
    try:
        with open(STATE_PATH) as f:
            data: StateDict = json.load(f)
            return data
    except (json.JSONDecodeError, IOError):
        return default_state()


def default_state() -> StateDict:
    return {
        "phase": "discover",
        "phase_started": None,
        "errors_turn": 0,
        "errors_session": 0,
        "tokens_session": 0,
        "tokens_budget_left": 5.00,
        "current_task": None,
        "decisions": [],
        "tool_calls_turn": 0,
        "last_updated": None,
    }


def save(state: StateDict) -> None:
    """State'i diske yaz."""
    state["last_updated"] = datetime.now(TZ).isoformat()
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def set_phase(phase: str) -> bool:
    """GSD fazını değiştir. Geçersiz fazda False döndür."""
    valid: list[str] = ["discover", "plan", "spec", "execute", "verify", "validate", "ship"]
    if phase not in valid:
        print(f"Invalid phase: {phase}. Use: {', '.join(valid)}", file=sys.stderr)
        return False
    state: StateDict = load()
    if state["phase"] != phase:
        state["phase"] = phase
        state["phase_started"] = datetime.now(TZ).isoformat()
        state["errors_turn"] = 0
        save(state)
        print(f"Phase → {phase}")
    return True


def add_error() -> int:
    """Hata sayacını 1 artır. Dönen değer: turn içindeki hata sayısı."""
    state: StateDict = load()
    state["errors_turn"] += 1
    state["errors_session"] += 1
    save(state)
    print(f"Error #{state['errors_turn']} this turn, #{state['errors_session']} session")
    return state["errors_turn"]


def add_decision(decision: str, reason: str = "",
                 alternatives: Optional[str] = None,
                 outcome: Optional[str] = None) -> None:
    """Karar log'una yeni giriş ekle."""
    state: StateDict = load()
    state["decisions"].append({
        "decision": decision,
        "reason": reason,
        "alternatives": alternatives,
        "outcome": outcome,
        "timestamp": datetime.now(TZ).isoformat(),
    })
    save(state)
    print(f"Decision logged: {decision}")


def inc_tool_calls() -> None:
    """Tool call sayacını 1 artır."""
    state: StateDict = load()
    state["tool_calls_turn"] += 1
    save(state)


def reset_turn() -> None:
    """Turn sayaçlarını sıfırla (hata + tool call)."""
    state: StateDict = load()
    state["errors_turn"] = 0
    state["tool_calls_turn"] = 0
    save(state)


def show() -> None:
    """State'in tamamını göster."""
    state: StateDict = load()
    print(json.dumps(state, indent=2, ensure_ascii=False))


def get_summary() -> str:
    """Her mesaj sonunda çağrılacak 1 satırlık özet."""
    state: StateDict = load()
    budget: float = state["tokens_budget_left"]
    errors: int = state["errors_session"]
    phase: str = state["phase"]
    calls: int = state["tool_calls_turn"]
    task: Optional[str] = state["current_task"]
    if task:
        return f"🧠 {phase.upper()} | hata:{errors} | tool:{calls} | ${budget:.2f} | {task}"
    return f"🧠 {phase.upper()} | hata:{errors} | tool:{calls} | ${budget:.2f}"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Brain v3 State Manager",
        usage="brain-state.py [show|set-phase|add-error|add-decision|reset|summary]"
    )
    parser.add_argument("command", nargs="?",
                        choices=["show", "set-phase", "add-error", "add-decision", "reset", "summary"],
                        help="Yapılacak işlem")
    parser.add_argument("args", nargs="*", help="Komut argümanları")

    parsed = parser.parse_args()

    if not parsed.command:
        parser.print_help()
        sys.exit(1)

    cmd: str = parsed.command
    args: list[str] = parsed.args

    if cmd == "show":
        show()
    elif cmd == "set-phase":
        if not args:
            print("Hata: set-phase için faz adı gerekli (ör: discover, execute)", file=sys.stderr)
            sys.exit(1)
        set_phase(args[0])
    elif cmd == "add-error":
        add_error()
    elif cmd == "add-decision":
        if not args:
            print("Hata: add-decision için en az karar adı gerekli", file=sys.stderr)
            sys.exit(1)
        decision: str = args[0]
        reason: str = args[1] if len(args) > 1 else ""
        alternatives: Optional[str] = args[2] if len(args) > 2 else None
        add_decision(decision, reason, alternatives)
    elif cmd == "reset":
        save(default_state())
        print("State reset to default")
    elif cmd == "summary":
        print(get_summary())


if __name__ == "__main__":
    main()
