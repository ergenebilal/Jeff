#!/usr/bin/env python3
import json, os, subprocess
from datetime import datetime

HERMES = os.path.expanduser("~/.hermes")
MEMORY_FILE = os.path.join(HERMES, "memory.json")
MEMORY_DIR = os.path.join(HERMES, "memory")
SESSION_DIR = os.path.join(HERMES, "sessions")
SESSIONS_JSON = os.path.join(SESSION_DIR, "sessions.json")

MEMORY_LIMIT_KB = 1024  # 1 MB — %85 threshold referansi

def get_memory_json_stats():
    if not os.path.exists(MEMORY_FILE):
        return None
    size_kb = os.path.getsize(MEMORY_FILE) / 1024
    with open(MEMORY_FILE) as f:
        data = json.load(f)
    lessons = data.get("lessons", [])
    timestamps = []
    for l in lessons:
        ts = l.get("timestamp", "")
        if ts:
            timestamps.append(ts)
    oldest = min(timestamps) if timestamps else "-"
    newest = max(timestamps) if timestamps else "-"
    return {
        "size_kb": size_kb,
        "lesson_count": len(lessons),
        "oldest": oldest,
        "newest": newest,
    }

def get_session_count():
    if not os.path.exists(SESSIONS_JSON):
        return 0
    with open(SESSIONS_JSON) as f:
        data = json.load(f)
    return len(data) if isinstance(data, dict) else 0

def get_session_request_count():
    if not os.path.exists(SESSION_DIR):
        return 0
    return len([f for f in os.listdir(SESSION_DIR) if f.startswith("request_dump_")])

def check_disk_usage_pct():
    try:
        res = subprocess.run(
            ["df", "--output=pcent", HERMES],
            capture_output=True, text=True, timeout=5
        )
        lines = res.stdout.strip().split("\n")
        if len(lines) >= 2:
            return lines[1].strip().replace("%", "")
    except:
        pass
    return None

def main():
    mem = get_memory_json_stats()
    session_count = get_session_count()
    request_count = get_session_request_count()
    disk_pct = check_disk_usage_pct()

    print(f"memory.json: {mem['size_kb']:.1f} KB" if mem else "memory.json: yok")
    print(f"lessons: {mem['lesson_count']} adet" if mem else "lessons: -")
    print(f"en eski kayit: {mem['oldest']}" if mem else "")
    print(f"en yeni kayit: {mem['newest']}" if mem else "")
    print(f"sessions.json: {session_count} session")
    print(f"request_dump dosyasi: {request_count} adet")
    print(f"disk kullanimi: %{disk_pct}" if disk_pct else "disk: bilinmiyor")

    if os.path.exists(MEMORY_DIR):
        memdir_files = os.listdir(MEMORY_DIR)
        print(f"~/.hermes/memory/ icinde {len(memdir_files)} dosya")

    if os.path.exists(HERMES):
        hermes_files = len(os.listdir(HERMES))
        print(f"~/.hermes/ toplam: {hermes_files} ogeler")

    mem_usage_ratio = (mem["size_kb"] / MEMORY_LIMIT_KB) if mem else 0
    if mem_usage_ratio >= 0.85:
        print("UYARI: Memory dolu (%{:.0f})".format(mem_usage_ratio * 100))

if __name__ == "__main__":
    main()
