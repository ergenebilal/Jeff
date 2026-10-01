"""v1.1 Runtime Bridge — Cognitive Core ↔ canlı Hermes (/opt/hermes/jeff_v2).

Rol: SADECE adapter. Business logic YOK (karar/verdict/worker/governance
mantığı canlı sistemlerde; burada sadece çağrı + format dönüşümü).

Canlı hedefler (backup DEĞİL):
- DECIDE → adversarial_engine.AdversarialDecisionEngine (canlı ADE) + live Board
- ACT → worker_pool.WorkerPool.process_task (direkt, senkron — Redis YOK)
- VERIFY→ADE.record_real_world_result (native kalibrasyon)
- GOVERN → governance/autonomy_guard (non-interactive classify/pushback)

Hata politikası: altyapı hatası → BridgeUnavailable (loop fail-open fallback);
governance DENY → her zaman saygı (fail-closed).
"""

from __future__ import annotations

import importlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

LIVE_JEFF = Path("/opt/hermes/jeff_v2")
LIVE_GOV = LIVE_JEFF / "governance"

# ADE verdict → loop aksiyonu (v1.1 §5)
ADE_ACTION = {
    "SCALE": "continue_governed",
    "TEST": "experiment",
    "ITERATE": "pivot",
    "HOLD": "wait",
    "KILL": "block",
    "RESEARCH": "research",
    "NORMAL": "continue",
}

# Board verdict → loop aksiyonu
BOARD_ACTION = {
    "ACCEPT": "continue",
    "MODIFY": "continue_flagged",
    "VALIDATE_FIRST": "experiment",
    "DEFER": "wait",
    "REJECT": "block",
}


class BridgeUnavailable(RuntimeError):
    """Canlı sisteme ulaşılamadı — loop fallback'e düşer (governance hariç)."""


def _ensure_live_path() -> None:
    for p in (str(LIVE_JEFF), str(LIVE_GOV)):
        if p not in sys.path:
            sys.path.insert(0, p)


