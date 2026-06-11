"""Baseline snapshot for Hermes ALPHA rebase checks."""

from __future__ import annotations

import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from .clock_keeper import TimeSyncGuard
from .learning import get_lessons_summary, get_recent_lessons
from .monitor import check_health, get_metrics
from .persona import load_persona_profile


CONFIG_PATH = Path.home() / ".hermes" / "config.yaml"


def collect_baseline_snapshot(
    test_count: Optional[int] = None,
    services: Optional[dict[str, bool]] = None,
) -> dict[str, Any]:
    """Collect a read-only baseline snapshot for ALPHA planning."""
    health = check_health()
    metrics = get_metrics()
    ops_services = services if services is not None else health.get("services", {})
    clock = TimeSyncGuard().check()
    persona = _collect_persona_snapshot()
    memory = _collect_memory_snapshot()
    tests = {"collected": int(test_count) if test_count is not None else _count_tests()}
    provider = _collect_provider_snapshot()
    status = "ok"
    if not ops_services.get("gateway") or not ops_services.get("embedding"):
        status = "degraded"
    if clock.get("synced") and clock.get("drift_ms") not in (None, 0) and float(clock.get("drift_ms") or 0) > 100:
        status = "degraded"
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "persona": persona,
        "ops": {
            "status": status,
            "services": ops_services,
            "health": health,
            "metrics": metrics,
            "clock": clock,
        },
        "memory": memory,
        "tests": tests,
        "provider": provider,
        "summary": _format_summary(status, persona, ops_services, tests, provider),
    }


def summarize_baseline(snapshot: Optional[dict[str, Any]] = None) -> str:
    """Return a short human-readable baseline summary."""
    snap = snapshot or collect_baseline_snapshot()
    return str(snap.get("summary", "")).strip()


def _collect_persona_snapshot() -> dict[str, Any]:
    profile = load_persona_profile()
    identity = profile.get("identity") if isinstance(profile, dict) else {}
    if not isinstance(identity, dict):
        identity = {}
    name = identity.get("name") or profile.get("name") if isinstance(profile, dict) else None
    technical_name = identity.get("official_name") or profile.get("official_name") if isinstance(profile, dict) else None
    return {
        "primary_name": name or "Jeff" if profile else None,
        "technical_name": technical_name or "Hermes Agent" if profile else "Hermes Agent",
        "has_profile": bool(profile),
    }


def _collect_memory_snapshot() -> dict[str, Any]:
    lessons = get_recent_lessons(limit=20)
    return {
        "lessons": len(lessons),
        "summary": get_lessons_summary(5),
    }


def _collect_provider_snapshot() -> dict[str, Any]:
    provider = ""
    model = ""
    memory_provider = ""
    try:
        if CONFIG_PATH.exists():
            for line in CONFIG_PATH.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if stripped.startswith("provider:") and not provider:
                    provider = stripped.split(":", 1)[1].strip().strip("'\"")
                elif stripped.startswith("model:") and not model:
                    model = stripped.split(":", 1)[1].strip().strip("'\"")
                elif "memory" in stripped and "provider:" in stripped and not memory_provider:
                    memory_provider = stripped.split("provider:", 1)[1].strip().strip("'\"")
    except Exception:
        pass
    return {
        "provider": provider or None,
        "model": model or None,
        "memory_provider": memory_provider or None,
        "platform": platform.system().lower(),
        "python": platform.python_version(),
        "cwd": str(Path.cwd()),
        "production": os.environ.get("HERMES_ENV", "").lower() in {"prod", "production"},
    }


def _count_tests() -> int:
    try:
        result = subprocess.run(
            [os.environ.get("PYTHON", "python"), "-m", "pytest", "tests/", "--collect-only", "-q"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        for line in result.stdout.splitlines():
            if "collected" in line:
                try:
                    return int(line.split()[0])
                except Exception:
                    continue
    except Exception:
        pass
    return 0


def _format_summary(status: str, persona: dict[str, Any], services: dict[str, bool], tests: dict[str, Any], provider: dict[str, Any]) -> str:
    gateway = "✅" if services.get("gateway") else "❌"
    embedding = "✅" if services.get("embedding") else "❌"
    name = persona.get("primary_name") or "Jeff"
    provider_name = provider.get("provider") or "unknown"
    return (
        f"Baseline: {status} | persona={name} | "
        f"services={gateway} gateway / {embedding} embedding | "
        f"tests={tests.get('collected', 0)} | provider={provider_name}"
    )
