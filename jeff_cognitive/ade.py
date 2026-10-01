"""Phase 5: ADE entegrasyonu — Cognitive Core KARAR GEREKTIGINI soyler,
ADE (Board) kararın HAYATTA KALIP KALMADIGINI soyler. Buradaki mantik
DUPLICATE DEGIL: gercek Board (`board_deliberation`, yedek path'ten salt-okunur
shim) varsa ONA delege edilir — Board tamamen offline/deterministik calisir
(heuristic director'ler, LLM yok, kendi ledger'ina yazar). Board yoksa veya
patlarsa acikca isaretlenmis heuristic fallback calisir.

Kritik kural: UNKNOWN asla sessizce TRUE olmaz — `assert_labeled()` denetler.
"""

from __future__ import annotations

import sys
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from .state import (
    EV_ESTIMATE,
    EV_HYPOTHESIS,
    EV_INFERENCE,
    EV_OBSERVED,
    EV_UNKNOWN,
    EV_VERIFIED,
    EVIDENCE_LEVELS,
    CognitiveState,
)

VERDICT_ACCEPT = "ACCEPT"
VERDICT_MODIFY = "MODIFY"
VERDICT_REJECT = "REJECT"
VERDICT_DEFER = "DEFER"
VERDICT_VALIDATE_FIRST = "VALIDATE_FIRST"

VERDICTS = (VERDICT_ACCEPT, VERDICT_MODIFY, VERDICT_REJECT, VERDICT_DEFER, VERDICT_VALIDATE_FIRST)

_BOARD_CANDIDATES = [
    Path("/opt/hermes/jeff_v2"),  # CANLI — production entegrasyon burası
    Path("/home/hermes/backups/pre-surgery-checkpoint-20260904/jeff_v2"),  # fallback
]

# Son yukleme hatasi (gozlemlenebilirlik — sessiz yutma YOK).
_BOARD_LOAD_ERROR: Optional[str] = None


def _load_board_fn() -> Optional[Callable[..., Any]]:
    """Yedek Board'u kutuphane olarak yuklemeyi dene (salt-okunur).

    Not: modul `sys.modules['jeff_board_shim']` altinda KAYITLI yuklenmeli —
    dosya `from __future__ import annotations` + dataclass kullandigi icin
    kayitsiz exec `AttributeError: 'NoneType'...__dict__` ile patlar.
    """
    global _BOARD_LOAD_ERROR
    _BOARD_LOAD_ERROR = None
    for base in _BOARD_CANDIDATES:
        mod = base / "board_deliberation.py"
        if not mod.exists():
            _BOARD_LOAD_ERROR = f"yok: {mod}"
            continue
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("jeff_board_shim", str(mod))
            if spec and spec.loader:
                m = importlib.util.module_from_spec(spec)
                sys.modules["jeff_board_shim"] = m
                spec.loader.exec_module(m)  # type: ignore[union-attr]
                if hasattr(m, "BoardDeliberation"):
                    return m.BoardDeliberation
                _BOARD_LOAD_ERROR = "BoardDeliberation sinifi yok"
        except Exception as exc:
            _BOARD_LOAD_ERROR = f"{type(exc).__name__}: {exc}"
            continue
    return None


def _board_type_enum() -> Any:
    """Board'un BoardType.CUSTOM enum'u (yoksa string fallback)."""
    m = sys.modules.get("jeff_board_shim")
    try:
        if m is not None and hasattr(m, "BoardType"):
            return m.BoardType.CUSTOM
    except Exception:
        pass
    return "custom"


def _verdict_str(value: Any) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def _extract_verdict(res: Any) -> Tuple[str, Optional[float], Dict[str, Any]]:
    """Board sonucundan (verdict, confidence, extra) cikar.

    Board'un `BoardDecision` dataclass'inda `verdict` alani YOK —
    karar `ceo_decision.verdict`'te (Verdict enum). KOK SEBEP NOTU:
    ilk surum `res.verdict` okuyordu → None → fallback'e dusuyordu.
    """
    extra: Dict[str, Any] = {}
    if isinstance(res, dict):
        v = str(res.get("verdict", VERDICT_MODIFY))
        return (v if v in VERDICTS else VERDICT_MODIFY,
                res.get("confidence"), {"board_id": res.get("board_id", "")})
    ceo = getattr(res, "ceo_decision", None)
    if ceo is not None and getattr(ceo, "verdict", None) is not None:
        v = _verdict_str(ceo.verdict)
        extra["board_id"] = str(getattr(res, "board_id", ""))
        extra["next_validation"] = str(getattr(ceo, "next_validation", ""))
        conf = getattr(ceo, "confidence", None)
        try:
            conf_f = float(conf) if conf is not None else None
        except (TypeError, ValueError):
            conf_f = None
        return (v if v in VERDICTS else VERDICT_MODIFY, conf_f, extra)
    direct = getattr(res, "verdict", None)
    if direct is not None:
        v = _verdict_str(direct)
        return (v if v in VERDICTS else VERDICT_MODIFY, None, extra)
    raise ValueError(f"Board sonucunda verdict bulunamadi: {type(res).__name__}")


