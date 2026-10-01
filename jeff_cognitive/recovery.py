"""Phase 13: Failure recovery — sonsuz retry YOK, butce var.

Adimlar: sinifla → mevcut politikayla retry → alternatif worker/model →
transient mi structural mi → state guncelle → gerekirse replan.
Basarisiz aksiyon state'den SILINMEZ (blocked_tasks'a duser).
"""

from __future__ import annotations

from typing import Any, Dict, List

from .state import CognitiveState

KIND_TRANSIENT = "transient"      # ag hatasi, timeout, rate limit
KIND_STRUCTURAL = "structural"    # yanlis varsayim, yetki yok, veri yok
KIND_UNKNOWN = "unknown"

TRANSIENT_HINTS = ("timeout", "rate limit", "429", "503", "connection",
                   "temporary", "retry", "timeouterror")
STRUCTURAL_HINTS = ("permission", "denied", "not found", "404", "forbidden",
                    "invalid", "schema", "yetki")


def classify(error: str) -> str:
    e = error.lower()
    if any(h in e for h in TRANSIENT_HINTS):
        return KIND_TRANSIENT
    if any(h in e for h in STRUCTURAL_HINTS):
        return KIND_STRUCTURAL
    return KIND_UNKNOWN


def handle_failure(state: CognitiveState, action: str, error: str,
                   attempts: int = 1, max_retries: int = 3) -> Dict[str, Any]:
    kind = classify(error)
    record = {"action": action, "error": error, "kind": kind, "attempt": attempts}
    if kind == KIND_TRANSIENT and attempts <= max_retries:
        state.active_tasks.append({**record, "status": "retry_scheduled"})
        return {"strategy": "retry", "record": record,
                "reason": f"transient — tekrar dene ({attempts}/{max_retries})"}
    if kind == KIND_TRANSIENT:
        state.blocked_tasks.append(record)
        return {"strategy": "alternative", "record": record,
                "reason": "retry butcesi bitti — alternatif worker/model dene"}
    state.blocked_tasks.append(record)  # structural/unknown kaybolmaz
    return {"strategy": "replan", "record": record,
            "reason": f"{kind} — replan gerekli, tekrarla cozulmez"}
