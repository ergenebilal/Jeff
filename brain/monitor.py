"""Read-only system health helpers for the Hermes brain facade."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any


def _service_active(name: str) -> bool:
    try:
        result = subprocess.run(
            ["systemctl", "is-active", name],
            capture_output=True,
            text=True,
            timeout=3,
        )
        return result.stdout.strip() == "active"
    except Exception:
        return False


def get_metrics() -> dict[str, Any]:
    """Return compact local metrics without mutating the system."""
    disk = shutil.disk_usage("/")
    return {
        "disk": {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": round((disk.used / disk.total) * 100, 2) if disk.total else None,
        },
        "services": {
            "hermes-gateway": _service_active("hermes-gateway.service"),
            "hermes-embedding-daemon": _service_active("hermes-embedding-daemon.service"),
            "hermes-hq": _service_active("hermes-hq.service"),
        },
        "cwd": str(Path.cwd()),
    }


def check_health() -> dict[str, Any]:
    """Return status plus metrics for dashboard/prompt use."""
    metrics = get_metrics()
    services = metrics.get("services", {})
    healthy = all(services.values()) if services else False
    return {"status": "healthy" if healthy else "degraded", "healthy": healthy, "metrics": metrics}
