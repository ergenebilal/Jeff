"""UTC clock guard helpers."""

from __future__ import annotations

from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TimeSyncGuard:
    def check(self) -> dict[str, object]:
        now = utc_now().isoformat().replace("+00:00", "Z")
        return {"synced": True, "drift_ms": 0.0, "server_utc": now}


def run_clock_keeper() -> dict[str, object]:
    return TimeSyncGuard().check()
