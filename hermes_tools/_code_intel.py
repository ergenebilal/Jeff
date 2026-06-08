"""Read-only code intelligence and tool hygiene helpers for Hermes."""
from __future__ import annotations

import ast
import importlib.util
import inspect
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _callable_rows() -> list[tuple[str, str]]:
    import tools

    rows: list[tuple[str, str]] = []
    for name, value in vars(tools).items():
        if name.startswith("__") or not callable(value):
            continue
        module = getattr(value, "__module__", "")
        if module.startswith("hermes_tools"):
            rows.append((name, module))
    return rows


def hermes_tool_hijyen_raporu() -> dict[str, Any]:
    """Return a read-only report of useful, legacy, and quarantine-candidate tools."""
    rows = _callable_rows()
    hermes_names = sorted(name for name, _ in rows if name.startswith("hermes_"))
    legacy_names = sorted(name for name, _ in rows if not name.startswith("hermes_"))

    quarantine_candidates = []
    legacy_blob = Path(__file__).with_name("_legacy.py").read_text(encoding="utf-8", errors="ignore")
    candidate_rules = [
        ("chromadb", "ChromaDB emekli; sadece eski fallback/test uyumlulugu icin duruyor."),
        ("longtracer", "Opsiyonel dogrulama bagimliligi; kurulu degilse verify_claim UNKNOWN doner."),
        ("n8n_redirect", "n8n workflow kapsam disi; sadece eski Google OAuth redirect metni kalmis."),
    ]
    for key, reason in candidate_rules:
        if key == "n8n_redirect":
            present = "n8n.aiergene.xyz" in legacy_blob
        else:
            present = key.lower() in legacy_blob.lower()
        if present:
            quarantine_candidates.append({"ad": key, "sebep": reason, "aksiyon": "karantina/ayri modul planla"})

    return {
        "toplam_callable": len(rows),
        "hermes_tool_sayisi": len(hermes_names),
        "legacy_callable_sayisi": len(legacy_names),
        "legacy_ornekleri": legacy_names[:20],
        "karantina_adaylari": quarantine_candidates,
        "otomatik_silme": False,
        "neden_silme_yok": "Legacy fonksiyonlarin bir kismi testlerde ve dis veri snapshot akisi icinde kullaniliyor.",
        "onerilen_temizlik": [
            "Chroma/LongTracer eski araclarini dogrudan silmeden once kullanim testlerini ayir.",
            "Google/Gmail/Sheets araclarini _google.py modulune tasi ve canli yazimlari onay kapisinda tut.",
            "Legacy dosyasini konu bazli modullere bol; public import uyumlulugunu koru.",
        ],
    }


def _is_installed(module_name: str | None = None, executable: str | None = None) -> bool:
    if executable and (shutil.which(executable) or Path(f"/opt/hermes/venv/bin/{executable}").exists()):
        return True
    if module_name and importlib.util.find_spec(module_name):
        return True
    return False


def _ast_grep_executable() -> str | None:
    """Return the ast-grep binary, avoiding Linux's unrelated /usr/bin/sg."""
    found = shutil.which("ast-grep")
    if found:
        return found
    venv_binary = Path("/opt/hermes/venv/bin/ast-grep")
    if venv_binary.exists():
        return str(venv_binary)
    return None


