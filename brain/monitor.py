"""Health and metrics helpers for Hermes core."""

import os
import socket
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def check_health() -> dict:
    services = {
        "gateway": _systemd_active("hermes-gateway.service"),
        "embedding": _port_open("127.0.0.1", 8767),
        "headroom": _port_open("127.0.0.1", 8787),
    }
    status = "ok" if services.get("gateway") and services.get("embedding") else "degraded"
    return {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "memory": _get_memory_usage(),
        "gateway": {"alive": services["gateway"]},
        "services": services,
    }


def get_metrics() -> dict:
    return {
        "active_sessions": _count_active_sessions(),
        "disk_usage": _get_disk_usage(),
    }


def _get_memory_usage() -> dict:
    try:
        mem = {}
        with open("/proc/meminfo", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith(("MemTotal", "MemAvailable")):
                    parts = line.split()
                    mem[parts[0].rstrip(":")] = int(parts[1]) // 1024
        return {
            "total_mb": mem.get("MemTotal", 0),
            "available_mb": mem.get("MemAvailable", 0),
        }
    except Exception:
        return {"total_mb": 0, "available_mb": 0}


def _get_disk_usage() -> dict:
    try:
        st = os.statvfs("/")
        total = st.f_frsize * st.f_blocks // (1024**3)
        free = st.f_frsize * st.f_bfree // (1024**3)
        return {"total_gb": total, "free_gb": free}
    except Exception:
        return {"total_gb": 0, "free_gb": 0}


def _count_active_sessions() -> int:
    db_path = Path.home() / ".hermes" / "hermes_state.db"
    if not db_path.exists():
        return 0
    try:
        import sqlite3

        conn = sqlite3.connect(str(db_path))
        try:
            cur = conn.execute("SELECT COUNT(*) FROM sessions WHERE status='active'")
            return int(cur.fetchone()[0])
        finally:
            conn.close()
    except Exception:
        return 0


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1.0):
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