def live_import(name: str):
    """Canlı modülü yükle. Yoksa BridgeUnavailable (sessiz None YOK)."""
    _ensure_live_path()
    try:
        return importlib.import_module(name)
    except Exception as exc:
        raise BridgeUnavailable(f"live import başarısız: {name}: {exc}") from exc


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class Bridge:
    """Adapter seti. hermes_home: lesson JSON + kalibrasyon DB kökü."""

    def __init__(self, hermes_home: Optional[str | Path] = None,
                 dry_run: bool = True) -> None:
        # NOT: os.environ'a DOKUNULMAZ. Canlı modüller HERMES_HOME'u ilk
        # import'ta okur; test izolasyonu tests/conftest.py session fixture'ında,
        # prod'da gateway env'indedir. Buradaki path sadece lesson JSON içindir.
        self.hermes_home = Path(hermes_home or os.environ.get(
            "HERMES_HOME", str(Path.home() / ".hermes")))
        self.dry_run = dry_run

    # ── DECIDE ──
    def decide_ade(self, question: str, context: Optional[Dict[str, Any]] = None,
                   trigger: str = "cognitive_loop",
                   force_level: Optional[str] = None,
                   dry_run: Optional[bool] = None) -> Dict[str, Any]:
        """Canlı ADE. Dönüş: record + mapped action. LLM yoksa dry_run."""
        mod = live_import("adversarial_engine")
        engine = mod.AdversarialDecisionEngine(
            dry_run=self.dry_run if dry_run is None else dry_run)
        record = engine.run(question=question, context=dict(context or {}),
                            trigger=trigger, force_level=force_level)
        verdict = str(record.get("verdict", "HOLD"))
        return {"record": record,
                "verdict": verdict,
                "action": ADE_ACTION.get(verdict, "wait"),
                "decision_id": record.get("decision_id", ""),
                "via": "live-ade"}

    def decide_board(self, question: str,
                     fact_pack: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Canlı Board (kural-bazlı, LLM'siz). verdict = ceo_decision.verdict."""
        mod = live_import("board_deliberation")
        board = mod.BoardDeliberation()
        res = board.deliberate(question=question,
                               fact_pack=dict(fact_pack or {}),
                               board_type=mod.BoardType.CUSTOM)
        ceo = getattr(res, "ceo_decision", None)
        raw = getattr(ceo, "verdict", None) if ceo is not None else None
        verdict = raw.value if hasattr(raw, "value") else str(raw)
        if verdict not in BOARD_ACTION:
            verdict = "DEFER"
        return {"verdict": verdict,
                "action": BOARD_ACTION[verdict],
                "board_id": str(getattr(res, "board_id", "")),
                "via": "live-board"}

    # ── ACT ──
    def act(self, worker_type: str = "echo",
            params: Optional[Dict[str, Any]] = None,
            idempotency_key: str = "") -> Dict[str, Any]:
        """Canlı WorkerPool.process_task direkt çağrısı (Redis yok).

        Güvenli default: echo. shell/python/file_* canlı guard'lara tabi.
        """
        mod = live_import("worker_pool")
        pool = mod.WorkerPool(pool_name="cognitive", queue_names=["cog"])
        task = {"id": idempotency_key or f"cog-{uuid4().hex[:8]}",
                "task": {"worker_type": worker_type,
                         "params": dict(params or {})}}
        try:
            result = pool.process_task(task)
        except Exception as exc:
            return {"success": False, "worker_type": worker_type,
                    "error": f"{type(exc).__name__}: {exc}",
                    "task_id": task["id"], "via": "live-worker"}
        out = dict(result)
        out.setdefault("worker_type", worker_type)
        out["task_id"] = task["id"]
        out["via"] = "live-worker"
        return out

    # ── OBSERVE ──
    def observe(self, action: str, worker_type: str,
                params: Dict[str, Any], result: Dict[str, Any],
                expected: str = "") -> Dict[str, Any]:
        """Execution sonucunu yapılandırılmış gözleme çevir."""
        return {
            "observation_id": f"obs-{uuid4().hex[:8]}",
            "action": action,
            "worker_type": worker_type,
            "requested": params,
            "success": bool(result.get("success", False)),
            "output": str(result.get("result", result.get("error", "")))[:2000],
            "error": str(result.get("error", ""))[:500],
            "expected": expected,
            "has_external_result": False,
            "created_at": _utcnow(),
        }

    # ── VERIFY ──
    def verify(self, expected: Optional[float], actual: Optional[float],
               context: str = "") -> Dict[str, Any]:
        """EXPECTED vs ACTUAL. Sayısal hata + anlamlı sonuç."""
        if expected is None or actual is None:
            return {"error": None, "outcome": "INCONCLUSIVE",
                    "reason": "beklenen/gerçek yok — " + context}
        err = round(float(actual) - float(expected), 4)
        tol = 0.05
        if abs(err) <= tol:
            outcome = "VERIFIED"
        elif abs(err) <= 0.25:
            outcome = "PARTIALLY_VERIFIED"
        else:
            outcome = "REFUTED"
        return {"error": err, "outcome": outcome,
                "reason": f"expected={expected} actual={actual} error={err:+}"}

    def record_real_world(self, decision_id: str,
                          outcome: Dict[str, Any]) -> Dict[str, Any]:
        """ADE native kalibrasyon yazımı (UNDERCONFIDENT/OVERCONFIDENT/CALIBRATED)."""
        mod = live_import("adversarial_engine")
        engine = mod.AdversarialDecisionEngine(dry_run=True)
        return engine.record_real_world_result(decision_id, outcome)

    # ── LEARN (persistent, cognitive-side lookup — enforcer'a dokunmaz) ──
    def _lessons_path(self) -> Path:
        return self.hermes_home / "cognitive_lessons.json"

    def learn_save(self, lesson: Dict[str, Any]) -> Dict[str, Any]:
        item = dict(lesson)
        item.setdefault("lesson_id", f"les-{uuid4().hex[:8]}")
        item.setdefault("timestamp", _utcnow())
        path = self._lessons_path()
        try:
            existing = json.loads(path.read_text()) if path.exists() else []
        except Exception:
            existing = []
        existing.append(item)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(existing, ensure_ascii=False, indent=2))
        return item

    def lessons_for(self, text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Davranışı değiştiren lookup: metindeki anahtar kelimelerle eşleşen
        dersleri döndür (applies_to/scope/rule alanlarında ara)."""
        path = self._lessons_path()
        if not path.exists():
            return []
        try:
            all_lessons = json.loads(path.read_text())
        except Exception:
            return []
        t = text.lower()
        scored = []
        for les in all_lessons:
            hay = " ".join([
                str(les.get("rule", "")), str(les.get("applies_to", "")),
                str(les.get("scope", "")), str(les.get("lesson", "")),
                str(les.get("failed_assumption", "")),
            ]).lower()
            hits = sum(1 for w in set(t.split()) if len(w) > 3 and w in hay)
            if hits:
                scored.append((hits, les))
        scored.sort(key=lambda x: -x[0])
        return [les for _, les in scored[:limit]]

    def assess_claim_evidence(self, text: str) -> Dict[str, Any]:
        """BEHAVIORAL kanıt fonksiyonu: ders varsa ihtiyatlı, yoksa baseline."""
        matched = self.lessons_for(text)
        if not matched:
            return {"stance": "baseline",
                    "statement": "Potential customer pain.",
                    "lessons_used": []}
        rules = [m.get("rule", "") for m in matched]
        return {
            "stance": "cautious",
            "statement": ("Bu yalnızca OBSERVED durumdur; gerçek müşteri talebi "
                          "doğrulanmadan commercial pain olarak kullanılamaz."),
            "lessons_used": [m.get("lesson_id", "") for m in matched],
            "rules": rules,
        }

    # ── CALIBRATE (persistent, cognitive.db) ──
    def calibrate_add(self, db_path: str | Path, prediction: float,
                      actual: float, confidence: float,
                      decision_type: str = "general",
                      domain: str = "general") -> Dict[str, Any]:
        conn = sqlite3.connect(str(db_path), timeout=10)
        try:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS calibration_points "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, prediction REAL, "
                "actual REAL, error REAL, confidence REAL, decision_type TEXT, "
                "domain TEXT, created_at TEXT)")
            err = round(float(actual) - float(prediction), 4)
            conn.execute(
                "INSERT INTO calibration_points (prediction, actual, error, "
                "confidence, decision_type, domain, created_at) "
                "VALUES (?,?,?,?,?,?,?)",
                (float(prediction), float(actual), err, float(confidence),
                 decision_type, domain, _utcnow()))
            conn.commit()
            n = conn.execute("SELECT COUNT(*) FROM calibration_points").fetchone()[0]
        finally:
            conn.close()
        if n < 30:
            return {"status": "unavailable — sample too small", "n": n}
        return {"status": "available", "n": n, "last_error": err}

    # ── GOVERN (non-interactive; DENY her zaman kazanır) ──
    def govern(self, action: str, tool: str = "",
               params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        mod = live_import("autonomy_guard")
        guard = mod.get_guard()
        res = guard.classify(action, tool, dict(params or {}))
        level = str(res.get("level", "deny")).lower()
        if level in ("deny", "block", "forbidden"):
            return {"decision": "DENY", "reason": str(res.get("reason", "guard")),
                    "via": "live-guard", "raw": res}
        if res.get("requires_telegram") or level in ("approval", "review", "human"):
            return {"decision": "APPROVAL_REQUIRED",
                    "reason": str(res.get("reason", "onay gerekli")),
                    "via": "live-guard", "raw": res}
        return {"decision": "ALLOW", "reason": str(res.get("reason", "auto")),
                "via": "live-guard", "raw": res}

    # ── ROUTE (L-seviye → gerçek kaynak eşlemesi) ──
    def route_for(self, level: str) -> Dict[str, Any]:
        table = {
            "L0": {"worker": "echo", "ade_level": "L0_NORMAL", "verify": False},
            "L1": {"worker": "python", "ade_level": "L1_LIGHT", "verify": False},
            "L2": {"worker": "python", "ade_level": "L2_FULL", "verify": True},
            "HIGH_RISK": {"worker": "python", "ade_level": "L2_FULL",
                          "verify": True, "governance": True},
            "CODING": {"worker": "opencode", "ade_level": "L1_LIGHT",
                       "verify": True},
        }
        return dict(table.get(level, table["L0"]))
