#!/usr/bin/env python3.11
"""Hermes Self-Evolve: haftalik kalite raporu ve gelisme onerisi."""

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

HERMES_DATA = Path("/home/hermes/hermes_data")
LOGS_DIR = Path("/home/hermes/logs")


def _git_log_son_7_gun() -> str:
    """Son 7 gundeki commitleri getir."""
    try:
        since = (datetime.now() - timedelta(days=7)).isoformat(timespec="seconds")
        result = subprocess.run(
            ["git", "log", "--oneline", f"--since={since}"],
            cwd=str(HERMES_DATA),
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if result.returncode != 0:
            return "(git repo yok veya git log okunamadi)"
        return result.stdout.strip() or "(son 7 gunde commit yok)"
    except Exception as e:
        return f"(git hatasi: {e})"


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _satir_say(dosya: str) -> int:
    """Bir dosyanin satir sayisini olc."""
    text = _read_text(HERMES_DATA / dosya)
    return len(text.splitlines()) if text else 0


def _fonksiyon_say(dosya: str) -> int:
    """Bir dosyadaki def sayisini say."""
    text = _read_text(HERMES_DATA / dosya)
    return sum(1 for line in text.splitlines() if line.strip().startswith("def "))


def _test_sayisi() -> dict:
    """tests/ dizinindeki test fonksiyonu sayisini ve py_compile kontrolu."""
    test_dir = HERMES_DATA / "tests"
    if not test_dir.exists():
        return {"toplam_test": 0, "dosya_sayisi": 0, "syntax_hatasi": 0}
    test_dosyalari = list(test_dir.glob("test_*.py"))
    toplam = 0
    syntax_hatasi = 0
    for test_path in test_dosyalari:
        text = _read_text(test_path)
        try:
            compile(text, str(test_path), "exec")
            toplam += sum(1 for line in text.splitlines() if line.strip().startswith("def test_"))
        except SyntaxError:
            syntax_hatasi += 1
    return {"toplam_test": toplam, "dosya_sayisi": len(test_dosyalari), "syntax_hatasi": syntax_hatasi}


def _kalite_skoru(tools_satir: int, brain_satir: int, test_sayisi: int) -> float:
    """Kabataslak kalite skoru (100 uzerinden)."""
    puan = 50.0
    if tools_satir <= 3000:
        puan += 15
    elif tools_satir <= 4000:
        puan += 5
    if brain_satir <= 4000:
        puan += 15
    elif brain_satir <= 5000:
        puan += 5
    if test_sayisi >= 300:
        puan += 20
    elif test_sayisi >= 200:
        puan += 10
    elif test_sayisi >= 100:
        puan += 5
    return round(puan, 1)


def rapor_uret() -> dict:
    """Ana raporu olustur."""
    tools_satir = _satir_say("tools.py")
    tools_func = _fonksiyon_say("tools.py")
    brain_satir = _satir_say("hermes_brain_core.py")
    brain_func = _fonksiyon_say("hermes_brain_core.py")
    hermes_tools_items = len(list(HERMES_DATA.joinpath("hermes_tools").glob("*.py"))) if HERMES_DATA.joinpath("hermes_tools").exists() else 0
    hermes_tools_satir = sum(_satir_say(f"hermes_tools/{f.name}") for f in HERMES_DATA.joinpath("hermes_tools").glob("*.py")) if HERMES_DATA.joinpath("hermes_tools").exists() else 0
    measured_tools_satir = hermes_tools_satir or tools_satir
    test = _test_sayisi()
    git_log = _git_log_son_7_gun()
    skor = _kalite_skoru(measured_tools_satir, brain_satir, test.get("toplam_test", 0))

    return {
        "tarih": datetime.now().isoformat(),
        "kalite_skoru": skor,
        "hermes_tools": {"satir": hermes_tools_satir, "dosya": hermes_tools_items},
        "tools.py": {"satir": tools_satir, "fonksiyon": tools_func},
        "hermes_brain_core.py": {"satir": brain_satir, "fonksiyon": brain_func},
        "test": test,
        "git_log": git_log,
    }


def rapor_formatla(rapor: dict) -> str:
    """Raporu Telegram mesajina cevir."""
    satirlar = ["Hermes Kalite Raporu\n"]
    satirlar.append(f"Skor: {rapor['kalite_skoru']}/100\n")
    hermes_tools = rapor.get("hermes_tools")
    if hermes_tools:
        satirlar.append(f"Hermes Tools: {hermes_tools['dosya']} dosya, {hermes_tools['satir']} satir")
    elif "tools.py" in rapor:
        satirlar.append(f"tools.py: {rapor['tools.py']['satir']} satir, {rapor['tools.py']['fonksiyon']} fonksiyon")
    satirlar.append(f"hermes_brain_core.py: {rapor['hermes_brain_core.py']['satir']} satir, {rapor['hermes_brain_core.py']['fonksiyon']} fonksiyon")
    t = rapor.get("test", {})
    satirlar.append(f"Test: {t.get('toplam_test', '?')} test, {t.get('dosya_sayisi', '?')} dosya, {t.get('syntax_hatasi', 0)} syntax hatasi\n")
    satirlar.append(f"Son 7 gun:\n{rapor['git_log']}\n")
    if rapor["kalite_skoru"] < 50:
        satirlar.append("🚨 Skor kritik — mudahale gerekli.")
    elif rapor["kalite_skoru"] < 70:
        satirlar.append("⚠️ Skor 70 alti — refaktor onerilir.")
    else:
        satirlar.append("✅ Skor stabil.")
    return "\n".join(satirlar)


def main() -> int:
    rapor = rapor_uret()
    mesaj = rapor_formatla(rapor)
    print(mesaj)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_DIR / "self_evolve.log"
    log_path.write_text(json.dumps(rapor, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
