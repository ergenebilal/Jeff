"""v1.2 Runtime Hook — conversation_loop giriş kancası (ADDITIVE, FAIL-OPEN).

V11 `cognitive_hook.py` (P1) politikası burada Hermes `conversation_loop`
imzasıyla birleştirilir: `cognitive_hook(agent, user_message, config)`.

İlkeler (V11 ile AYNI):
- Mod gate: `COGNITIVE_HOOK_MODE=disabled` → hep SKIP/continue; ayrıca hermes
  `cognitive.enabled=false` (varsayılan) → SKIP.
- Stratejik görünen şeyler → canlı ADE(dry) + Board (ms, no LLM; `full` modunda
  gerçek LLM — bilinçli).
- Stratejik kararlar denetim izi yazar (decision + board ledger); stratejik
  olmayan çağrılar HİÇBİR ŞEY yazmaz (yalnız ders danışmanlığı).
- Hata → SKIP/continue (fail-open); ADIM 12: governance BLOCK/enforcement
  YALNIZCA `full` modda geçerlidir. fast/dry-run → OBSERVE (no-enforcement,
  fail-open) — placeholder/kanıtsız karar governance authority kazanamaz.
- Bu kanca gateway'i ASLA bloke etmez (try/except + kısa zaman bütçesi).
"""

from __future__ import annotations

import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

_COGNITIVE = Path(__file__).resolve().parent

# gate_decision'ın hiç debate gerektirmediği ancak denetim istediğimiz karar sınıfları
STRATEGIC_TRIGGERS = {
    "niche_selection", "product_decision", "pricing", "customer_segment",
    "resource_allocation", "architecture_change", "critical_sales",
    "assumption_validation", "research_strategic", "high_value",
}

_STRATEGIC_KW = [
    "strateji", "stratejik", "pivot", "vizyon", "yeni ürün", "yeni niş",
    "fiyat", "pricing", "pazar seçim", "pazar seçimi", "pazar genişlet",
    "kritik karar", "yatırım", "investment", "çekil", "exit", "ürün yönü",
    "acquisition", "büyüme strateji", "niche", "pazar", "ürün karar",
]

# conversation_loop çağrısında uygulanacak ek eşik (fail-open): çok kısa / gündelik
# mesajlarda cognitive katmanı uyandırma.
_TRIVIAL_PATTERNS = (
    "merhaba", "selam", "hey", "hello", "hi", "saat kaç", "naber",
    "nasılsın", "ok", "tamam", "tesekkur", "thanks",
)


def _env_mode() -> str:
    return os.environ.get("COGNITIVE_HOOK_MODE", "fast").lower()


def _looks_strategic(text: str) -> bool:
    t = str(text).lower()
    return any(kw in t for kw in _STRATEGIC_KW)


def _is_trivial(text: str) -> bool:
    t = str(text).strip().lower()
    if len(t) < 25:
        return True
    return t.startswith(_TRIVIAL_PATTERNS)


# ---------------------------------------------------------------------------
# Config resolution (hermes native — autonomy ile aynı desen)
# ---------------------------------------------------------------------------

def get_cognitive_config_from_hermes() -> Optional[Dict[str, Any]]:
    """Hermes full config'inden cognitive bölümünü oku (varsa)."""
    try:
        from hermes_cli.config import load_config_readonly
        section = (load_config_readonly() or {}).get("cognitive")
        return dict(section) if isinstance(section, dict) else None
    except Exception:
        return None


