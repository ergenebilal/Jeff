#!/usr/bin/env python3
import json, os, shutil, sqlite3
from datetime import datetime, timedelta, timezone

HERMES = os.path.expanduser("~/.hermes")
MEMORY_FILE = os.path.join(HERMES, "memory.json")
SESSIONS_DB = os.path.join(HERMES, "sessions.db")
SESSION_DIR = os.path.join(HERMES, "sessions")
SESSIONS_JSON = os.path.join(SESSION_DIR, "sessions.json")
ARCHIVE_DIR = os.path.join(HERMES, "sessions-archive")
CUTOFF = datetime.now(timezone.utc) - timedelta(days=7)

os.makedirs(ARCHIVE_DIR, exist_ok=True)

def memory_json_size_kb() -> float:
    if not os.path.exists(MEMORY_FILE):
        return 0.0
    return os.path.getsize(MEMORY_FILE) / 1024

def sessions_db_exists() -> bool:
    return os.path.exists(SESSIONS_DB)

def count_session_entries() -> int:
    if not os.path.exists(SESSIONS_JSON):
        return 0
    with open(SESSIONS_JSON) as f:
        data = json.load(f)
    return len(data) if isinstance(data, dict) else 0

def archive_old_sessions() -> int:
    if not os.path.exists(SESSIONS_JSON):
        return 0
    with open(SESSIONS_JSON) as f:
        sessions = json.load(f)

    kept = {}
    archived_count = 0
    for key, session in sessions.items():
        updated_str = session.get("updated_at") or session.get("created_at", "")
        if not updated_str:
            kept[key] = session
            continue
        try:
            updated = datetime.fromisoformat(updated_str)
            if updated.tzinfo is None:
                updated = updated.replace(tzinfo=timezone.utc)
        except:
            kept[key] = session
            continue

        is_completed = session.get("expiry_finalized", False)
        if updated < CUTOFF and is_completed:
            archive_path = os.path.join(ARCHIVE_DIR, f"session_{key.replace(':', '_')}.json")
            with open(archive_path, "w") as f:
                json.dump(session, f, indent=2, ensure_ascii=False)
            archived_count += 1
        else:
            kept[key] = session

    with open(SESSIONS_JSON, "w") as f:
        json.dump(kept, f, indent=2, ensure_ascii=False)
    return archived_count

def archive_old_request_dumps() -> int:
    count = 0
    if not os.path.exists(SESSION_DIR):
        return 0
    for fname in os.listdir(SESSION_DIR):
        if not fname.startswith("request_dump_"):
            continue
        fpath = os.path.join(SESSION_DIR, fname)
        mtime = datetime.fromtimestamp(os.path.getmtime(fpath), tz=timezone.utc)
        if mtime < CUTOFF:
            shutil.move(fpath, os.path.join(ARCHIVE_DIR, fname))
            count += 1
    return count

def main():
    mem_size = memory_json_size_kb()
    db_ok = "var" if sessions_db_exists() else "yok"
    session_count = count_session_entries()

    archived_sessions = archive_old_sessions()
    archived_dumps = archive_old_request_dumps()
    total_archived = archived_sessions + archived_dumps

    print(f"memory.json {mem_size:.1f} KB, sessionlar {session_count} adet, {total_archived} adet archive edildi")

if __name__ == "__main__":
    main()
