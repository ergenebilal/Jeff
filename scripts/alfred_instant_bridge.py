#!/usr/bin/env python3
"""
CyberGene Alfred Instant Event Bridge v2.0
Jeff (Ubuntu sunucu) <-> Alfred (Windows yerel) köprüsü.

Transport önceliği:
  1. HTTP -> Alfred HTTP server'ına POST (primary, port 7788)
  2. Dosya -> outbox/ klasörüne JSON yaz (fallback)

v1.0 ile geriye dönük uyumlu (aynı fonksiyon imzaları).
"""

import os
import sys
import json
import time
import uuid
import logging
import urllib.request
import urllib.error

# Logging
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="[%(asctime)s] [Bridge] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger("alfred_bridge")

# Paths
BRIDGE_QUEUE_DIR = os.path.expanduser("~/.hermes/alfred_bridge")
OUTBOX_DIR = os.path.join(BRIDGE_QUEUE_DIR, "outbox")
INBOX_DIR  = os.path.join(BRIDGE_QUEUE_DIR, "inbox")

# Network config
ALFRED_HOST       = "100.89.26.86"
ALFRED_PORT       = 7788
ALFRED_HEALTH_URL = f"http://{ALFRED_HOST}:{ALFRED_PORT}/health"
ALFRED_TASK_URL   = f"http://{ALFRED_HOST}:{ALFRED_PORT}/task"

JEFF_RESPONSE_PORT = 7789

HTTP_TIMEOUT = 5  # saniye


def init_bridge():
    """Gerekli klasörleri oluşturur."""
    os.makedirs(OUTBOX_DIR, exist_ok=True)
    os.makedirs(INBOX_DIR, exist_ok=True)


def _make_task(task_type: str, payload: dict) -> dict:
    """Standart görev zarfı (UUID tabanlı ID)."""
    return {
        "task_id":    str(uuid.uuid4()),
        "type":       task_type,
        "payload":    payload,
        "status":     "PENDING",
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def is_alfred_online() -> bool:
    """Alfred HTTP server'ının ayakta olup olmadığını kontrol eder."""
    try:
        with urllib.request.urlopen(ALFRED_HEALTH_URL, timeout=HTTP_TIMEOUT) as resp:
            return resp.status == 200
    except Exception:
        return False


def _http_post(url: str, data: dict, timeout: int = HTTP_TIMEOUT):
    """JSON POST gönderir. Başarılıysa yanıt dict'ini, hata varsa None döner."""
    try:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            url, data=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else {}
    except urllib.error.URLError as e:
        log.error(f"HTTP POST hatasi -> {url}: {e}")
        return None
    except Exception as e:
        log.error(f"Beklenmeyen HTTP hatasi -> {url}: {e}")
        return None


def _save_to_outbox(task: dict) -> str:
    """Görevi outbox/ klasörüne yazar. Dosya yolunu döner."""
    init_bridge()
    task_file = os.path.join(OUTBOX_DIR, f"{task['task_id']}.json")
    with open(task_file, "w", encoding="utf-8") as f:
        json.dump(task, f, ensure_ascii=False, indent=2)
    log.info(f"[FALLBACK] Görev outbox'a yazildi: {task_file}")
    return task_file


# Public API (v1.0 ile geriye dönük uyumlu)

def dispatch_task_to_alfred(task_type: str, payload: dict) -> str:
    """
    Jeff -> Alfred görev gönderimi.
    Önce HTTP dener; Alfred offline ise dosya fallback'e geçer.
    Görev ID'sini döner.
    """
    init_bridge()
    task = _make_task(task_type, payload)
    task_id = task["task_id"]

    if is_alfred_online():
        log.info(f"Alfred online — HTTP ile gönderiliyor: {task_id} ({task_type})")
        result = _http_post(ALFRED_TASK_URL, task)
        if result is not None:
            log.info(f"[HTTP OK] Görev gönderildi: {task_id}")
            task["status"] = "SENT_VIA_HTTP"
            _save_to_outbox(task)
            return task_id
        log.warning("HTTP gönderimi basarisiz — dosya fallback'e geçiliyor.")
    else:
        log.warning(f"Alfred offline ({ALFRED_HOST}:{ALFRED_PORT}) — dosya fallback.")

    task["status"] = "DRAFT_PENDING_APPROVAL"
    _save_to_outbox(task)
    return task_id


def check_alfred_responses() -> list:
    """
    Alfred'den dönen yanıtları okur.
    inbox/ klasöründeki tüm JSON dosyalarını listeler.
    """
    init_bridge()
    responses = []
    for fname in os.listdir(INBOX_DIR):
        if fname.endswith(".json"):
            fpath = os.path.join(INBOX_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    responses.append(json.load(f))
            except Exception as e:
                log.error(f"Hata: {fname} okunamadi: {e}")
    return responses


def get_task_status(task_id: str) -> dict:
    """Bir görevin durumunu outbox'tan okur."""
    init_bridge()
    task_file = os.path.join(OUTBOX_DIR, f"{task_id}.json")
    if not os.path.exists(task_file):
        return {"task_id": task_id, "status": "NOT_FOUND"}
    with open(task_file, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    init_bridge()
    print("=== CYBERGENE ALFRED INSTANT BRIDGE v2.0 ===")
    print(f"Alfred online: {is_alfred_online()}")
    t_id = dispatch_task_to_alfred("PING", {"msg": "bridge test"})
    print(f"Görev ID: {t_id}")
    print(f"Durum: {get_task_status(t_id)['status']}")
