"""Phase 8 testleri."""

from jeff_cognitive.calibration import Calibrator


def test_small_n_unavailable():
    c = Calibrator()
    c.add(0.7, 0.7, 0.2)
    c.add(0.6, 0.6, 0.6)
    c.add(0.8, 0.8, 0.1)
    s = c.summary()
    assert s["status"].startswith("unavailable") and s["n"] == 3


def test_large_n_available():
    c = Calibrator()
    for i in range(50):
        c.add(0.7, 0.7, 0.2, decision_type="pricing", domain="real-estate")
    s = c.summary()
    assert s["status"] == "available" and s["n"] == 50
    assert s["overconfidence_rate"] == 1.0  # hep asiri tahmin
    assert s["by_type_mae"]["pricing"] > 0
    assert s["success_rate"] == 0.0  # hata hep 0.5 > tolerans


def test_success_rate():
    c = Calibrator()
    for i in range(30):
        c.add(0.5, 0.6, 0.55)  # hata 0.05 → basarili
    s = c.summary()
    assert s["success_rate"] == 1.0
