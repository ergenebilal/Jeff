#!/usr/bin/env python3
"""ErgeneAI Komuta Merkezi backend. Localhost-only HTTP API."""

import json
import os
import shlex
import socket
import subprocess
import sys
from datetime import datetime, timezone
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse


HQ = Path(__file__).resolve().parent
ROOT = HQ.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class HQAPIHandler(SimpleHTTPRequestHandler):
    _command_history = []

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._json_response(self._build_health())
        elif parsed.path == "/api/tokens":
            self._json_response(self._build_tokens())
        elif parsed.path == "/api/decisions":
            self._json_response(self._build_decisions())
        elif parsed.path == "/api/status":
            self._json_response(self._build_full_status())
        elif parsed.path == "/api/command-history":
            self._json_response({"commands": self._command_history[-10:]})
        elif parsed.path in {"", "/"}:
            self._serve_html()
        else:
            self._json_response({"error": "not_found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        data = self._read_json_body()
        if parsed.path == "/api/command":
            payload, status = _run_allowed_command(str(data.get("command", "")).strip())
            if status == 200:
                self._command_history.append(
                    {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "command": payload.get("command"),
                        "exit_code": payload.get("exit_code"),
                    }
                )
            self._json_response(payload, status)
        elif parsed.path == "/api/token-limit":
            payload, status = _handle_token_limit(data)
            self._json_response(payload, status)
        else:
            self._json_response({"error": "not_found"}, 404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:8889")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", 0))
        if not content_length:
            return {}
        try:
            raw = self.rfile.read(content_length).decode("utf-8")
            data = json.loads(raw) if raw else {}
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:8889")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8"))

    def _serve_html(self):
        index = HQ / "index.html"
        if not index.exists():
            self._json_response({"error": "index.html not found"}, 500)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(index.read_bytes())

    @staticmethod
    def _build_health() -> dict:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "gateway": _systemd_active("hermes-gateway.service"),
                "embedding": _port_open("127.0.0.1", 8767),
                "headroom": _port_open("127.0.0.1", 8787),
                "n8n": _port_open("127.0.0.1", 5678),
            },
            "system": {
                "memory": _memory(),
                "disk": _disk(),
            },
        }

    @staticmethod
    def _build_tokens() -> dict:
        try:
            from brain.token import TokenGuard, get_budget_left, get_daily_usage

            return {
                "guard": TokenGuard.check(),
                "budget_left": get_budget_left(),
                "daily": get_daily_usage(),
            }
        except Exception:
            return {"error": "token data unavailable"}

    @staticmethod
    def _build_decisions() -> list:
        try:
            from brain.reasoning_tree import get_recent

            return get_recent(10)
        except Exception:
            return []

    @staticmethod
    def _build_full_status() -> dict:
        decisions = HQAPIHandler._build_decisions()
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "health": HQAPIHandler._build_health(),
            "tokens": HQAPIHandler._build_tokens(),
            "decisions": decisions[-5:],
            "decision_count": len(decisions),
        }

    def log_message(self, format, *args):
        return


def _memory() -> dict:
    try:
        mem = {}
        with open("/proc/meminfo", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith(("MemTotal", "MemAvailable")):
                    parts = line.split()
                    mem[parts[0].rstrip(":")] = int(parts[1]) // 1024
        return mem
    except Exception:
        return {}


def _disk() -> dict:
    try:
        st = os.statvfs("/")
        return {
            "total_gb": st.f_frsize * st.f_blocks // (1024**3),
            "free_gb": st.f_frsize * st.f_bfree // (1024**3),
        }
    except Exception:
        return {}


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except Exception:
        return False


def _systemd_active(unit: str) -> bool:
    try:
        result = subprocess.run(
            ["systemctl", "is-active", unit],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        return result.stdout.strip() == "active"
    except Exception:
        return False


ALLOWED_COMMAND_PREFIXES = (
    "systemctl status",
    "systemctl restart hermes",
    "systemctl start hermes",
    "systemctl stop hermes",
    "journalctl -n 30 -u",
    "df -h",
    "free -m",
    "ps aux",
    "uptime",
)


def _run_allowed_command(command: str) -> tuple[dict, int]:
    if not command:
        return {"error": "Komut boş", "command": command}, 400
    if not command.startswith(ALLOWED_COMMAND_PREFIXES):
        return {"error": "Bu komuta izin verilmiyor", "command": command}, 403
    try:
        args = shlex.split(command)
    except ValueError as exc:
        return {"error": str(exc), "command": command}, 400
    try:
        result = subprocess.run(args, capture_output=True, text=True, timeout=10, check=False)
        return {
            "command": command,
            "exit_code": result.returncode,
            "stdout": result.stdout[-1000:],
            "stderr": result.stderr[-500:],
        }, 200
    except subprocess.TimeoutExpired:
        return {"error": "Komut zaman aşımı", "command": command}, 408
    except Exception as exc:
        return {"error": str(exc), "command": command}, 500


def _handle_token_limit(data: dict) -> tuple[dict, int]:
    action = data.get("action", "")
    if action == "reset":
        return {"status": "reset_requested"}, 200
    if action == "set":
        try:
            new_limit = float(data.get("limit", 0.5))
        except (TypeError, ValueError):
            return {"error": "Geçersiz limit"}, 400
        if new_limit <= 0:
            return {"error": "Limit pozitif olmalı"}, 400
        return {"status": "limit_updated", "new_limit": new_limit}, 200
    return {"error": "Geçersiz aksiyon"}, 400


def run(port: int = 8889, host: str = "127.0.0.1"):
    server = HTTPServer((host, port), HQAPIHandler)
    print(f"HQ → http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    import sys

    run(port=int(sys.argv[1]) if len(sys.argv) > 1 else 8889)
