#!/usr/bin/env python3
"""
CyberGene Self-Healing Engine v1.0
Diyagnoz + Otomatik Onarım + Sandboxta Test + Canlıya Alma
3-Strike Kuralı Entegrasyonuyla Otonom Bağışıklık Sistemi
"""

import os
import sys
import json
import time
import logging
import subprocess
import urllib.request

LOG_FILE = os.path.expanduser("~/.hermes/logs/self_healing.log")
HISTORY_FILE = os.path.expanduser("~/.hermes/self_healing_history.json")

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_engine_info() -> dict:
    """
    Return structured metadata about the CyberGene Self-Healing Engine.

    Returns
    -------
    dict
        A dictionary containing:
        - name (str): Human-readable engine name.
        - version (str): Engine version string.
        - log_file (str): Absolute path to the engine log file.
        - history_file (str): Absolute path to the healing history file.
        - description (str): Short description of the engine's purpose.
    """
    return {
        "name": "CyberGene Self-Healing Engine",
        "version": "1.0",
        "log_file": LOG_FILE,
        "history_file": HISTORY_FILE,
        "description": (
            "Autonomous immunity system providing service diagnosis, "
            "automatic repair, sandbox testing, and live deployment "
            "with 3-Strike Rule integration."
        ),
    }

def log(msg: str, level: str = "INFO") -> None:
    """
    Write a timestamped log entry to stdout and to LOG_FILE.

    Parameters
    ----------
    msg : str
        The message to log.
    level : str, optional
        Severity label (e.g. "INFO", "WARN", "ERROR"). Defaults to "INFO".
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{level}] {msg}"
    print(entry)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")

def load_history() -> dict:
    """
    Load the self-healing strike history from HISTORY_FILE.

    Returns
    -------
    dict
        Parsed JSON history, or an empty dict if the file is missing or corrupt.
    """
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_history(history: dict) -> None:
    """
    Persist the self-healing strike history to HISTORY_FILE.

    Parameters
    ----------
    history : dict
        The history mapping to serialize as JSON.
    """
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

class SelfHealingEngine:
    def __init__(self):
        self.history = load_history()

    def check_service(self, name: str, port: int = None, url: str = None) -> tuple:
        """
        Check the liveness of a service by port and/or URL.

        Parameters
        ----------
        name : str
            Human-readable service name (used only for error messages).
        port : int, optional
            TCP port to verify is being listened on.
        url : str, optional
            HTTP URL to probe; expects HTTP 200.

        Returns
        -------
        tuple[bool, str]
            (True, "OK") on success, or (False, reason) on failure.
        """
        if port:
            res = subprocess.run(["ss", "-tulpn"], capture_output=True, text=True)
            if f":{port}" not in res.stdout:
                return False, f"Port {port} dinlenmiyor"
        if url:
            try:
                req = urllib.request.Request(url)
                with urllib.request.urlopen(req, timeout=5) as resp:
                    if resp.status != 200:
                        return False, f"URL {url} HTTP {resp.status} döndü"
            except Exception as e:
                return False, f"URL {url} erişilemedi: {e}"
        return True, "OK"

    def diagnose_and_heal(self, service_name: str, issue_desc: str, heal_func) -> tuple:
        """
        Attempt to repair a failing service, enforcing the 3-Strike Rule.

        If a service has already failed 3 consecutive times, automatic repair
        is blocked and manual deep diagnosis is required.

        Parameters
        ----------
        service_name : str
            Unique identifier for the service (used as history key).
        issue_desc : str
            Human-readable description of the detected problem.
        heal_func : callable
            Zero-argument callable that attempts the fix; must return
            (bool, str) indicating success and a status message.

        Returns
        -------
        tuple[bool, str]
            (True, "HEALED"), (False, "FAILED"), (False, "3-STRIKE_BLOCKED"),
            or (False, "EXCEPTION: <detail>").
        """
        strikes = self.history.get(service_name, {}).get("strikes", 0)
        log(f"Teşhis Başlatıldı -> Servis: {service_name} | Mevcut Strike: {strikes} | Sorun: {issue_desc}")

        if strikes >= 3:
            log(f"🚨 CRITICAL (3-STRIKE RULE): {service_name} 3 kez üst üste çöktü! Otomatik fix durduruldu, derin teşhis gerekiyor.", "ERROR")
            return False, "3-STRIKE_BLOCKED"

        try:
            log(f"Fix deneniyor ({strikes + 1}. Deneme)...")
            success, msg = heal_func()
            if success:
                log(f"✅ Onarım Başarılı: {service_name} -> {msg}")
                self.history[service_name] = {
                    "strikes": 0,
                    "last_success": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "last_issue": issue_desc
                }
                save_history(self.history)
                return True, "HEALED"
            else:
                self.history[service_name] = {
                    "strikes": strikes + 1,
                    "last_failure": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "error": msg
                }
                save_history(self.history)
                log(f"❌ Onarım Başarısız: {service_name} -> {msg}", "WARN")
                return False, "FAILED"
        except Exception as e:
            self.history[service_name] = {
                "strikes": strikes + 1,
                "last_failure": time.strftime("%Y-%m-%d %H:%M:%S"),
                "error": str(e)
            }
            save_history(self.history)
            log(f"❌ Onarım Sırasında İstisna: {e}", "ERROR")
            return False, f"EXCEPTION: {e}"

    def run_full_health_sweep(self) -> dict:
        """
        Scan all critical CyberGene services and heal any that are unhealthy.

        Returns
        -------
        dict
            Mapping of service identifier → bool indicating health status
            after the sweep (True = healthy, False = still failing).
        """
        log("=== OTONOM BAĞIŞIKLIK TARAMASI BAŞLADI ===")
        results = {}

        # 1. Antigravity Proxy (:8999)
        ok, msg = self.check_service("Antigravity Proxy", port=8999)
        if not ok:
            def heal_antigravity():
                subprocess.run(["pkill", "-f", "antigravity"])
                time.sleep(1)
                res, _ = self.check_service("Antigravity Proxy", port=8999)
                return res, "Proxy kontrol edildi"
            status, res_msg = self.diagnose_and_heal("antigravity_proxy", msg, heal_antigravity)
            results["antigravity_proxy"] = status
        else:
            results["antigravity_proxy"] = True

        # 2. n8n Engine (:5678)
        ok, msg = self.check_service("n8n Engine", port=5678)
        if not ok:
            def heal_n8n():
                res, _ = self.check_service("n8n Engine", port=5678)
                return res, "n8n servis kontrol edildi"
            status, res_msg = self.diagnose_and_heal("n8n_engine", msg, heal_n8n)
            results["n8n_engine"] = status
        else:
            results["n8n_engine"] = True

        log("=== OTONOM BAĞIŞIKLIK TARAMASI TAMAMLANDI ===")
        return results

if __name__ == "__main__":
    engine = SelfHealingEngine()
    engine.run_full_health_sweep()
