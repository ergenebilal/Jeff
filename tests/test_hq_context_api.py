import json
import threading
import time
import urllib.request
from http.server import HTTPServer
from pathlib import Path

import brain.context_manager as cm
import brain.n8n_gate as gate
from hq.server import HQAPIHandler


def _start_server():
    server = HTTPServer(("127.0.0.1", 0), HQAPIHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.1)
    return server, server.server_address[1]


def test_hq_context_api_flow(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    cm.CONTEXT_EVENTS_PATH = tmp_path / "topics.jsonl"
    cm.CONTEXT_STATE_PATH = tmp_path / "topics_state.json"
    gate.GATE_PATH = tmp_path / "n8n_write_gate.json"
    gate.LOG_PATH = tmp_path / "logs" / "n8n_write.log"

    topic = cm.new_topic("Denizbank takibi", "iş", priority=80, ttl_minutes=20)
    server, port = _start_server()
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/context/active") as handle:
            payload = json.loads(handle.read().decode("utf-8"))
        assert payload["active_topic"]["id"] == topic["id"]

        with urllib.request.urlopen(
            urllib.request.Request(
                f"http://127.0.0.1:{port}/api/n8n/write_enable",
                data=json.dumps({"minutes": 60, "reason": "test"}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        ) as handle:
            payload = json.loads(handle.read().decode("utf-8"))
        assert payload["enabled"] is True

        with urllib.request.urlopen(
            urllib.request.Request(
                f"http://127.0.0.1:{port}/api/context/close",
                data=json.dumps({"topic_id": topic["id"]}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
        ) as handle:
            payload = json.loads(handle.read().decode("utf-8"))
        assert payload["closed"]["active"] is False

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/persona/status") as handle:
            payload = json.loads(handle.read().decode("utf-8"))
        assert "identity_block" in payload

        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/baseline/status") as handle:
            payload = json.loads(handle.read().decode("utf-8"))
        assert "summary" in payload
    finally:
        server.shutdown()
        server.server_close()


def test_hq_context_close_all(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    cm.CONTEXT_EVENTS_PATH = tmp_path / "topics.jsonl"
    cm.CONTEXT_STATE_PATH = tmp_path / "topics_state.json"
    topic = cm.new_topic("Konu 1", "iş")
    cm.new_topic("Konu 2", "iş")
    server, port = _start_server()
    try:
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/context/close",
            data=json.dumps({"close_all": True}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as handle:
            payload = json.loads(handle.read().decode("utf-8"))
        assert payload["remaining"] == []
    finally:
        server.shutdown()
        server.server_close()

