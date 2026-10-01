"""Phase 18 testleri."""

import tempfile

from jeff_cognitive.demo import run_demo


def test_demo_runs():
    with tempfile.TemporaryDirectory() as tmp:
        out = run_demo(tmp)
        assert out["verdict"] in ("ACCEPT", "MODIFY", "VALIDATE_FIRST", "DEFER",
                                  "REJECT", "INSUFFICIENT_EVIDENCE")
        if not out.get("insufficient"):
            assert "Yonetici Ozeti" in out["summary"]
            assert out["replan"] in ("CONTINUE", "PIVOT", "PAUSE", "KILL",
                                     "ESCALATE", "RESEARCH")
            # kabul kriteri: acikca yanildim + en ucuz sonraki deney
            assert out["acknowledged_wrong"] and "Yanildim" in out["summary"]
            assert "en ucuz deney" in out["summary"]


def test_insufficient_evidence_path(monkeypatch):
    import jeff_cognitive.demo as demo_mod
    monkeypatch.setattr(demo_mod, "_jeff_leads", lambda: [])
    with tempfile.TemporaryDirectory() as tmp:
        out = run_demo(tmp)
        assert out["verdict"] == "INSUFFICIENT_EVIDENCE"
        assert out.get("insufficient", True) or "Yetersiz" in out["summary"]
