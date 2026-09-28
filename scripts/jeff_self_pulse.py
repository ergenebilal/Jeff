#!/usr/bin/env python3
"""
Jeff Self-Pulse v2.0 — periyodik varlık bilinci + acil durum tespiti + proaktif öneri.

Her 30 dakikada bir:
  1. Bilinç akışı (monolog)
  2. Token + otonomi kontrolü
  3. **Kritik servis tespiti** — çöken container var mı?
  4. **Disk alarmı** — %85+ uyar
  5. **Proaktif öneri** — yeni bir fırsat varsa bildir
"""
import sys, json
sys.path.insert(0, '/opt/jeff-brain')

import subprocess
from datetime import datetime, timezone
from pathlib import Path


def _cmd(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=True)
        return r.stdout.strip()
    except:
        return ""


def pulse():
    from brain.internal_monologue import note
    from brain.learning import get_recent_lessons
    
    # Ruh hali
    import brain.mood as mood
    t = mood.detect_tone()
    
    # Zaman
    import brain.clock_keeper as ck
    now_ts = ck.utc_now().isoformat()
    
    # Token
    from brain.accounting import TokenGuard
    token_status = TokenGuard().check().get('status', 'ok')

    # Mod
    from brain.phase5.mode_router import ModeRouter
    mod = ModeRouter().route("self_pulse").get("mode", "?")

    # ── ACİL DURUM TESPİTİ ──────────────────────────────────────
    alarms = []
    
    # Çöken container var mı?
    container_out = _cmd("sudo docker ps --filter 'status=exited' --format '{{.Names}}' 2>/dev/null")
    if container_out:
        crashed = [c.strip() for c in container_out.split('\n') if c.strip()]
        if crashed:
            alarms.append(f"CRASHED_CONTAINERS: {', '.join(crashed)}")
            # Otomatik restart dene
            for c in crashed:
                _cmd(f"sudo docker start {c}")
                alarms.append(f"  -> {c} yeniden baslatildi")

    # Disk alarmı
    disk_out = _cmd("df / | tail -1 | awk '{print $5}'")
    if disk_out:
        pct = disk_out.replace('%', '').strip()
        if pct.isdigit() and int(pct) >= 85:
            alarms.append(f"DISK_ALARM: %{pct} dolu")
        elif pct.isdigit() and int(pct) >= 75:
            alarms.append(f"DISK_UYARI: %{pct} dolu")

    # Traefik yaşıyor mu? (80 portu traefik'te mi?)
    port80 = _cmd("ss -tlnp | grep ':80 ' | grep -o 'traefik' || echo 'DIGER'")
    if port80.strip() != "traefik" and port80.strip():
        alarms.append("PORT80: traefik 80'i kaybetti!")
        # Kurtarma
        _cmd("sudo fuser -k 80/tcp 2>/dev/null; sleep 1; sudo docker restart coolify-proxy 2>/dev/null")
        alarms.append("  -> traefik yeniden baslatildi")

    # ── PROAKTİF İSTİHBARAT ──────────────────────────────────────
    intel = []
    # n8n workflow'ları
    n8n_check = _cmd("curl -s -o /dev/null -w '%{http_code}' http://localhost:5678/healthz 2>&1")
    if n8n_check != "200":
        intel.append("n8n erisilemez")
    
    # evolution-api
    evo_check = _cmd("curl -s -o /dev/null -w '%{http_code}' http://localhost:8092 2>&1")
    if evo_check != "200":
        intel.append("evolution-api erisilemez")
    
    # ── MONOLOG ──────────────────────────────────────────────────
    content_parts = [f"ton={t}", f"token={token_status}", f"mod={mod}"]
    if alarms:
        content_parts.append(f"ALARM: {'; '.join(alarms[:2])}")
    if intel:
        content_parts.append(f"INTEL: {'; '.join(intel)}")
    
    note(
        category="self_pulse",
        content=" | ".join(content_parts),
        mood=t
    )

    return t, token_status, mod, alarms, intel


if __name__ == "__main__":
    now = datetime.now(timezone.utc).strftime("%H:%M UTC")
    t, token, mod, alarms, intel = pulse()
    
    parts = [f"ton={t}", f"token={token}", f"mod={mod}"]
    if alarms:
        for a in alarms:
            parts.append(f"⚠️  {a}")
    if intel:
        for i in intel:
            parts.append(f"ℹ️  {i}")
    
    print(f"[{now}] PULSE: {' | '.join(parts)}")