def _resolve_hook_config(agent: Any, config: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """config arg > agent._cognitive_section > hermes config. Never raises."""
    if isinstance(config, dict):
        return config
    try:
        agent_cfg = getattr(agent, "_cognitive_section", None)
        if isinstance(agent_cfg, dict):
            return agent_cfg
    except Exception:
        pass
    return get_cognitive_config_from_hermes()


# ---------------------------------------------------------------------------
# Bridge factory (testlerde fake ile ezilebilir)
# ---------------------------------------------------------------------------

def _make_bridge() -> Any:
    """V11 runtime_bridge.Bridge(dry_run=True) — canlı modüllere erişir ama
    dry_run olduğundan LLM yok. Testler bridge_factory enjekte edebilir."""
    if str(_COGNITIVE) not in sys.path:
        sys.path.insert(0, str(_COGNITIVE))
    from runtime_bridge import Bridge
    full = _env_mode() == "full"
    return Bridge(dry_run=not full)


# ---------------------------------------------------------------------------
# Ana kanca
# ---------------------------------------------------------------------------

def cognitive_hook(
    agent: Any,
    user_message: str,
    config: Optional[Dict[str, Any]] = None,
    bridge_factory: Optional[Callable[[], Any]] = None,
) -> Dict[str, Any]:
    """conversation_loop için tek cognitive kancası.

    Dönüş (her zaman):
      {action, reason, strategic, verdict, blocked, source,
       cognitive_result, latency_ms}
    - action: "skip" | "cognitive_active" | "blocked"
    - strategic: bool (bu çağrı stratejik sınıfa girdi mi)
    - blocked: fail-closed governance durumunda True
    - verdict: ADE/Board ya da SKIP
    ASLA raise etmez.
    """
    t0 = time.time()
    result = {
        "action": "skip",
        "reason": "default",
        "strategic": False,
        "verdict": "SKIP",
        "blocked": False,
        "source": "config",
        "cognitive_result": None,
        "latency_ms": 0,
        "preview": str(user_message)[:60] if user_message is not None else "",
    }

    cfg = _resolve_hook_config(agent, config)

    # Mod gates
    if _env_mode() == "disabled":
        result["reason"] = "mode_disabled"
        return result
    if not cfg:
        result["reason"] = "no_config"
        return result
    if not cfg.get("enabled", False):
        result["reason"] = "cognitive_disabled"
        return _log_and_return(result)

    mode = str(cfg.get("mode", "observe")).lower()
    if mode in ("off", "disabled"):
        result["reason"] = "mode_off"
        return _log_and_return(result)

    try:
        raw = str(user_message) if user_message is not None else ""
        if _is_trivial(raw):
            result.update(reason="non_strategic_trivial")
            return _log_and_return(result)

        strategic = bool(_looks_strategic(raw))
        if not strategic:
            result.update(reason="non_strategic")
            return _log_and_return(result)

        result["strategic"] = True
        try:
            outcome = _evaluate_strategic(raw, bridge_factory=bridge_factory)
        except Exception as exc:
            logger.debug("cognitive: evaluate failed (fail-open): %s", exc)
            result.update(
                action="skip", reason="evaluate_error",
                source="exception", verdict="SKIP",
            )
            return _log_and_return(result)

        result["cognitive_result"] = outcome
        result["verdict"] = outcome.get("verdict", "SKIP")
        result["source"] = outcome.get("source", "")
        result["blocked"] = bool(outcome.get("blocked", False))
        if outcome.get("blocked"):
            result.update(action="blocked", reason="governance_block")
        else:
            result.update(action="cognitive_active", reason="strategic_task")

    except Exception as exc:
        logger.debug("cognitive: hook error (fail-open): %s", exc)
        result.update(reason="hook_error:%s" % type(exc).__name__)

    result["latency_ms"] = round((time.time() - t0) * 1000, 1)
    return _log_and_return(result)


def _log_and_return(result: Dict[str, Any]) -> Dict[str, Any]:
    """Log one decision row per turn (ADIM 10 observability) then return the result."""
    try:
        logger.info(
            "cognitive_hook: action=%s verdict=%s strategic=%s blocked=%s source=%s "
            "latency_ms=%s reason=%s preview=%s",
            result.get("action", "-"), result.get("verdict", "-"), result.get("strategic", "-"),
            result.get("blocked", "-"), result.get("source", "-"),
            result.get("latency_ms", "-"), result.get("reason", "-"),
            result.get("preview", ""),
        )
        import json as _json
        _hh = os.environ.get("HERMES_HOME")
        if _hh:
            _path = os.path.join(_hh, "cognitive_hook_decisions.log")
            with open(_path, "a", encoding="utf-8") as fh:
                fh.write(_json.dumps(result, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass
    return result


def log_action_enforcement(decision_id, verdict, blocked, suppressed_tools, latency_ms=None):
    """ADIM 11: enforcement trace — BLOCK kararinin action katmanina ulastigini tek karar loguna yazar."""
    try:
        import json as _json
        _hh = os.environ.get("HERMES_HOME")
        if _hh:
            _entry = {
                "event": "action_enforcement",
                "ts": round(time.time(), 3),
                "decision_id": (decision_id or ""),
                "verdict": (verdict or ""),
                "blocked": bool(blocked),
                "suppressed_tools": list(suppressed_tools or []),
                "latency_ms": latency_ms,
            }
            _path = os.path.join(_hh, "cognitive_hook_decisions.log")
            with open(_path, "a", encoding="utf-8") as fh:
                fh.write(_json.dumps(_entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass


def _evaluate_strategic(question: str, bridge_factory: Optional[Callable[[], Any]] = None) -> Dict[str, Any]:
    """Stratejik karar değerlendirmesi — V11 cognitive_hook.evaluate politikası.

    ADIM 12: fast/dry-run modunda değerlendirme GÖZLEMSELDİR (OBSERVE).
    Placeholder ADE (dry_run → boş gövde) ve kanıtsız Board kararı governance
    authority kazanamaz; bu modda BLOCK üretilmez (no-enforcement). Gerçek
    enforcement yalnızca `full` modda (gerçek LLM muhakemesi) geçerlidir.

    Dönüş: {verdict, action, blocked, source, latency_ms, hooks:{...}}
    """
    t0 = time.time()
    factory = bridge_factory or _make_bridge
    b = factory()
    out: Dict[str, Any] = {}
    dry = _env_mode() != "full"
    out["mode"] = "dry_run" if dry else "full"

    # 1) LEARN lookup — her zaman (salt okuma, yan etki yok)
    try:
        lessons = b.lessons_for(question)
        if lessons:
            out["lessons_used"] = [les.get("lesson_id", "") for les in lessons]
            out["lesson_rule"] = lessons[0].get("rule", "")
    except Exception:
        out["lessons_error"] = True

    # 2) Karar katmanı — stratejikse canlı ADE (fast: dry) + canlı Board
    try:
        ade = b.decide_ade(
            question,
            context={"message": question},
            trigger="assumption_validation",
            dry_run=dry,
        )
        board = b.decide_board(question, fact_pack={"message": question})
        out["ade"] = ade.get("verdict", "HOLD")
        out["board"] = board.get("verdict", "DEFER")
        out["ade_action"] = ade.get("action", "wait")
        out["board_action"] = board.get("action", "wait")
        out["decision_id"] = ade.get("decision_id", "")
        src = "ade:%s+board:%s" % (out["ade"], out["board"])

        # ADIM 12: dry-run/placeholder kararı governance authority kazanamaz.
        # Bu modda sonuç GÖZLEMSELDİR: BLOCK yok, enforcement yok (fail-open).
        # ADE dry_run boş gövde döner; Board fact_pack'siz kural-bazlı oynar —
        # ikisi de gerçek muhakeme değildir, bu yüzden BLOCK üretemez.
        if dry:
            return {
                "verdict": "DRY_RUN", "action": "observe", "blocked": False,
                "dry_run": True, "source": src,
                "latency_ms": round((time.time() - t0) * 1000),
                "hooks": out,
            }

        if ade.get("action") == "block" or board.get("action") == "block":
            return {
                "verdict": "BLOCK", "action": "block", "blocked": True,
                "source": src, "latency_ms": round((time.time() - t0) * 1000),
                "hooks": out,
            }
        action = board.get("action") if ade.get("action") == "continue" else ade.get("action")
        return {
            "verdict": "CLEARED", "action": action, "blocked": False,
            "source": src, "latency_ms": round((time.time() - t0) * 1000),
            "hooks": out,
        }
    except Exception as exc:
        # ADE/Board altyapı hatası → fail-open SKIP (sadece ders danışmanlığı varsa ADVISED)
        if out.get("lessons_used"):
            return {
                "verdict": "ADVISED", "action": "continue_flagged", "blocked": False,
                "source": "lessons", "latency_ms": round((time.time() - t0) * 1000),
                "hooks": {**out, "decision_error": str(exc)[:200]},
            }
        return {
            "verdict": "SKIP", "action": "continue", "blocked": False,
            "source": "exception", "latency_ms": round((time.time() - t0) * 1000),
            "hooks": {**out, "decision_error": str(exc)[:200]},
        }


# ---------------------------------------------------------------------------
# Yardımcı: stratejik olduğunu önceden bilen çağıranlar için
# ---------------------------------------------------------------------------

def should_run_cognitive(user_message: str, config: Optional[Dict[str, Any]] = None) -> bool:
    """Bu mesaj cognitive katmanını uyandırmalı mı? (saf, yan etkisiz)"""
    if _env_mode() == "disabled":
        return False
    cfg = config if isinstance(config, dict) else get_cognitive_config_from_hermes()
    if not cfg or not cfg.get("enabled", False):
        return False
    mode = str(cfg.get("mode", "observe")).lower()
    if mode in ("off", "disabled"):
        return False
    if _is_trivial(user_message):
        return False
    return bool(_looks_strategic(str(user_message)))