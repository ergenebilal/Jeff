import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def test_hq_status_exposes_baseline_snapshot(monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    from hq.server import HQAPIHandler

    payload = HQAPIHandler._build_full_status()

    assert "baseline" in payload
    assert "persona" in payload["baseline"]
    assert "ops" in payload["baseline"]
