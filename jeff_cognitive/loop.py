"""JEFF Cognitive Core — Executive Cognitive Loop (v1.1 runtime-wired).

GOAL→UNDERSTAND→PLAN→DECIDE→ACT→OBSERVE→VERIFY→LEARN→CALIBRATE→REPLAN.

- DECIDE → canlı ADE (dry_run default) + canlı Board; ADE KILL → DONE (halt).
  Board REJECT bayrağı replan sinyallerine düşer (ara-vuruşta deadlock yok).
- ACT → canlı WorkerPool.process_task (default echo = güvenli); governance
  DENY → REPLAN (fail-closed). Idempotency key her denemede sabit.
- OBSERVE/VERIFY/LEARN/CALIBRATE → bridge adapter'ları; malzeme yoksa
  INSUFFICIENT kaydı + ilerleme (uydurma YOK).
- Canlı altyapı çökerse → fallback passthrough + bridge_error (fail-open);
  governance kararı bundan muaf.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .state import (
    PHASE_ACT,
    PHASE_CALIBRATE,
    PHASE_DECIDE,
    PHASE_DONE,
    PHASE_GOAL,
    PHASE_LEARN,
    PHASE_OBSERVE,
    PHASE_PLAN,
    PHASE_REPLAN,
    PHASE_UNDERSTAND,
    PHASE_VERIFY,
    CognitiveState,
    CognitiveStore,
)
from .replan import (
    OUT_CONTINUE,
    OUT_ESCALATE,
    OUT_KILL,
    OUT_PAUSE,
    OUT_PIVOT,
    OUT_RESEARCH,
    decide as replan_decide,
)
from .runtime_bridge import Bridge, BridgeUnavailable

PHASE_ORDER = (
    PHASE_GOAL,
    PHASE_UNDERSTAND,
    PHASE_PLAN,
    PHASE_DECIDE,
    PHASE_ACT,
    PHASE_OBSERVE,
    PHASE_VERIFY,
    PHASE_LEARN,
    PHASE_CALIBRATE,
    PHASE_REPLAN,
)

HandlerResult = Dict[str, Any]
Handler = Callable[[CognitiveState, Dict[str, Any]], HandlerResult]


def _default_next(current: str) -> str:
    """Sira ile sonraki faz; REPLAN sonrasi default DONE (Phase 10'da akillanir)."""
    if current == PHASE_REPLAN:
        return PHASE_DONE
    idx = PHASE_ORDER.index(current)
    return PHASE_ORDER[idx + 1]


# ── Default handler'lar (minimal, idempotent, LLM yok) ──

def _h_goal(state: CognitiveState, ctx: Dict[str, Any]) -> HandlerResult:
    if not state.objective.strip():
        return {
            "reason": "objective bos — calisilamaz",
            "errors": ["empty_objective"],
            "confidence": 0.0,
            "next_phase": PHASE_DONE,
            "next_action": None,
            "output": {"accepted": False},
        }
    return {
        "reason": "hedef kabul edildi",
        "confidence": 0.5,
        "output": {"accepted": True, "objective": state.objective},
        "next_action": "anla",
    }


def _h_understand(state: CognitiveState, ctx: Dict[str, Any]) -> HandlerResult:
    updates: Dict[str, Any] = {}
    if not state.unknowns and not state.assumptions:
        updates["unknowns"] = ["odeme niyeti bilinmiyor", "karar verici bilinmiyor"]
        updates["assumptions"] = ["teklif deger onermesi anlasilir"]
    return {
        "reason": "varsayim/bilinmeyen cikartildi",
        "confidence": 0.4,
        "output": {"unknowns": state.unknowns or updates.get("unknowns")},
        "updates": updates,
        "next_action": "planla",
    }


def _h_plan(state: CognitiveState, ctx: Dict[str, Any],
            bridge: Any = None) -> HandlerResult:
    updates: Dict[str, Any] = {}
    if not state.plan:
        updates["plan"] = [
            {"step": 1, "action": "kanit topla", "cost_estimate": 1.0},
            {"step": 2, "action": "deney tasarla", "cost_estimate": 1.0},
            {"step": 3, "action": "dogurla", "cost_estimate": 1.0},
        ]
    # LEARN→BEHAVIOR: kayıtlı ders varsa planı ihtiyatlandır (loop seviyesi)
    lesson_hit: List[str] = []
    if bridge is not None:
        try:
            for les in bridge.lessons_for(state.objective):
                rule = str(les.get("rule", ""))
                if rule and rule not in state.constraints:
                    state.constraints.append(f"ders: {rule}")
                    lesson_hit.append(str(les.get("lesson_id", "")))
        except Exception:
            pass
    if lesson_hit:
        updates["constraints"] = state.constraints
    return {
        "reason": "iskelet plan" + (f" ({len(lesson_hit)} ders uygulandi)"
                                    if lesson_hit else ""),
        "confidence": 0.45,
        "output": {"steps": len(state.plan) or 3,
                   "lesson_informed": bool(lesson_hit),
                   "lessons_used": lesson_hit},
        "updates": updates,
        "next_action": "karar ver",
    }


def _h_passthrough(reason: str, nxt: str, conf: float = 0.5) -> Handler:
    def _fn(state: CognitiveState, ctx: Dict[str, Any]) -> HandlerResult:
        return {"reason": reason, "confidence": conf,
                "output": {"phase": state.current_phase}, "next_action": nxt}
    _fn.__name__ = f"passthrough_{reason[:12]}"
    return _fn


def _fallback(reason: str, err: str, nxt_action: str,
              conf: float = 0.4) -> HandlerResult:
    """Canlı altyapı yoksa: ilerle ama KAYDET (fail-open, governance hariç)."""
    return {"reason": reason, "confidence": conf,
            "output": {"fallback": True}, "errors": [err],
            "next_action": nxt_action}


def _h_decide(state: CognitiveState, ctx: Dict[str, Any],
              bridge: Bridge) -> HandlerResult:
    thesis = state.objective
    context = {"success_criteria": state.success_criteria,
               "unknowns": state.unknowns,
               "assumptions": state.assumptions}
    try:
        ade = bridge.decide_ade(
            thesis, context,
            trigger=str(ctx.get("trigger", "cognitive_loop")),
            force_level=ctx.get("force_level"),
            dry_run=ctx.get("dry_run", bridge.dry_run))
        board = bridge.decide_board(
            thesis, {"evidence": [{"content": e.get("content", ""), "level": "UNKNOWN"}
                                  for e in state.evidence[:5]]})
    except BridgeUnavailable as exc:
        return _fallback("bridge yok — karar ertelendi", str(exc), "uygula")
    state.decisions.append({"kind": "ade_decision",
                            "ade_verdict": ade["verdict"],
                            "ade_action": ade["action"],
                            "decision_id": ade["decision_id"],
                            "board_verdict": board["verdict"],
                            "board_action": board["action"],
                            "board_id": board["board_id"]})
    if ade["action"] == "block":  # ADE KILL — halt (tek halt kuralı)
        return {"reason": f"ADE KILL — durduruldu ({ade['decision_id']})",
                "confidence": 0.2,
                "output": {"ade_verdict": "KILL", "halted": True},
                "errors": ["ade_kill"],
                "next_phase": PHASE_DONE, "next_action": "kapat"}
    flag = " [board REJECT bayraklı]" if board["action"] == "block" else ""
    return {"reason": f"ADE {ade['verdict']} + Board {board['verdict']}{flag}",
            "confidence": 0.55,
            "output": {"ade_verdict": ade["verdict"],
                       "board_verdict": board["verdict"],
                       "ade_action": ade["action"],
                       "decision_id": ade["decision_id"]},
            "next_action": "uygula"}


def _h_act(state: CognitiveState, ctx: Dict[str, Any],
           bridge: Bridge) -> HandlerResult:
    spec = dict(ctx.get("action") or {})
    worker_type = str(spec.get("worker_type", "echo"))
    params = dict(spec.get("params") or {"task": state.objective})
    category = str(ctx.get("category", "SIMULATE"))
    # 1) governance — fail-closed (bizim politika + canlı guard)
    from .autonomy import check as policy_check
    pol = policy_check(category, governance_ok=True,
                       approval_granted=bool(ctx.get("approval_granted", False)))
    if pol["decision"] == "DENY":
        state.blocked_tasks.append({"action": worker_type, "params": params,
                                    "error": pol["reason"]})
        return {"reason": f"governance DENY — REPLAN ({pol['reason']})",
                "confidence": 0.3, "errors": ["governance_deny"],
                "next_phase": PHASE_REPLAN, "next_action": "hatayi degerlendir"}
    if pol["decision"] == "APPROVAL_REQUIRED":
        state.blocked_tasks.append({"action": worker_type, "params": params,
                                    "error": pol["reason"]})
        return {"reason": f"onay yok — REPLAN ({pol['reason']})",
                "confidence": 0.3, "errors": ["approval_required"],
                "next_phase": PHASE_REPLAN, "next_action": "onay iste"}
    try:
        gov = bridge.govern(f"{worker_type}: {str(params)[:120]}",
                            tool=worker_type, params=params)
    except BridgeUnavailable as exc:
        return _fallback("guard yok — güvenli echo'ya düşüldü", str(exc), "gozle")
    if gov["decision"] == "DENY":
        state.blocked_tasks.append({"action": worker_type, "params": params,
                                    "error": gov["reason"]})
        return {"reason": f"canlı guard DENY — REPLAN ({gov['reason']})",
                "confidence": 0.3, "errors": ["live_guard_deny"],
                "next_phase": PHASE_REPLAN, "next_action": "hatayi degerlendir"}
    # 2) yürüt (idempotent key)
    key = str(ctx.get("idempotency_key")
              or f"{state.goal_id}-act-{len(state.completed_tasks)}")
    try:
        res = bridge.act(worker_type, params, idempotency_key=key)
    except BridgeUnavailable as exc:
        return _fallback("worker yok — ertelendi", str(exc), "gozle")
    rec = {"action": worker_type, "params": params, "result": res,
           "task_id": res.get("task_id", key)}
    if res.get("success"):
        state.completed_tasks.append(rec)
    else:
        state.active_tasks.append(rec)
    return {"reason": f"worker {worker_type}: "
                      f"{'ok' if res.get('success') else 'hata'}",
            "confidence": 0.6 if res.get("success") else 0.3,
            "output": {"task_id": rec["task_id"], "success": bool(res.get("success"))},
            "errors": [] if res.get("success") else [str(res.get("error", "worker_error"))],
            "next_action": "gozle"}


def _h_observe(state: CognitiveState, ctx: Dict[str, Any],
               bridge: Bridge) -> HandlerResult:
    last = (state.completed_tasks + state.active_tasks)[-1] if (
        state.completed_tasks + state.active_tasks) else None
    if last is None:
        return {"reason": "gozlemlenecek execution yok",
                "confidence": 0.3,
                "output": {"observation": None},
                "next_action": "dogrula"}
    res = last.get("result", {})
    obs = bridge.observe(str(last.get("action", "")), str(res.get("worker_type", "")),
                         dict(last.get("params", {})), dict(res),
                         expected=str((state.plan or [{}])[0].get("strategy", "")))
    state.observations.append(obs)
    return {"reason": f"gozlem {obs['observation_id']} "
                      f"({'ok' if obs['success'] else 'hata'})",
            "confidence": 0.55,
            "output": {"observation_id": obs["observation_id"],
                       "success": obs["success"]},
            "next_action": "dogrula"}


def _h_replan(state: CognitiveState, ctx: Dict[str, Any]) -> HandlerResult:
    """REPLAN fazi → Phase 10 `decide()`'a bagli. Sinyaller ctx'ten:
    `replan_signals` (veya `signals`). Outcome→hedef eslemesi:
    CONTINUE→DONE (dongu tamam) · PIVOT→PLAN · RESEARCH→UNDERSTAND ·
    PAUSE/KILL/ESCALATE→DONE (next_action'da iz birakilir; devam cocuk hedefle).
    """
    signals = dict(ctx.get("replan_signals") or ctx.get("signals") or {})
    res = replan_decide(state, signals)
    outcome = res["outcome"]
    nxt = {
        OUT_CONTINUE: PHASE_DONE,
        OUT_PIVOT: PHASE_PLAN,
        OUT_RESEARCH: PHASE_UNDERSTAND,
        OUT_PAUSE: PHASE_DONE,
        OUT_KILL: PHASE_DONE,
        OUT_ESCALATE: PHASE_DONE,
    }[outcome]
    return {
        "reason": f"replan: {outcome} — {res['reason']}",
        "confidence": state.confidence,
        "output": {"outcome": outcome, "signals": signals},
        "next_phase": nxt,
        "next_action": state.next_action or "",
    }


def _h_verify(state: CognitiveState, ctx: Dict[str, Any],
              bridge: Bridge) -> HandlerResult:
    exp = ctx.get("expected")
    act = ctx.get("actual")
    if exp is None or act is None:
        # sayısal çift yoksa dürüst INCONCLUSIVE (uydurma yok)
        state.verification_results.append({"outcome": "INCONCLUSIVE",
                                           "reason": "expected/actual yok"})
        return {"reason": "dogrulanacak olcu yok — INCONCLUSIVE",
                "confidence": 0.3,
                "output": {"outcome": "INCONCLUSIVE"},
                "next_action": "ogren"}
    v = bridge.verify(exp, act, context=state.objective[:80])
    state.verification_results.append(v)
    # ADE native kalibrasyon kaydı (varsa decision_id ile — best effort)
    did = ""
    for d in reversed(state.decisions):
        if isinstance(d, dict) and d.get("decision_id"):
            did = str(d["decision_id"])
            break
    if did:
        try:
            bridge.record_real_world(did, {"success": v["outcome"] in (
                "VERIFIED", "PARTIALLY_VERIFIED"),
                "error": v["error"], "context": state.objective[:120]})
        except BridgeUnavailable:
            pass
    state.confidence = max(0.0, min(1.0, state.confidence + (
        0.1 if v["outcome"] == "VERIFIED" else (
            -0.1 if v["outcome"] == "REFUTED" else 0.0))))
    return {"reason": f"verify: {v['outcome']} ({v['reason']})",
            "confidence": state.confidence,
            "output": {"outcome": v["outcome"], "error": v["error"]},
            "next_action": "ogren"}


def _h_learn(state: CognitiveState, ctx: Dict[str, Any],
             bridge: Bridge) -> HandlerResult:
    from .learning import build_lesson
    obs = state.observations[-1] if state.observations else None
    ver = state.verification_results[-1] if state.verification_results else {}
    if obs is None:
        state.lessons.append({"note": "ogrenilecek gozlem yok",
                              "kind": "insufficient"})
        return {"reason": "ogrenme malzemesi yok — ders uretilmedi",
                "confidence": state.confidence,
                "output": {"lesson": None},
                "next_action": "kalibre et"}
    try:
        les = build_lesson(
            believed=state.objective,
            happened=str(obs.get("output", ""))[:500] or "gozlem bos",
            why_matters=str(ver.get("reason", "dogrulama kaydi")),
            failed_assumption=(state.assumptions[0]
                               if state.assumptions else "varsayim kaydi yok"),
            change=f"Benzer gorevde once gozlemi dogrula, sonra yargiya var "
                   f"({ver.get('outcome', 'INCONCLUSIVE')})",
            apply_where="cognitive-loop/*",
            confidence=0.6,
            goal_id=state.goal_id)
    except ValueError as exc:
        return {"reason": f"ders kurulamadi: {exc}", "confidence": state.confidence,
                "output": {"lesson": None}, "errors": [str(exc)],
                "next_action": "kalibre et"}
    saved = bridge.learn_save(les.to_dict())
    state.lessons.append(saved)
    return {"reason": f"ders {saved['lesson_id'][:8]} kaydedildi",
            "confidence": state.confidence,
            "output": {"lesson_id": saved["lesson_id"]},
            "next_action": "kalibre et"}


def _h_calibrate(state: CognitiveState, ctx: Dict[str, Any],
                 bridge: Bridge, db_path: Any) -> HandlerResult:
    ver = state.verification_results[-1] if state.verification_results else {}
    if ver.get("error") is None:
        state.calibration_data = {"status": "unavailable — olcu yok"}
        return {"reason": "kalibrasyon olcusu yok",
                "confidence": state.confidence,
                "output": dict(state.calibration_data),
                "next_action": "replanla"}
    last_conf = 0.5
    for d in reversed(state.decisions):
        if isinstance(d, dict) and "confidence" in d:
            try:
                last_conf = float(d["confidence"])
                break
            except (TypeError, ValueError):
                pass
    try:
        # expected/actual ctx'ten veya verification kaydından türetilemezse
        # lesson-only: noktayı 0-merkezli hata ile işleme (dürüst: skip)
        exp = ctx.get("expected")
        act = ctx.get("actual")
        if exp is None or act is None:
            raise KeyError("numeric pair yok")
        out = bridge.calibrate_add(db_path, exp, act, last_conf)
    except (BridgeUnavailable, KeyError, TypeError, ValueError) as exc:
        state.calibration_data = {"status": f"skipped: {exc}"}
        return {"reason": f"kalibrasyon atlandi: {exc}",
                "confidence": state.confidence,
                "output": dict(state.calibration_data),
                "next_action": "replanla"}
    state.calibration_data = out
    return {"reason": f"kalibrasyon: {out.get('status')} (n={out.get('n')})",
            "confidence": state.confidence,
            "output": out, "next_action": "replanla"}


def build_handlers(bridge: Bridge, db_path: Any) -> Dict[str, Handler]:
    """Runtime-wired handler seti (testlerde register ile ezilebilir)."""
    return {
        PHASE_GOAL: _h_goal,
        PHASE_UNDERSTAND: _h_understand,
        PHASE_PLAN: lambda s, c: _h_plan(s, c, bridge),
        PHASE_DECIDE: lambda s, c: _h_decide(s, c, bridge),
        PHASE_ACT: lambda s, c: _h_act(s, c, bridge),
        PHASE_OBSERVE: lambda s, c: _h_observe(s, c, bridge),
        PHASE_VERIFY: lambda s, c: _h_verify(s, c, bridge),
        PHASE_LEARN: lambda s, c: _h_learn(s, c, bridge),
        PHASE_CALIBRATE: lambda s, c: _h_calibrate(s, c, bridge, db_path),
        PHASE_REPLAN: _h_replan,
    }


DEFAULT_HANDLERS: Dict[str, Handler] = {
    PHASE_GOAL: _h_goal,
    PHASE_UNDERSTAND: _h_understand,
    PHASE_PLAN: _h_plan,
    PHASE_DECIDE: _h_passthrough("karar noktasi (ADE Phase 5'te)", "uygula"),
    PHASE_ACT: _h_passthrough("eylem (WorkerPool Phase 6+)", "gozle"),
    PHASE_OBSERVE: _h_passthrough("gozlem toplandi", "dogrula"),
    PHASE_VERIFY: _h_passthrough("dogrulama (karsilastirma Phase 7'de)", "ogren"),
    PHASE_LEARN: _h_passthrough("ogrenme (structured Phase 9'da)", "kalibre et"),
    PHASE_CALIBRATE: _h_passthrough("kalibrasyon (Phase 8'de)", "replanla"),
    PHASE_REPLAN: _h_replan,
}


class CognitiveLoop:
    """ExecutiveController. State'i her adimda store'dan tazeler (crash-safe).

    bridge verilmezse store dizinine yazan default Bridge kurulur
    (dry_run=True). register() ile her faz ezilebilir.
    """

    def __init__(self, store: CognitiveStore, max_errors: int = 3,
                 bridge: Optional[Bridge] = None) -> None:
        self.store = store
        self.max_errors = max_errors
        self.bridge = bridge if bridge is not None else Bridge(
            hermes_home=store.db_path.parent)
        self.handlers: Dict[str, Handler] = build_handlers(
            self.bridge, store.db_path)

    def register(self, phase: str, fn: Handler) -> None:
        if phase not in PHASE_ORDER and phase != PHASE_DONE:
            raise ValueError(f"bilinmeyen faz: {phase!r}")
        self.handlers[phase] = fn

    def history(self, goal_id: str) -> List[Dict[str, Any]]:
        return self.store.transitions(goal_id)

    def step(self, goal_id: str, ctx: Optional[Dict[str, Any]] = None) -> CognitiveState:
        """Tek faz ilerlet. Donus: guncel state."""
        state = self.store.load(goal_id)
        if state.current_phase == PHASE_DONE:
            return state
        ctx = dict(ctx or {})
        handler = self.handlers.get(state.current_phase)
        if handler is None:
            raise RuntimeError(f"handler yok: {state.current_phase}")
        try:
            result = handler(state, ctx) or {}
        except Exception as exc:  # handler patlarsa → REPLAN'a dus, state kaybolmaz
            return self.store.transition(
                state, PHASE_REPLAN,
                reason=f"handler hatasi ({state.current_phase}): {type(exc).__name__}: {exc}",
                input_data={"phase": state.current_phase},
                output_data={},
                errors=[f"{type(exc).__name__}: {exc}"],
                next_action="hatayi degerlendir",
            )
        updates = result.get("updates") or {}
        for key, value in updates.items():
            if hasattr(state, key):
                setattr(state, key, value)
        cost = result.get("cost")
        if cost:
            try:
                state.spend(float(cost))
            except (TypeError, ValueError):
                pass
        next_phase = result.get("next_phase") or _default_next(state.current_phase)
        return self.store.transition(
            state, next_phase,
            reason=str(result.get("reason", "")),
            input_data={"phase": state.current_phase, **{k: v for k, v in ctx.items() if k != "secrets"}},
            output_data=dict(result.get("output") or {}),
            confidence=result.get("confidence", state.confidence),
            cost=cost,
            errors=list(result.get("errors") or []),
            next_action=str(result.get("next_action") or ""),
        )

    def run(
        self,
        goal_id: str,
        ctx: Optional[Dict[str, Any]] = None,
        max_steps: int = 20,
    ) -> CognitiveState:
        """Hedef DONE olana veya max_steps dolana kadar ilerle. Yari kalirsa resume edilebilir."""
        state = self.store.load(goal_id)
        steps = 0
        while state.current_phase != PHASE_DONE and steps < max_steps:
            state = self.step(goal_id, ctx)
            steps += 1
        return state
