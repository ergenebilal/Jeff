"""Phase 5 testleri."""

import pytest

from jeff_cognitive import CognitiveState
from jeff_cognitive.ade import DecisionProposal, assert_labeled, challenge, heuristic_verdict


def _prop(**kw):
    base = dict(thesis="T", antithesis="A", evidence=[], counter_evidence=[],
                uncertainty=0.2, customer_problem_strength=0.9,
                payment_potential=0.9, economic_viability=0.8, capability=0.9)
    base.update(kw)
    return DecisionProposal(**base)


def test_strong_case_accepts():
    assert heuristic_verdict(_prop())["verdict"] == "ACCEPT"


def test_weak_case_rejects():
    p = _prop(customer_problem_strength=0.05, payment_potential=0.05,
              economic_viability=0.05, capability=0.1, uncertainty=0.8)
    assert heuristic_verdict(p)["verdict"] == "REJECT"


def test_unknown_never_true():
    with pytest.raises(ValueError):
        assert_labeled([{"content": "x", "level": "TRUE"}])
    # etiketsiz → UNKNOWN varsayilmaz, hata verir (aciklik sart)
    with pytest.raises(ValueError):
        assert_labeled([{"content": "x", "level": "BELKI"}])


def test_verified_needs_source():
    with pytest.raises(ValueError):
        assert_labeled([{"content": "x", "level": "VERIFIED", "source": ""}])


def test_challenge_records_to_state():
    s = CognitiveState(objective="X")
    out = challenge(_prop(), state=s, board_fn={"verdict": "MODIFY"},
                    next_experiment="deney-1")
    assert out["verdict"] == "MODIFY" and out["via"] == "board-stub"
    assert s.decisions[-1]["kind"] == "ade_challenge"
    assert s.decisions[-1]["next_experiment"] == "deney-1"


def test_real_board_authoritative():
    import pytest as _pt
    import os
    if os.environ.get('JEFF_COGNITIVE_LIVE_TESTS') != '1':
        _pt.skip('live Board requires explicit isolated runtime opt-in')
    board_file = "/home/hermes/backups/pre-surgery-checkpoint-20260904/jeff_v2/board_deliberation.py"
    import os as _os
    if not _os.path.exists(board_file):
        _pt.skip("yedek board yok (sadece hermes sunucusunda)")
    s = CognitiveState(objective="X")
    out = challenge(_prop(), state=s, board_fn=None)
    assert out["via"] == "board", f"board yuklenemedi: {out.get('board_error')}"
    assert out["verdict"] in ("ACCEPT", "MODIFY", "REJECT", "DEFER", "VALIDATE_FIRST")
