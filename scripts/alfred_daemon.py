#!/usr/bin/env python3
"""
CyberGene Alfred Daemon v2.0 — Alfred (Windows) tarafinda calisir.

Gorevler:
  - HTTP server (port 7788): Jeff'ten gorev alir
  - Outbox polling (5sn): dosya fallback icin outbox/ klasorunu izler
  - Gorev isleme: PING, SCREENSHOT, WHATSAPP_SEND, TELEGRAM_REPORT
  - Yanit gonderme: Jeff'e HTTP ile geri gonderir (port 7789)

Kurulum (Windows):
  python alfred_daemon.py

Ortam degiskenleri (opsiyonel):
  TELEGRAM_BOT_TOKEN  — Telegram bot token
  TELEGRAM_CHAT_ID    — Bilal'in chat ID'si
  JEFF_HOST           — Jeff'in IP'si (varsayilan: 13.140.183.88)
  BRIDGE_DIR          — Kopru klasoru (varsayilan: ~/.hermes/alfred_bridge)
"""

import os
import sys
import json
import time
import uuid
import logging
import threading
import urllib.request
import urllib.error
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler

# Platform tespiti
IS_WINDOWS = sys.platform == "win32"

# Logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="[%(asctime)s] [Alfred] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("alfred_daemon")

# Paths
BRIDGE_DIR  = Path(os.environ.get("BRIDGE_DIR", os.path.expanduser("~/.hermes/alfred_bridge")))
OUTBOX_DIR  = BRIDGE_DIR / "outbox"
INBOX_DIR   = BRIDGE_DIR / "inbox"

# Network config
LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 7788

JEFF_HOST         = os.environ.get("JEFF_HOST", "13.140.183.88")
JEFF_RESPONSE_URL = f"http://{JEFF_HOST}:7789/response"

HTTP_TIMEOUT  = 5
POLL_INTERVAL = 5  # saniye


def init_dirs():
    OUTBOX_DIR.mkdir(parents=True, exist_ok=True)
    INBOX_DIR.mkdir(parents=True, exist_ok=True)


# Gorev isleyicileri

def handle_ping(task: dict) -> dict:
    log.info(f"[PING] task_id={task.get('task_id')}")
    return {"result": "PONG", "status": "DONE"}


def handle_screenshot(task: dict) -> dict:
    """Ekran goruntusu alir, inbox'a kaydeder."""
    try:
        import subprocess
        ts = time.strftime("%Y%m%d_%H%M%S")
        out_path = str(INBOX_DIR / f"screenshot_{ts}.png")

        if IS_WINDOWS:
            ps_cmd = (
                "Add-Type -AssemblyName System.Windows.Forms,System.Drawing; "
                "$s=[System.Windows.Forms.Screen]::PrimaryScreen; "
                "$b=New-Object System.Drawing.Bitmap($s.Bounds.Width,$s.Bounds.Height); "
                "$g=[System.Drawing.Graphics]::FromImage($b); "
                "$g.CopyFromScreen($s.Bounds.Location,[System.Drawing.Point]::Empty,$s.Bounds.Size); "
                f"$b.Save('{out_path}')"
            )
            subprocess.run(["powershell", "-Command", ps_cmd], timeout=15, check=True, capture_output=True)
        else:
            subprocess.run(["scrot", out_path], timeout=10, check=True, capture_output=True)

        log.info(f"[SCREENSHOT] Kaydedildi: {out_path}")
        return {"result": "screenshot_saved", "path": out_path, "status": "DONE"}
    except Exception as e:
        log.error(f"[SCREENSHOT] Hata: {e}")
        return {"result": "error", "error": str(e), "status": "FAILED"}


def handle_whatsapp_send(task: dict) -> dict:
    """WhatsApp Web uzerinden mesaj — placeholder (pyautogui/selenium ile genistetilebilir)."""
    payload = task.get("payload", {})
    to      = payload.get("to", "?")
    phone   = payload.get("phone", "?")
    message = payload.get("message", "")
    log.info(f"[WHATSAPP] -> {to} ({phone}): {message[:60]}")
    return {
        "result": "whatsapp_queued",
        "to": to,
        "phone": phone,
        "status": "DONE",
        "note": "Placeholder — gercek gonderim icin pyautogui entegre edilmeli.",
    }


