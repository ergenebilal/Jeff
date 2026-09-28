#!/usr/bin/env python3
"""
Alfred Bridge Client — runs on Windows (Alfred).
Polls Jeff's Bridge API for tasks, sends heartbeats, handles task types.

Kurulum (Windows):
  pip install requests
  python alfred_client.py

Ortam değişkenleri (opsiyonel):
  JEFF_API=http://193.164.4.149:7700
  BRIDGE_KEY=cybergene-bridge-2026
"""

import base64
import json
import logging
import os
import platform
import subprocess
import sys
import time
import urllib.parse
import webbrowser
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    print("requests not installed. Run: pip install requests")
    sys.exit(1)

# ── Config ─────────────────────────────────────────────────────────────────────
JEFF_API = os.environ.get("JEFF_API", "http://100.124.217.48:7700")
BRIDGE_KEY = os.environ.get("BRIDGE_KEY", "cybergene-bridge-2026")
POLL_INTERVAL = 10        # seconds between task polls
HEARTBEAT_INTERVAL = 30   # seconds between heartbeats
RETRY_WAIT = 5            # seconds to wait on connection error
VERSION = "1.0.0"

LOG_DIR = Path(os.environ.get("USERPROFILE", os.path.expanduser("~"))) / ".hermes"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = LOG_DIR / "alfred_bridge.log"
DRAFT_DIR = LOG_DIR / "drafts"
DRAFT_DIR.mkdir(parents=True, exist_ok=True)

# ── Logging ────────────────────────────────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("alfred_client")

# ── HTTP session ───────────────────────────────────────────────────────────────
session = requests.Session()
session.headers.update({
    "X-Bridge-Key": BRIDGE_KEY,
    "Content-Type": "application/json",
    "User-Agent": f"AlfredClient/{VERSION}",
})


def _post(path: str, data: dict) -> bool:
    try:
        r = session.post(f"{JEFF_API}{path}", json=data, timeout=15)
        r.raise_for_status()
        return True
    except Exception as exc:
        log.error("POST %s failed: %s", path, exc)
        return False


