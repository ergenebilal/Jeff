#!/usr/bin/env python3
"""
CyberGene Alfred Response Receiver v2.0 — Jeff (Ubuntu) tarafinda calisir.

Alfred'den gelen HTTP yanitlari alir, inbox/ klasorune kaydeder.

Endpoints:
  POST /response  — Alfred'in yanitini alir
  GET  /health    — saglik kontrolu

Calistirma:
  python3 alfred_response_receiver.py
  veya systemd: alfred-response-receiver.service
"""

import os
import sys
import json
import time
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler

# Logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="[%(asctime)s] [ResponseReceiver] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("alfred_response_receiver")

# Paths
BRIDGE_QUEUE_DIR = os.path.expanduser("~/.hermes/alfred_bridge")
INBOX_DIR        = os.path.join(BRIDGE_QUEUE_DIR, "inbox")
os.makedirs(INBOX_DIR, exist_ok=True)

# Network config
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 7789


class ResponseReceiverHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        log.info(f"[HTTP] {self.client_address[0]} — {fmt % args}")

    def _send_json(self, code: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            inbox_count = len([f for f in os.listdir(INBOX_DIR) if f.endswith(".json")])
            self._send_json(200, {
                "status": "ok",
                "agent":  "alfred_response_receiver",
                "version": "2.0",
                "inbox_count": inbox_count,
            })
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/response":
            try:
                length   = int(self.headers.get("Content-Length", 0))
                raw      = self.rfile.read(length).decode("utf-8")
                response = json.loads(raw)

                task_id  = response.get("task_id", f"unknown_{int(time.time())}")
                fname    = os.path.join(INBOX_DIR, f"resp_{task_id}.json")

                with open(fname, "w", encoding="utf-8") as f:
                    json.dump(response, f, ensure_ascii=False, indent=2)

                log.info(f"[SAVED] Alfred yaniti kaydedildi: {fname}")
                self._send_json(200, {"status": "saved", "task_id": task_id})
            except Exception as e:
                log.error(f"[POST /response] Hata: {e}")
                self._send_json(400, {"error": str(e)})
        else:
            self._send_json(404, {"error": "not found"})


def main():
    server = HTTPServer((LISTEN_HOST, LISTEN_PORT), ResponseReceiverHandler)
    log.info(f"Alfred Response Receiver baslatildi: {LISTEN_HOST}:{LISTEN_PORT}")
    log.info(f"Inbox: {INBOX_DIR}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Response Receiver durduruluyor...")
        sys.exit(0)


if __name__ == "__main__":
    main()
