"""Tests for V11 runtime hook (/home/hermes/jeff_cognitive/hook.py).

Hermetic: fake bridge (scripted verdicts), no live ADE/Board, no LLM.
Policy matrix mirrors cognitive_hook.py (P1 + ADIM 12):
- disabled mode → SKIP; cognitive.enabled=false → SKIP
- trivial → SKIP (no writes)
- non-strategic → SKIP
- strategic (full mod) → CLEARED / BLOCKED (fail-closed) / SKIP on error (fail-open)
- strategic (fast/dry-run, ADIM 12) → DRY_RUN / OBSERVE (NO enforcement)
- lessons consulted on every strategic evaluation

ADIM 12 notu: fast=default modda cognitive katmani GOZLEMSELDIR. Placeholder ADE
(dry_run → bos govde) ve kanitsiz Board karari governance authority kazanamaz;
bu modda BLOCK uretilmez. Gercek enforcement yalnizca COGNITIVE_HOOK_MODE=full.
"""

import os
import pytest

from jeff_cognitive import hook as JCH


# ---------------------------------------------------------------------------
# Fake bridge
# ---------------------------------------------------------------------------

class FakeBridge:
    """Scripted bridge — never touches live modules."""

    def __init__(self, ade_verdict="NORMAL", de_action="continue",
                 board_verdict="ACCEPT", bd_action="continue",
                 lessons=None):
        self.ade_verdict = ade_verdict
        self.ade_action = de_action or "continue"
        self.board_verdict = board_verdict
        self.board_action = bd_action or "continue"
        self.lessons = lessons or []
        self.calls = {"lessons_for": 0, "decide_ade": 0, "decide_board": 0}

    def lessons_for(self, text, limit=5):
        self.calls["lessons_for"] += 1
        return self.lessons

    def decide_ade(self, question, context=None, trigger="", dry_run=None):
        self.calls["decide_ade"] += 1
        return {"verdict": self.ade_verdict, "action": self.ade_action,
                "decision_id": "dec_test", "via": "fake"}

    def decide_board(self, question, fact_pack=None):
        self.calls["decide_board"] += 1
        return {"verdict": self.board_verdict, "action": self.board_action,
                "board_id": "b_test", "via": "fake"}


class FakeAgent:
    def __init__(self, cfg):
        self._cognitive_section = cfg


ENABLED = {
    "enabled": True,
    "mode": "observe",
    "budget_limit_usd": 0.10,
}

STRATEGIC_MSG = (
    "Bu ay için strateji planlama çalışması yap ve pazara giriş "
    "modeliyle ilgili önerileri detaylı sun"
)
CASUAL_MSG = "merhaba, nasılsın"
INFORMATIONAL = "Python nedir kısaca anlatır mısın"


@pytest.fixture
def fast_mode(monkeypatch):
    """ADIM 12: varsayilan fast mod (dry-run → observe)."""
    monkeypatch.delenv("COGNITIVE_HOOK_MODE", raising=False)
    return None


@pytest.fixture
def full_mode(monkeypatch):
    """Gercek muhakeme modu — karar dallari burada test edilir."""
    monkeypatch.setenv("COGNITIVE_HOOK_MODE", "full")
    return None


# ---------------------------------------------------------------------------
# Gates
# ---------------------------------------------------------------------------

def test_mode_disabled_env(monkeypatch):
    monkeypatch.setenv("COGNITIVE_HOOK_MODE", "disabled")
    r = JCH.cognitive_hook(FakeAgent(ENABLED), STRATEGIC_MSG)
    assert r["action"] == "skip"
    assert r["reason"] == "mode_disabled"


def test_cognitive_disabled_by_default():
    r = JCH.cognitive_hook(FakeAgent({"enabled": False}), STRATEGIC_MSG)
    assert r["action"] == "skip"
    assert r["reason"] == "cognitive_disabled"


