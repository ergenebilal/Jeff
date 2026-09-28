#!/usr/bin/env python3
"""
File Watcher — kritik dosyaları izler, değişiklikleri raporlar.
Lean & Mean: sadece stat + sha256, harici bağımlılık yok.
Her 30 dk'da bir çalışır (cron), sadece değişiklik varsa OUTPUT üretir.
"""

import hashlib
import json
import os
import stat as stat_module
from pathlib import Path

HERMES_HOME = Path.home() / ".hermes"
BASELINE_FILE = HERMES_HOME / "data" / "file_watcher_baseline.json"

WATCHED_FILES = [
    HERMES_HOME / ".env",
    HERMES_HOME / "config.yaml",
    HERMES_HOME / "internal_log.json",
    HERMES_HOME / "state.db",
    HERMES_HOME / "config.yaml",
]

WATCHED_DIRS = [
    HERMES_HOME / "skills",
    HERMES_HOME / "cron",
]


def sha256_file(path: Path) -> str | None:
    """Read file and return SHA256 hex digest. Returns None if file doesn't exist."""
    if not path.exists():
        return None
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except (OSError, PermissionError):
        return None


def get_file_state(path: Path) -> dict:
    """Get current state of a file: size, mtime, hash."""
    if not path.exists():
        return {"exists": False, "size": 0, "mtime": 0, "hash": None}
    st = path.stat()
    return {
        "exists": True,
        "size": st.st_size,
        "mtime": st.st_mtime_ns,
        "hash": sha256_file(path),
    }


def load_baseline() -> dict:
    """Load previous baseline from disk."""
    if BASELINE_FILE.exists():
        try:
            return json.loads(BASELINE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_baseline(state: dict) -> None:
    """Save current state as new baseline."""
    BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def check_skills_count() -> dict:
    """Count skills and report any changes."""
    skills_dir = HERMES_HOME / "skills"
    if not skills_dir.exists():
        return {"count": 0, "dirs": []}
    dirs = sorted([d.name for d in skills_dir.iterdir() if d.is_dir()])
    return {"count": len(dirs), "dirs": dirs}


def main() -> None:
    baseline = load_baseline()
    current_state = {}
    changes = []

    # Monitor individual files
    for path in WATCHED_FILES:
        rel = str(path.relative_to(HERMES_HOME))
        state = get_file_state(path)
        current_state[rel] = state

        if rel in baseline:
            prev = baseline[rel]
            if state["hash"] != prev.get("hash"):
                changes.append(
                    f"🔴 DEĞİŞİKLİK: {rel}\n"
                    f"   Önce: {prev.get('size', 0)} bytes, hash={prev.get('hash', '')[:16]}...\n"
                    f"   Şimdi: {state['size']} bytes, hash={state['hash'][:16] if state['hash'] else 'N/A'}..."
                )
        else:
            if state["exists"]:
                changes.append(f"🆕 YENİ: {rel} ({state['size']} bytes)")

    # Monitor skills directory
    skills_state = check_skills_count()
    current_state["_skills"] = skills_state
    if "_skills" in baseline:
        prev_count = baseline["_skills"].get("count", 0)
        if skills_state["count"] != prev_count:
            changes.append(
                f"📂 SKILL SAYISI DEĞİŞTİ: {prev_count} → {skills_state['count']}"
            )
            added = set(skills_state["dirs"]) - set(
                baseline["_skills"].get("dirs", [])
            )
            removed = set(baseline["_skills"].get("dirs", [])) - set(
                skills_state["dirs"]
            )
            if added:
                changes.append(f"   ➕ Eklenen: {', '.join(sorted(added))}")
            if removed:
                changes.append(f"   ➖ Silinen: {', '.join(sorted(removed))}")

    save_baseline(current_state)

    # Monitor state.db büyümesi (genel sağlık)
    state_db = HERMES_HOME / "state.db"
    if state_db.exists():
        size_mb = state_db.stat().st_size / (1024 * 1024)
        current_state["_state_db_size_mb"] = round(size_mb, 1)

    # Output only if changes detected
    if changes:
        report = "🔍 **File Watcher Raporu**\n\n" + "\n\n".join(changes)

        # Add state.db size info
        if "_state_db_size_mb" in current_state:
            report += f"\n\n📊 state.db: {current_state['_state_db_size_mb']} MB"

        print(report)
    else:
        # Silent — nothing changed
        pass


if __name__ == "__main__":
    main()