def hermes_entegrasyon_degerlendirmesi() -> dict[str, Any]:
    """Evaluate requested external repos without mutating Hermes."""
    ast_grep_ready = _is_installed(executable="ast-grep")
    aider_ready = _is_installed(module_name="aider", executable="aider")
    letta_ready = _is_installed(module_name="letta")
    agno_ready = _is_installed(module_name="agno") or _is_installed(module_name="phi")

    return {
        "onerilen_sira": ["ast-grep", "aider-dry-run", "letta-evaluation", "agno-evaluation"],
        "entegrasyonlar": {
            "ast-grep": {
                "karar": "aktif" if ast_grep_ready else "kur",
                "fayda": "Kod yapisini AST ile hizli ve read-only tarar; Hermes'in hata/fonksiyon bulma kalitesini hemen artirir.",
                "risk": "Dusuk; varsayilan kullanim okuma modunda.",
            },
            "aider": {
                "karar": "dry_run_onay_kapisi",
                "kurulu": aider_ready,
                "fayda": "Diff tabanli patch disiplini saglar.",
                "risk": "Dosya degistirebildigi icin otomatik uygulama degil, once patch plani/onay gerekir.",
            },
            "letta": {
                "karar": "ertele",
                "kurulu": letta_ready,
                "fayda": "Stateful agent hafizasi icin guclu platform.",
                "risk": "Hermes'te Mnemosyne zaten aktif; hemen kurmak bellek katmanini karmasiklastirir.",
            },
            "phidata_agno": {
                "karar": "ertele",
                "kurulu": agno_ready,
                "fayda": "Agent/knowledge framework olarak faydali olabilir.",
                "risk": "Phidata Agno'ya tasindi; once Hermes'in mevcut karar/knowledge arayuzune adapter tasarlanmasi gerekir.",
            },
        },
    }


def _parse_ast_grep_stdout(stdout: str, max_sonuc: int) -> list[dict[str, Any]]:
    matches: list[dict[str, Any]] = []
    for raw in stdout.splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = line.split(":", 2)
        match: dict[str, Any] = {"text": line}
        if len(parts) >= 2 and parts[1].isdigit():
            match.update({"file": parts[0], "line": int(parts[1])})
            if len(parts) == 3:
                match["snippet"] = parts[2].strip()
        matches.append(match)
        if len(matches) >= max_sonuc:
            break
    return matches


def hermes_kod_yapisal_ara(pattern: str, lang: str = "python", path: str = ".", max_sonuc: int = 20) -> dict[str, Any]:
    """Search code with ast-grep in read-only mode."""
    if not isinstance(pattern, str) or not pattern.strip():
        return {"status": "error", "error": "pattern bos olamaz", "matches": []}
    executable = _ast_grep_executable()
    if executable is None:
        return {
            "status": "unavailable",
            "engine": "ast-grep",
            "matches": [],
            "match_count": 0,
            "install_hint": "/opt/hermes/venv/bin/pip install ast-grep-cli",
        }

    cmd = [executable, "--pattern", pattern, "--lang", lang, str(path)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
    except Exception as exc:
        return {"status": "error", "engine": "ast-grep", "error": str(exc), "matches": [], "match_count": 0}

    matches = _parse_ast_grep_stdout(result.stdout, max_sonuc=max_sonuc)
    return {
        "status": "ok" if result.returncode in (0, 1) else "error",
        "engine": "ast-grep",
        "returncode": result.returncode,
        "matches": matches,
        "match_count": len(matches),
        "stderr": result.stderr.strip()[:500],
    }


def hermes_kod_fonksiyon_bul(function_name: str, path: str = ".", max_sonuc: int = 20) -> dict[str, Any]:
    """Find Python function definitions using ast-grep, with Python AST fallback."""
    if not isinstance(function_name, str) or not function_name.strip():
        return {"status": "error", "error": "function_name bos olamaz", "matches": []}

    pattern = f"def {function_name.strip()}($$$ARGS): $$$BODY"
    if _ast_grep_executable():
        result = hermes_kod_yapisal_ara(pattern, lang="python", path=path, max_sonuc=max_sonuc)
        if result.get("status") == "ok" and result.get("match_count", 0) > 0:
            return result

    root = Path(path)
    files = [root] if root.is_file() else list(root.rglob("*.py"))
    matches: list[dict[str, Any]] = []
    for file_path in files:
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
                matches.append({"file": str(file_path), "line": node.lineno, "name": node.name})
                if len(matches) >= max_sonuc:
                    break
        if len(matches) >= max_sonuc:
            break
    return {
        "status": "ok",
        "engine": "python-ast-fallback",
        "matches": matches,
        "match_count": len(matches),
    }
