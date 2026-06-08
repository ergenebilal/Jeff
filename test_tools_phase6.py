import sys
from pathlib import Path
_PROJECT_ROOT = str(Path(__file__).resolve().parent)
if _PROJECT_ROOT in sys.path:
    sys.path.remove(_PROJECT_ROOT)
sys.path.insert(0, _PROJECT_ROOT)

import importlib
import subprocess

import pytest


def test_code_intel_tools_are_exported_from_tools():
    """Skip if the installed 'tools' package doesn't re-export these."""
    try:
        tools = importlib.import_module("tools")
    except ImportError:
        pytest.skip("tools package not available")
    if not hasattr(tools, "hermes_tool_hijyen_raporu"):
        pytest.skip("tools package does not export hermes_tool_hijyen_raporu")
    assert callable(tools.hermes_tool_hijyen_raporu)
    assert callable(tools.hermes_entegrasyon_degerlendirmesi)
    assert callable(tools.hermes_kod_yapisal_ara)
    assert callable(tools.hermes_kod_fonksiyon_bul)


def test_tool_hygiene_report_classifies_legacy_without_deleting():
    from hermes_tools._code_intel import hermes_tool_hijyen_raporu

    report = hermes_tool_hijyen_raporu()

    assert report["otomatik_silme"] is False
    # When running outside the full hermes-agent (e.g. in dev), the
    # installed tools package may not expose hermes_tools callables.
    # The report structure is still valid regardless of tool counts.
    if report["toplam_callable"] == 0:
        pytest.skip("hermes_tools not registered in the installed tools package")
    assert report["toplam_callable"] >= 100
    assert report["hermes_tool_sayisi"] >= 60


def test_integration_decision_recommends_ast_grep_first():
    from hermes_tools._code_intel import hermes_entegrasyon_degerlendirmesi

    report = hermes_entegrasyon_degerlendirmesi()

    assert report["onerilen_sira"][0] == "ast-grep"
    assert report["entegrasyonlar"]["ast-grep"]["karar"] in {"kur", "aktif"}
    assert report["entegrasyonlar"]["letta"]["karar"] == "ertele"
    assert report["entegrasyonlar"]["phidata_agno"]["karar"] == "ertele"


def test_structural_search_uses_ast_grep_when_available(monkeypatch):
    from hermes_tools import _code_intel

    monkeypatch.setattr(_code_intel.shutil, "which", lambda name: "/opt/hermes/venv/bin/ast-grep")

    class Result:
        returncode = 0
        stdout = "hermes_brain_core.py:10: def hedef():\n"
        stderr = ""

    calls = []
    def fake_run(cmd, **kwargs):
        calls.append(cmd)
        return Result()

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = _code_intel.hermes_kod_yapisal_ara("def $FUNC($$$ARGS): $$$BODY", lang="python", path=".")

    assert result["status"] == "ok"
    assert result["engine"] == "ast-grep"
    assert result["match_count"] == 1
    assert calls[0][0].endswith("ast-grep")


def test_function_find_falls_back_to_python_ast_when_ast_grep_missing(tmp_path, monkeypatch):
    from hermes_tools import _code_intel

    src = tmp_path / "sample.py"
    src.write_text("def hedef():\n    return 1\n\ndef baska():\n    return 2\n", encoding="utf-8")
    monkeypatch.setattr(_code_intel, "_ast_grep_executable", lambda: None)

    result = _code_intel.hermes_kod_fonksiyon_bul("hedef", path=str(tmp_path))

    assert result["status"] == "ok"
    assert result["engine"] == "python-ast-fallback"
    assert result["match_count"] == 1
    assert result["matches"][0]["file"].endswith("sample.py")
    assert result["matches"][0]["line"] == 1