def _get(path: str, timeout: int = 35) -> dict | None:
    try:
        r = session.get(f"{JEFF_API}{path}", timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as exc:
        log.error("GET %s failed: %s", path, exc)
        return None


# ── Task handlers ──────────────────────────────────────────────────────────────
def handle_whatsapp_draft(task: dict):
    """Open native WhatsApp Windows App with message text."""
    payload = _parse_payload(task)
    text = payload.get("text") or payload.get("message") or payload.get("result") or json.dumps(payload)
    phone = payload.get("phone") or payload.get("to") or ""
    task_id = task["task_id"]

    draft_file = DRAFT_DIR / f"{task_id}.txt"
    draft_file.write_text(text, encoding="utf-8")

    encoded_text = urllib.parse.quote(text)
    clean_phone = "".join(c for c in str(phone) if c.isdigit())
    if clean_phone and not clean_phone.startswith("90") and len(clean_phone) == 10:
        clean_phone = "90" + clean_phone

    if clean_phone:
        url = f"whatsapp://send?phone={clean_phone}&text={encoded_text}"
    else:
        url = f"whatsapp://send?text={encoded_text}"

    # Open native Windows WhatsApp Desktop application (NO Web Browser)
    try:
        if platform.system() == "Windows" and hasattr(os, "startfile"):
            os.startfile(url)
        else:
            webbrowser.open(url)
        log.info("WHATSAPP_NATIVE_APP_OPENED  task_id=%s  url=%s", task_id, url)
    except Exception as exc:
        log.error("WHATSAPP_NATIVE_OPEN_FAIL  task_id=%s  exc=%s", task_id, exc)

    print("\n" + "=" * 60)
    print("[WHATSAPP WINDOWS UYGULAMASI] — Masaüstü App Açılıyor:")
    print("-" * 60)
    print(f"Alıcı   : {payload.get('recipient', clean_phone or 'Varsayılan')}")
    print(f"Mesaj   : {text}")
    print(f"Protokol: {url}")
    print("-" * 60)
    print(f"Kaydedildi: {draft_file}")
    print("=" * 60 + "\n")

    _send_result(task_id, "WHATSAPP_DRAFT", f"Native WhatsApp Windows App opened: {url}")


def handle_screenshot_request(task: dict):
    """Capture full-screen screenshot and send base64 to Jeff."""
    task_id = task["task_id"]
    try:
        try:
            import mss
            with mss.mss() as sct:
                img = sct.grab(sct.monitors[0])
                from mss.tools import to_png
                png_bytes = to_png(img.rgb, img.size)
        except ImportError:
            from PIL import ImageGrab
            import io
            img = ImageGrab.grab()
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            png_bytes = buf.getvalue()

        b64 = base64.b64encode(png_bytes).decode()
        log.info("SCREENSHOT  task_id=%s  size=%d bytes", task_id, len(png_bytes))

        _post("/alfred/result", {
            "task_id": task_id,
            "type": "SCREENSHOT_REQUEST",
            "result": "screenshot captured",
            "screenshot_b64": b64,
            "timestamp": _now(),
        })
    except Exception as exc:
        log.error("SCREENSHOT_FAIL  task_id=%s  exc=%s", task_id, exc)
        _send_result(task_id, "SCREENSHOT_REQUEST", f"ERROR: {exc}")


def handle_aider_result_notify(task: dict):
    """Log Aider completion notification."""
    payload = _parse_payload(task)
    task_id = task["task_id"]
    status = payload.get("status", "unknown")
    preview = payload.get("result_preview", "")

    log.info("AIDER_NOTIFY  task_id=%s  status=%s", task_id, status)
    print("\n" + "=" * 60)
    print(f"[AIDER TASK COMPLETE] — {task_id}")
    print(f"    Status : {status}")
    print(f"    Preview: {preview[:200]}")
    print("=" * 60 + "\n")
    _send_result(task_id, "AIDER_RESULT_NOTIFY", "acknowledged")


def handle_browser_action(task: dict):
    """Open a URL in the default browser."""
    payload = _parse_payload(task)
    url = payload.get("url", "")
    task_id = task["task_id"]

    if url:
        webbrowser.open(url)
        log.info("BROWSER_OPEN  task_id=%s  url=%s", task_id, url)
        _send_result(task_id, "BROWSER_ACTION", f"Opened: {url}")
    else:
        log.warning("BROWSER_ACTION  task_id=%s  no url in payload", task_id)
        _send_result(task_id, "BROWSER_ACTION", "ERROR: no url provided")


HANDLERS = {
    "WHATSAPP_DRAFT": handle_whatsapp_draft,
    "SCREENSHOT_REQUEST": handle_screenshot_request,
    "AIDER_RESULT_NOTIFY": handle_aider_result_notify,
    "BROWSER_ACTION": handle_browser_action,
}


# ── Helpers ────────────────────────────────────────────────────────────────────
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_payload(task: dict) -> dict:
    raw = task.get("payload") or "{}"
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return {"raw": raw}


def _send_result(task_id: str, type_: str, result: str):
    _post("/alfred/result", {
        "task_id": task_id,
        "type": type_,
        "result": result,
        "timestamp": _now(),
    })


def _consume_task(task_id: str):
    """Mark task as consumed so it won't be fetched again."""
    _post("/alfred/result", {
        "task_id": task_id,
        "type": "CONSUMED",
        "result": "consumed",
        "timestamp": _now(),
    })


# ── Main loops ─────────────────────────────────────────────────────────────────
PROCESSED_TASK_IDS = set()


def poll_tasks():
    data = _get("/alfred/tasks?timeout=25", timeout=30)
    if not data:
        return 0
    tasks = data.get("tasks", [])
    count = 0
    for task in tasks:
        task_id = task.get("task_id")
        task_type = task.get("type", "UNKNOWN")

        if not task_id or task_id in PROCESSED_TASK_IDS:
            continue
        PROCESSED_TASK_IDS.add(task_id)
        count += 1

        log.info("TASK_RECEIVED  task_id=%s  type=%s", task_id, task_type)
        handler = HANDLERS.get(task_type)
        if handler:
            try:
                handler(task)
            except Exception as exc:
                log.error("HANDLER_ERROR  task_id=%s  type=%s  exc=%s", task_id, task_type, exc)
                _send_result(task_id, task_type, f"ERROR: {exc}")
        else:
            log.warning("UNKNOWN_TASK_TYPE  type=%s", task_type)
        _consume_task(task_id)
    return count


def send_heartbeat():
    _post("/alfred/heartbeat", {
        "agent": "alfred",
        "status": "ok",
        "version": VERSION,
        "timestamp": _now(),
    })
    log.debug("Heartbeat sent")


def main():
    log.info("Alfred Bridge Client v%s (Instant Long-Polling) starting", VERSION)
    log.info("Jeff API : %s", JEFF_API)
    log.info("Log file : %s", LOG_PATH)
    log.info("Platform : %s %s", platform.system(), platform.release())

    last_heartbeat = 0.0

    while True:
        try:
            now = time.monotonic()

            if now - last_heartbeat >= HEARTBEAT_INTERVAL:
                send_heartbeat()
                last_heartbeat = now

            processed = poll_tasks()
            # If no tasks processed or timeout reached, sleep tiny fraction to avoid spinning
            if processed == 0:
                time.sleep(0.5)

        except KeyboardInterrupt:
            log.info("Interrupted by user. Exiting.")
            break
        except Exception as exc:
            log.error("Main loop error: %s — retrying in %ds", exc, RETRY_WAIT)
            time.sleep(RETRY_WAIT)


if __name__ == "__main__":
    main()
