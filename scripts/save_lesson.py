#!/usr/bin/env python3
"""Session lesson saver — runs via cron to consolidate learnings."""
import json, sys, os
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".hermes"))

lessons = []
lesson_file = Path.home() / ".hermes" / "learning" / "lessons.jsonl"
lesson_file.parent.mkdir(parents=True, exist_ok=True)

# If there's a pending lesson file from the session, process it
pending = Path.home() / ".hermes" / "learning" / "pending_lesson.json"
if pending.exists():
    try:
        data = json.loads(pending.read_text())
        with lesson_file.open("a") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
        print(f"✅ Lesson saved: {data.get('trigger', 'unknown')}")
        pending.unlink()
    except Exception as e:
        print(f"❌ Failed to save lesson: {e}")

# Sync to Mnemosyne if available
try:
    import brain
    brain.sync_all_to_mnemosyne()
    print("✅ Synced to Mnemosyne")
except Exception:
    print("⏭️ Mnemosyne sync skipped")