@dataclass
class DecisionProposal:
    thesis: str = ""
    antithesis: str = ""
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    counter_evidence: List[Dict[str, Any]] = field(default_factory=list)
    uncertainty: float = 0.5
    customer_problem_strength: float = 0.0
    payment_potential: float = 0.0
    economic_viability: float = 0.0
    capability: float = 0.0
    confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def assert_labeled(items: List[Dict[str, Any]]) -> None:
    """Her kanit etiketli olmali; VERIFIED kaynak ister; TRUE diye level yok."""
    for ev in items:
        level = ev.get("level", EV_UNKNOWN)
        if level not in EVIDENCE_LEVELS:
            raise ValueError(f"etiketsiz kanit: {ev!r} (TRUE diye seviye YOK)")
        if level == EV_VERIFIED and not ev.get("source"):
            raise ValueError(f"VERIFIED kaynak ister: {ev!r}")


def heuristic_verdict(p: DecisionProposal) -> Dict[str, Any]:
    score = (
        0.3 * p.customer_problem_strength
        + 0.3 * p.payment_potential
        + 0.2 * p.economic_viability
        + 0.2 * p.capability
    ) * (1.0 - 0.5 * p.uncertainty)
    if score >= 0.7:
        v = VERDICT_ACCEPT
    elif score >= 0.5:
        v = VERDICT_MODIFY
    elif score >= 0.3:
        v = VERDICT_VALIDATE_FIRST
    elif score >= 0.15:
        v = VERDICT_DEFER
    else:
        v = VERDICT_REJECT
    return {"verdict": v, "score": round(score, 3), "via": "heuristic-fallback"}


def challenge(
    proposal: DecisionProposal,
    state: Optional[CognitiveState] = None,
    board_fn: Optional[Callable[..., Any]] = None,
    next_experiment: str = "",
) -> Dict[str, Any]:
    """Karari adversarial analizden gecir. Donus: verdict paketi (state'e islenir)."""
    assert_labeled(proposal.evidence)
    assert_labeled(proposal.counter_evidence)
    out: Dict[str, Any]
    confidence = proposal.confidence
    loader = board_fn if board_fn is not None else _load_board_fn()
    if loader is not None:
        try:
            if isinstance(loader, type):
                board = loader()
                res = board.deliberate(
                    question=proposal.thesis,
                    fact_pack={"antithesis": proposal.antithesis,
                               "evidence": proposal.evidence,
                               "counter_evidence": proposal.counter_evidence},
                    board_type=_board_type_enum(),
                )
                verdict, board_conf, extra = _extract_verdict(res)
                out = {"verdict": verdict, "via": "board", "score": None, **extra}
                if board_conf is not None:
                    confidence = board_conf
            elif hasattr(loader, "deliberate"):
                res = loader.deliberate(
                    question=proposal.thesis,
                    fact_pack={"antithesis": proposal.antithesis,
                               "evidence": proposal.evidence},
                    board_type="custom",
                )
                verdict, board_conf, extra = _extract_verdict(res)
                out = {"verdict": verdict, "via": "board", "score": None, **extra}
                if board_conf is not None:
                    confidence = board_conf
            elif isinstance(loader, dict):
                verdict, board_conf, extra = _extract_verdict(loader)
                out = {"verdict": verdict, "via": "board-stub", "score": None, **extra}
            else:
                out = heuristic_verdict(proposal)
        except Exception as exc:
            out = heuristic_verdict(proposal)
            out["board_error"] = f"{type(exc).__name__}: {exc}"
    else:
        out = heuristic_verdict(proposal)
        if _BOARD_LOAD_ERROR:
            out["board_error"] = _BOARD_LOAD_ERROR
    out.update({
        "confidence": confidence,
        "uncertainty": proposal.uncertainty,
        "next_experiment": next_experiment or out.get("next_validation", ""),
        "levels_used": sorted({e.get("level", EV_UNKNOWN) for e in proposal.evidence}),
    })
    if state is not None:
        state.decisions.append({"kind": "ade_challenge", **proposal.to_dict(), **out})
    return out
