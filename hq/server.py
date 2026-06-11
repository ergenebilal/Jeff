#!/usr/bin/env python3
"""Hermes HQ command center — local-only status panel."""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path("/opt/hermes/hq")
if "/opt/hermes" not in sys.path:
    sys.path.insert(0, "/opt/hermes")


def _payload() -> dict:
    try:
        from brain import generate_brain_health_report, get_relevant_context
        health = generate_brain_health_report()
        context = get_relevant_context("hq")
    except Exception as exc:
        health = {"status": "degraded", "error": str(exc)}
        context = ""
    return {
        "status": health.get("status", "unknown"),
        "health": health,
        "context": context,
        "tokens": {"daily": 0, "session": 0},
        "decisions": [],
    }


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, obj: dict, code: int = 200) -> None:
        body = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self) -> None:
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):  # noqa: N802
        payload = _payload()
        if self.path in {"/", "/index.html"}:
            return self._send_html()
        if self.path in {"/api/status", "/api/health", "/api/tokens", "/api/decisions"}:
            return self._send_json(payload)
        return self._send_json({"error": "not found"}, 404)

    def log_message(self, fmt, *args):  # noqa: A003
        return


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    port = int(argv[0]) if argv else 8889
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Hermes HQ listening on http://127.0.0.1:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