def test_no_config_skips():
    r = JCH.cognitive_hook(None, STRATEGIC_MSG)
    assert r["action"] == "skip"


def test_mode_off_config():
    r = JCH.cognitive_hook(FakeAgent({"enabled": True, "mode": "off"}), STRATEGIC_MSG)
    assert r["action"] == "skip"
    assert r["reason"] == "mode_off"


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def test_trivial_message_skips():
    r = JCH.cognitive_hook(FakeAgent(ENABLED), CASUAL_MSG)
    assert r["action"] == "skip"
    assert r["strategic"] is False
    assert r["reason"] == "non_strategic_trivial"


def test_informational_question_skips():
    r = JCH.cognitive_hook(FakeAgent(ENABLED), INFORMATIONAL)
    assert r["action"] == "skip"
    assert r["strategic"] is False


# ---------------------------------------------------------------------------
# ADIM 12 — fast/dry-run = OBSERVE / NO-ENFORCEMENT  (yeni davranis)
# ---------------------------------------------------------------------------

def test_adim12_dryrun_no_block_on_ade_kill(fast_mode):
    """fast/dry-run: ADE KILL gelse bile BLOCK uretilmemeli."""
    b = FakeBridge(ade_verdict="KILL", de_action="block")
    r = JCH.cognitive_hook(FakeAgent(ENABLED), STRATEGIC_MSG, bridge_factory=lambda: b)
    assert r["blocked"] is False
    assert r["action"] == "cognitive_active"
    assert r["verdict"] == "DRY_RUN"
    assert r["cognitive_result"]["dry_run"] is True
    assert r["cognitive_result"]["hooks"]["mode"] == "dry_run"
    assert b.calls["decide_ade"] == 1


def test_adim12_dryrun_no_block_on_board_reject(fast_mode):
    """fast/dry-run: Board REJECT gelse bile BLOCK uretilmemeli."""
    b = FakeBridge(board_verdict="REJECT", bd_action="block")
    r = JCH.cognitive_hook(FakeAgent(ENABLED), STRATEGIC_MSG, bridge_factory=lambda: b)
    assert r["blocked"] is False
    assert r["action"] != "blocked"
    assert r["verdict"] == "DRY_RUN"


def test_adim12_dryrun_real_prod_signature(fast_mode):
    """Uretimde gozlenen tam sinyal: ade=HOLD + board=REJECT → artik BLOCK DEGIL."""
    b = FakeBridge(ade_verdict="HOLD", de_action="wait",
                   board_verdict="REJECT", bd_action="block")
    r = JCH.cognitive_hook(FakeAgent(ENABLED), STRATEGIC_MSG, bridge_factory=lambda: b)
    assert r["blocked"] is False, "Uretim sinyali hala blokluyor!"
    assert r["action"] != "blocked"
    assert r["verdict"] == "DRY_RUN"
    assert r["source"] == "ade:HOLD+board:REJECT"


def test_adim12_dryrun_still_consults_ade_and_board(fast_mode):
    """OBSERVE demek 'hic sorma' degil — ADE+Board yine cagrilir (denetim izi)."""
    b = FakeBridge()
    r = JCH.cognitive_hook(FakeAgent(ENABLED), STRATEGIC_MSG, bridge_factory=lambda: b)
    assert b.calls["decide_ade"] == 1
    assert b.calls["decide_board"] == 1
    assert b.calls["lessons_for"] >= 1


# ---------------------------------------------------------------------------
# Strategic path — full mod (gercek enforcement muhakemesi)
# ---------------------------------------------------------------------------

def test_strategic_clear_activates(full_mode):
    b = FakeBridge()
    r = JCH.cognitive_hook(FakeAgent(ENABLED), STRATEGIC_MSG, bridge_factory=lambda: b)
    assert r["action"] == "cognitive_active"
    assert r["strategic"] is True
    assert r["verdict"] == "CLEARED"
    assert r["blocked"] is False
    assert r["source"] == "ade:NORMAL+board:ACCEPT"
    assert b.calls["decide_ade"] == 1
    assert b.calls["decide_board"] == 1
    assert b.calls["lessons_for"] >= 1


