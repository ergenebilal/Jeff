#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON="${PYTHON:-python3}"

"$PYTHON" - <<'PY'
import json
import tempfile
import threading
import time
import urllib.request
from http.server import HTTPServer
from pathlib import Path

from brain import close_topic, get_active_topic, list_topics, new_topic
import brain.context_manager as cm
import brain.n8n_gate as gate
from hq.server import HQAPIHandler

tmp = Path(tempfile.mkdtemp(prefix="hermes-smoke-"))
cm.CONTEXT_EVENTS_PATH = tmp / "topics.jsonl"
cm.CONTEXT_STATE_PATH = tmp / "topics_state.json"
gate.GATE_PATH = tmp / "n8n_gate.json"
gate.LOG_PATH = tmp / "logs" / "n8n_write.log"

topic = new_topic("Smoke test bağlamı", "iş", priority=80, ttl_minutes=10)
assert get_active_topic()["id"] == topic["id"]
closed = close_topic(topic["id"])
assert closed and not closed["active"]
assert list_topics() == []

gate.enable_write(minutes=60, reason="smoke", actor="test")
assert gate.health()["enabled"] is True

server = HTTPServer(("127.0.0.1", 0), HQAPIHandler)
port = server.server_address[1]
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
time.sleep(0.2)

with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/context/active") as handle:
    payload = json.loads(handle.read().decode("utf-8"))
assert "topics" in payload

with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/n8n/health") as handle:
    payload = json.loads(handle.read().decode("utf-8"))
assert "enabled" in payload

with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/baseline/status") as handle:
    payload = json.loads(handle.read().decode("utf-8"))
assert "persona" in payload

with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/persona/status") as handle:
    payload = json.loads(handle.read().decode("utf-8"))
assert "context_line" in payload

server.shutdown()
server.server_close()

print("ALL TESTS PASSED")
PY
