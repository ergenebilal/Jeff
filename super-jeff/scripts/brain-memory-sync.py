#!/usr/bin/env python3
"""Brain v3 → Mnemosyne sync. Her 15dk'da bir decisions'ları brain.learning'e kaydeder."""
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Any, Optional

sys.path.insert(0, os.path.expanduser("~/.hermes"))

STATE_PATH: str = "/tmp/hermes-brain-state.json"
LAST_SYNC_PATH: str = "/tmp/hermes-brain-sync.txt"
TZ: timezone = timezone(timedelta(hours=3))


def get_last_sync() -> str:
    """Son sync zamanını oku."""
    if not os.path.exists(LAST_SYNC_PATH):
        return "2000-01-01T00:00:00+03:00"
    with open(LAST_SYNC_PATH) as f:
        return f.read().strip()


def set_last_sync(ts: str) -> None:
    """Son sync zamanını kaydet."""
    with open(LAST_SYNC_PATH, "w") as f:
        f.write(ts)


def load_state() -> Optional[dict[str, Any]]:
    """State.json'dan oku, yoksa None."""
    if not os.path.exists(STATE_PATH):
        return None
    try:
        with open(STATE_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def get_unsynced_decisions(state: dict[str, Any], last_sync: str) -> list[dict[str, Any]]:
    """last_sync'ten sonra eklenmiş kararları bul."""
    return [d for d in state.get("decisions", []) if d.get("timestamp", last_sync) > last_sync]


def sync_via_brain_learning(decisions: list[dict[str, Any]]) -> int:
    """Kararları brain.learning.save_lesson() ile kalıcı belleğe yaz."""
    try:
        from brain.learning import save_lesson
    except ImportError:
        print("brain.learning import edilemedi — sync atlanıyor", file=sys.stderr)
        return 0

    count: int = 0
    for d in decisions:
        decision_text: str = d.get("decision", "bilinmeyen karar")
        reason_text: str = d.get("reason", "")
        content: str = f"KARAR: {decision_text}"
        if reason_text:
            content += f" | NEDEN: {reason_text}"
        if d.get("alternatives"):
            content += f" | ALTERNATİF: {d['alternatives']}"
        if d.get("outcome"):
            content += f" | SONUÇ: {d['outcome']}"

        try:
            save_lesson(
                category="decision",
                trigger=decision_text[:80],
                lesson=content[:500],
                importance=0.7,
                source="brain-v3",
            )
            count += 1
        except Exception as e:
            print(f"Sync hatası: {decision_text[:40]}... → {e}", file=sys.stderr)

    return count


def main() -> None:
    last_sync: str = get_last_sync()
    state: Optional[dict[str, Any]] = load_state()

    if not state:
        print(f"State yok: {STATE_PATH}")
        return

    unsynced: list[dict[str, Any]] = get_unsynced_decisions(state, last_sync)

    if not unsynced:
        print(f"Yeni karar yok. Son sync: {last_sync}")
        set_last_sync(datetime.now(TZ).isoformat())
        return

    print(f"Sync edilecek {len(unsynced)} karar:")
    for d in unsynced:
        print(f"  - {d.get('decision', '?')[:60]}")

    synced: int = sync_via_brain_learning(unsynced)
    print(f"✅ {synced}/{len(unsynced)} karar brain.learning'e kaydedildi")

    new_sync: str = datetime.now(TZ).isoformat()
    set_last_sync(new_sync)
    print(f"Sync zamanı: {new_sync}")


if __name__ == "__main__":
    main()
