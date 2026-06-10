"""Clock Keeper protocol for Hermes UTC drift discipline."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional


STATE_PATH = Path.home() / ".hermes" / "agent_state.json"
DRIFT_THRESHOLD_MS = 100.0


def utc_now() -> datetime:
    """Return the authoritative server UTC time."""
    return datetime.now(timezone.utc)


def _isoformat_utc(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_utc(value: object) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except Exception:
        return None


def _read_state(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_state(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


class TimeSyncGuard:
    """Compare Hermes logic time with server UTC and repair drift."""

    def __init__(
        self,
        state_path: Optional[Path] = None,
        threshold_ms: float = DRIFT_THRESHOLD_MS,
        now_fn: Optional[Callable[[], datetime]] = None,
    ):
        self.state_path = Path(state_path) if state_path is not None else STATE_PATH
        self.threshold_ms = float(threshold_ms)
        self.now_fn = now_fn or utc_now

    def check(self) -> dict:
        state = _read_state(self.state_path)
        server_now = self.now_fn().astimezone(timezone.utc)
        server_iso = _isoformat_utc(server_now)
        logic_before = state.get("last_sync") or state.get("clock_keeper", {}).get("last_sync_utc")
        logic_dt = _parse_utc(logic_before)
        drift_ms = None
        should_sync = logic_dt is None
        if logic_dt is not None:
            drift_ms = abs((server_now - logic_dt).total_seconds() * 1000.0)
            should_sync = drift_ms > self.threshold_ms

        result = {
            "server_utc": server_iso,
            "logic_utc_before": logic_before,
            "drift_ms": drift_ms,
            "threshold_ms": self.threshold_ms,
            "synced": bool(should_sync),
        }
        if should_sync:
            state["last_sync"] = server_iso
        state["clock_keeper"] = {
            **result,
            "last_sync_utc": state.get("last_sync", server_iso),
            "checked_at_utc": server_iso,
        }
        _write_state(self.state_path, state)
        return state["clock_keeper"]


def run_clock_keeper() -> str:
    """Run the guard once and return a concise UTC-only status line."""
    result = TimeSyncGuard().check()
    drift = result.get("drift_ms")
    drift_text = "missing" if drift is None else f"{drift:.3f}ms"
    status = "synced" if result.get("synced") else "ok"
    return f"Clock Keeper: {status} | drift={drift_text} | utc={result.get('server_utc')}"