def handle_telegram_report(task: dict) -> dict:
    """Jeff'e Telegram bot uzerinden rapor gonderir."""
    payload = task.get("payload", {})
    text    = payload.get("text", "")
    token   = payload.get("bot_token", os.environ.get("TELEGRAM_BOT_TOKEN", ""))
    chat_id = payload.get("chat_id", os.environ.get("TELEGRAM_CHAT_ID", ""))

    if not token or not chat_id:
        log.warning("[TELEGRAM] bot_token veya chat_id eksik.")
        return {"result": "error", "error": "missing credentials", "status": "FAILED"}

    try:
        tg_url = f"https://api.telegram.org/bot{token}/sendMessage"
        body   = json.dumps({"chat_id": chat_id, "text": text}, ensure_ascii=False).encode("utf-8")
        req    = urllib.request.Request(tg_url, data=body,
                     headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            log.info(f"[TELEGRAM] Gönderildi: ok={result.get('ok')}")
            return {"result": "sent", "ok": result.get("ok"), "status": "DONE"}
    except Exception as e:
        log.error(f"[TELEGRAM] Hata: {e}")
        return {"result": "error", "error": str(e), "status": "FAILED"}


TASK_HANDLERS = {
    "PING":            handle_ping,
    "SCREENSHOT":      handle_screenshot,
    "WHATSAPP_SEND":   handle_whatsapp_send,
    "WHATSAPP_DRAFT":  handle_whatsapp_send,   # v1 uyumlulugu
    "TELEGRAM_REPORT": handle_telegram_report,
}


def send_response_to_jeff(task: dict, result: dict):
    """Sonucu HTTP ile Jeff'e gonderir; basarisiz olursa inbox'a yazar."""
    response = {
        "task_id":      task.get("task_id"),
        "type":         task.get("type"),
        "result":       result,
        "responded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }

    # HTTP yolu
    try:
        body = json.dumps(response, ensure_ascii=False).encode("utf-8")
        req  = urllib.request.Request(
            JEFF_RESPONSE_URL, data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
            log.info(f"[-> Jeff HTTP] Yanit gonderildi: {task.get('task_id')} status={resp.status}")
            return
    except Exception as e:
        log.warning(f"[-> Jeff HTTP] Basarisiz, inbox'a yaziliyor: {e}")

    # Dosya fallback
    resp_file = INBOX_DIR / f"resp_{task.get('task_id', str(uuid.uuid4()))}.json"
    with open(str(resp_file), "w", encoding="utf-8") as f:
        json.dump(response, f, ensure_ascii=False, indent=2)
    log.info(f"[-> Inbox] Yanit kaydedildi: {resp_file}")


def process_task(task: dict):
    task_id   = task.get("task_id", "?")
    task_type = task.get("type", "UNKNOWN")
    log.info(f"[TASK] Isleniyor: {task_id} ({task_type})")

    handler = TASK_HANDLERS.get(task_type)
    if handler is None:
        log.warning(f"[TASK] Bilinmeyen tip: {task_type}")
        result = {"result": "error", "error": f"unknown task type: {task_type}", "status": "FAILED"}
    else:
        try:
            result = handler(task)
        except Exception as e:
            log.error(f"[TASK] Handler hatasi ({task_type}): {e}")
            result = {"result": "error", "error": str(e), "status": "FAILED"}

    send_response_to_jeff(task, result)


# HTTP Server (port 7788)

class AlfredHTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        log.info(f"[HTTP] {fmt % args}")

    def _send_json(self, code: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"status": "ok", "agent": "alfred_daemon", "version": "2.0"})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/task":
            try:
                length = int(self.headers.get("Content-Length", 0))
                raw    = self.rfile.read(length).decode("utf-8")
                task   = json.loads(raw)
                t = threading.Thread(target=process_task, args=(task,), daemon=True)
                t.start()
                self._send_json(202, {"status": "accepted", "task_id": task.get("task_id")})
            except Exception as e:
                log.error(f"[HTTP POST /task] Hata: {e}")
                self._send_json(400, {"error": str(e)})
        else:
            self._send_json(404, {"error": "not found"})


def run_http_server():
    server = HTTPServer((LISTEN_HOST, LISTEN_PORT), AlfredHTTPHandler)
    log.info(f"Alfred HTTP server baslatildi: {LISTEN_HOST}:{LISTEN_PORT}")
    try:
        server.serve_forever()
    except Exception as e:
        log.error(f"HTTP server durdu: {e}")


# Outbox Polling (dosya fallback)

_processed_ids: set = set()


def poll_outbox():
    """OUTBOX_DIR'i periyodik tarar, yeni gorevleri isler."""
    log.info(f"Outbox polling baslatildi: {OUTBOX_DIR} (her {POLL_INTERVAL}sn)")
    while True:
        try:
            for fpath in sorted(OUTBOX_DIR.iterdir()):
                if fpath.suffix != ".json":
                    continue
                task_id = fpath.stem
                if task_id in _processed_ids:
                    continue
                try:
                    with open(str(fpath), "r", encoding="utf-8") as f:
                        task = json.load(f)
                    status = task.get("status", "")
                    if status in ("SENT_VIA_HTTP", "DONE", "FAILED"):
                        _processed_ids.add(task_id)
                        continue
                    _processed_ids.add(task_id)
                    t = threading.Thread(target=process_task, args=(task,), daemon=True)
                    t.start()
                except Exception as e:
                    log.error(f"Outbox dosyasi okunamadi ({fpath.name}): {e}")
        except Exception as e:
            log.error(f"Outbox polling hatasi: {e}")
        time.sleep(POLL_INTERVAL)


def main():
    init_dirs()
    log.info("=" * 60)
    log.info("CyberGene Alfred Daemon v2.0 baslatiliyor...")
    log.info(f"Platform: {sys.platform}")
    log.info(f"Bridge dir: {BRIDGE_DIR}")
    log.info(f"Jeff response URL: {JEFF_RESPONSE_URL}")
    log.info("=" * 60)

    # HTTP server — ayri thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()

    # Outbox polling — ana thread
    try:
        poll_outbox()
    except KeyboardInterrupt:
        log.info("Alfred Daemon durduruluyor (Ctrl+C)...")
        sys.exit(0)


if __name__ == "__main__":
    main()
