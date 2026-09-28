#!/usr/bin/env python3
"""Kanban zombie task detection script for cron.

Her 15 dakikada bir çalışır, 30dk+ running task'leri tespit eder.
"""
import json, subprocess, sys, time
from datetime import datetime
from pathlib import Path

HERMES = str(Path.home() / ".local" / "bin" / "hermes")
ZOMBIE_TIMEOUT = 30  # dakika

def run_kanban(*args):
    return subprocess.run([HERMES, "kanban", *args], capture_output=True, text=True, timeout=15)

# Running task'leri al
result = run_kanban("list", "--status", "running", "--json")
if result.returncode != 0:
    sys.exit(0)

try:
    tasks = json.loads(result.stdout.strip())
except json.JSONDecodeError:
    sys.exit(0)

if not tasks:
    sys.exit(0)  # sessiz çık

now = time.time()
zombies = []
for task in tasks:
    started = task.get("started_at")
    if not started:
        continue
    try:
        if isinstance(started, str):
            ts = datetime.fromisoformat(started).timestamp()
        else:
            ts = float(started)
        elapsed = (now - ts) / 60
        if elapsed > ZOMBIE_TIMEOUT:
            zombies.append({
                "id": task["id"], "title": task.get("title","?")[:60],
                "assignee": task.get("assignee","?"), "elapsed_min": round(elapsed)
            })
    except Exception:
        continue

if zombies:
    print(f"ZOMBIE: {len(zombies)} stuck task(s)")
    for z in zombies:
        print(f"  ☠️ {z['id']} | {z['title']} | {z['assignee']} | {z['elapsed_min']}dk")
else:
    # sessiz — sadece zombie varsa bildir
    pass