def test_strategic_blocked_on_ade_kill(full_mode):
    b = FakeBridge(ade_verdict="KILL", de_action="block")
    r = JCH.cognitive_hook(FakeAgent(ENABLED), STRATEGIC_MSG, bridge_factory=lambda: b)
    assert r["action"] == "blocked"
    assert r["blocked"] is True
    assert r["verdict"] == "BLOCK"


def test_strategic_blocked_on_board_reject(full_mode):
    b = FakeBridge(board_verdict="REJECT", bd_action="block")
    r = JCH.cognitive_hook(FakeAgent(ENABLED), STRATEGIC_MSG, bridge_factory=lambda: b)
    assert r["action"] == "blocked"
    assert r["blocked"] is True
    assert r["verdict"] == "BLOCK"


def test_strategic_lessons_consulted(fast_mode):
    lesson = {
        "lesson_id": "L1", "rule": "Yorum sessizligi talep kaniti degildir",
        "applies_to": "strateji", "scope": "pazar", "lesson": "ders",
    }
    b = FakeBridge(lessons=[lesson])
    r = JCH.cognitive_hook(FakeAgent(ENABLED), STRATEGIC_MSG, bridge_factory=lambda: b)
    cr = r["cognitive_result"]
    assert cr["hooks"]["lessons_used"] == ["L1"]
    assert "sessizligi" in cr["hooks"].get("lesson_rule", "")


# ---------------------------------------------------------------------------
# Fail-open behavior
# ---------------------------------------------------------------------------

def test_bridge_error_fails_open(fast_mode):
    class ExplodingBridge:
        def lessons_for(self, text, limit=5):
            raise RuntimeError("no live modules")

    r = JCH.cognitive_hook(FakeAgent(ENABLED), STRATEGIC_MSG,
                           bridge_factory=lambda: ExplodingBridge())
    # lessons_for patladı → _evaluate_strategic yakalar → SKIP fallback
    assert r["action"] in ("skip", "cognitive_active")
    assert r["blocked"] is False


def test_ade_error_with_lessons_advises(fast_mode):
    class LessonsOnlyBridge:
        def lessons_for(self, text, limit=5):
            return [{"lesson_id": "L9", "rule": "kural", "applies_to": "x"}]

        def decide_ade(self, question, context=None, trigger="", dry_run=None):
            raise RuntimeError("ade down")

        def decide_board(self, question, fact_pack=None):
            raise RuntimeError("board down")

    r = JCH.cognitive_hook(FakeAgent(ENABLED), STRATEGIC_MSG,
                           bridge_factory=lambda: LessonsOnlyBridge())
    assert r["blocked"] is False
    assert r["action"] in ("skip", "cognitive_active")


def test_hook_never_raises():
    """Kanca her koşulda raise etmemeli."""
    # garip/None mesaj
    r = JCH.cognitive_hook(FakeAgent(ENABLED), None)
    assert "action" in r and "latency_ms" in r
    # bozuk config
    r2 = JCH.cognitive_hook(FakeAgent({"enabled": "not-a-bool"}), STRATEGIC_MSG)
    assert "action" in r2


# ---------------------------------------------------------------------------
# should_run_cognitive
# ---------------------------------------------------------------------------

def test_should_run_disabled(monkeypatch):
    monkeypatch.setenv("COGNITIVE_HOOK_MODE", "disabled")
    assert JCH.should_run_cognitive(STRATEGIC_MSG, ENABLED) is False


def test_should_run_strategic():
    assert JCH.should_run_cognitive(STRATEGIC_MSG, ENABLED) is True


def test_should_run_casual():
    assert JCH.should_run_cognitive(CASUAL_MSG, ENABLED) is False
