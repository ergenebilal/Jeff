"""Proactive reporting engine for Hermes."""

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


REPORT_STATE = Path.home() / ".hermes" / "learning" / "report_state.json"
DEFAULT_TARGET = os.environ.get("HERMES_REPORT_TARGET", "telegram")


def generate_health_report() -> str:
    """Build a concise UTC health report."""
    lines = ["📊 HERMES DURUM RAPORU", f"🕐 {datetime.now(timezone.utc).strftime('%d %b %Y, %H:%M UTC')}", ""]
    services = _check_services()
    lines.append("Servisler: " + " · ".join(f"{'✅' if ok else '⬜' if name == 'n8n' else '❌'} {name}" for name, ok in services.items()))

    try:
        from brain.token import TokenGuard

        guard = TokenGuard.check()
        usage = float(guard.get("usage", 0.0))
        budget = float(guard.get("budget_left", 0.5))
        icon = {"ok": "✅", "warn": "⚠️", "flash": "🔴", "stop": "🛑"}.get(guard.get("status", "ok"), "✅")
        lines.append(f"Token: {icon} ${usage:.2f} kullanıldı · kalan ${budget:.2f}")
    except Exception:
        lines.append("Token: ⬜ bilinmiyor")

    try:
        from brain.reasoning_tree import get_recent

        decisions = get_recent(100)
        total = len(decisions)
        succeeded = sum(1 for item in decisions if item.get("outcome") == "success")
        failed = sum(1 for item in decisions if item.get("outcome") == "failed")
        lines.append(f"Kararlar: {total} toplam · ✅ {succeeded} başarılı · ❌ {failed} başarısız")
    except Exception:
        pass

    try:
        from brain.learning import get_recent_lessons

        lines.append(f"Dersler: {len(get_recent_lessons(100))} aktif")
    except Exception:
        pass

    system = _system_snapshot()
    if system:
        lines.append(f"Sistem: {system.get('mem_available_mb', 0)}MB RAM boş · {system.get('disk_free_gb', 0)}GB disk boş")
    return "\n".join(lines)


def collect_state() -> dict:
    """Collect a compact state used for change detection."""
    token_usage = 0.0
    try:
        from brain.token import TokenGuard

        token_usage = float(TokenGuard.check().get("usage", 0.0))
    except Exception:
        pass
    decision_count = 0
    try:
        from brain.reasoning_tree import get_recent

        decision_count = len(get_recent(100))
    except Exception:
        pass
    lesson_count = 0
    try:
        from brain.learning import get_recent_lessons

        lesson_count = len(get_recent_lessons(100))
    except Exception:
        pass
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": _check_services(),
        "token_usage": token_usage,
        "decision_count": decision_count,
        "lesson_count": lesson_count,
    }


def generate_change_report(old_state: dict, new_state: dict) -> Optional[str]:
    """Return a report only when state changed."""
    changes = []
    old_services = old_state.get("services", {})
    new_services = new_state.get("services", {})
    for service in sorted(set(old_services) | set(new_services)):
        old_value = old_services.get(service)
        new_value = new_services.get(service)
        if old_value != new_value:
            changes.append(f"{'✅' if new_value else '❌'} {service}: {'canlı' if new_value else 'düştü'}")

    old_token = float(old_state.get("token_usage", 0.0))
    new_token = float(new_state.get("token_usage", 0.0))
    if abs(new_token - old_token) > 0.01:
        changes.append(f"💰 Token: ${old_token:.2f} → ${new_token:.2f}")

    old_decisions = int(old_state.get("decision_count", 0))
    new_decisions = int(new_state.get("decision_count", 0))
    if new_decisions > old_decisions:
        changes.append(f"🧠 +{new_decisions - old_decisions} yeni karar")

    old_lessons = int(old_state.get("lesson_count", 0))
    new_lessons = int(new_state.get("lesson_count", 0))
    if new_lessons > old_lessons:
        changes.append(f"📚 +{new_lessons - old_lessons} yeni ders")

    if not changes:
        return None
    return "\n".join(["📊 DURUM DEĞİŞİKLİĞİ", f"🕐 {datetime.now(timezone.utc).isoformat()}"] + changes)


def generate_token_alert() -> Optional[str]:
    try:
        from brain.token import TokenGuard

        guard = TokenGuard.check()
        status = guard.get("status")
        if status == "warn":
            return f"⚠️ Token limitinin %75'ine ulaşıldı. ${guard.get('usage', 0):.2f} kullanıldı."
        if status == "flash":
            return "🔴 Token limitinin %90'ına ulaşıldı! Flash moduna geçiliyor."
        if status == "stop":
            return "🛑 Token limiti AŞILDI! Yeni seans başlatılamaz."
    except Exception:
        pass
    return None


def run_report_cycle(dry_run: bool = False) -> dict:
    """Send a report only when something changed, then persist new state."""
    old_state = _load_report_state()
    new_state = collect_state()
    report = generate_health_report() if not old_state else generate_change_report(old_state, new_state)
    alert = generate_token_alert()
    if alert:
        report = f"{report}\n\n{alert}" if report else alert
    _save_report_state(new_state)
    if not report:
        return {"sent": False, "reason": "no_change"}
    result = send_report(report, dry_run=dry_run)
    return {"sent": not dry_run and result.get("exit_code") == 0, "report": report, **result}


def send_report(text: str, target: str = DEFAULT_TARGET, dry_run: bool = False) -> dict:
    """Send a report through Hermes CLI. Dry-run never shells out."""
    if dry_run:
        return {"dry_run": True, "target": target, "text": text}
    command = ["/opt/hermes/venv/bin/hermes", "send", "--to", target, text]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=20, check=False)
        return {"dry_run": False, "target": target, "exit_code": result.returncode, "stdout": result.stdout[-500:], "stderr": result.stderr[-500:]}
    except Exception as exc:
        return {"dry_run": False, "target": target, "exit_code": -1, "stderr": str(exc)}


def _check_services() -> dict:
    checks = {
        "gateway": ("systemctl", "is-active", "hermes-gateway.service"),
        "embedding": ("curl", "-sf", "http://127.0.0.1:8767/health"),
        "headroom": ("curl", "-sf", "http://127.0.0.1:8787/health"),
        "n8n": ("curl", "-sf", "http://127.0.0.1:5678/health"),
    }
    result = {}
    for name, command in checks.items():
        try:
            completed = subprocess.run(command, capture_output=True, text=True, timeout=5, check=False)
            result[name] = completed.returncode == 0
        except Exception:
            result[name] = False
    return result


def _system_snapshot() -> dict:
    try:
        mem = {}
        with open("/proc/meminfo", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith(("MemTotal", "MemAvailable")):
                    parts = line.split()
                    mem[parts[0].rstrip(":")] = int(parts[1]) // 1024
        st = os.statvfs("/")
        return {"mem_available_mb": mem.get("MemAvailable", 0), "disk_free_gb": st.f_frsize * st.f_bfree // (1024**3)}
    except Exception:
        return {}


def _load_report_state() -> dict:
    try:
        return json.loads(REPORT_STATE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_report_state(state: dict):
    REPORT_STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = REPORT_STATE.with_suffix(REPORT_STATE.suffix + ".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(REPORT_STATE)


if __name__ == "__main__":
    print(json.dumps(run_report_cycle(), ensure_ascii=False, indent=2))
