#!/usr/bin/env python3
"""
Jeff Self-Health — acil durum refleksleri ve kendini iyileştirme.
Her 10 dakikada bir çalışır:
  - Çöken container'ları restartla
  - Traefik 80 portunu koru
  - Disk %90+ ise acil temizlik yap
  - Token aşımı varsa uyar
"""
import subprocess, json, os
from datetime import datetime, timezone
from pathlib import Path

HEALTH_LOG = Path.home() / ".hermes" / "logs" / "self_health.jsonl"
HEALTH_LOG.parent.mkdir(parents=True, exist_ok=True)


def _cmd(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=True)
        return r.stdout.strip() or r.stderr.strip()
    except:
        return ""


def _log(entry: dict):
    try:
        with HEALTH_LOG.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except:
        pass


def heal():
    actions = []
    now = datetime.now(timezone.utc)

    # 1. Çöken container'ları restartla
    crashed = _cmd("sudo docker ps --filter 'status=exited' --format '{{.Names}}' 2>/dev/null")
    for name in crashed.strip().split('\n'):
        name = name.strip()
        if not name:
            continue
        r = _cmd(f"sudo docker start {name} 2>&1")
        actions.append(f"restart:{name}={'ok' if 'Error' not in r else 'fail'}")

    # 2. Traefik 80 portu
    port80 = _cmd("ss -tlnp | grep ':80 ' | grep -o 'traefik' || echo 'lost'")
    if port80.strip() == "lost":
        _cmd("sudo fuser -k 80/tcp 2>/dev/null; sleep 1; sudo docker restart coolify-proxy 2>/dev/null")
        actions.append("traefik:restart")

    # 3. Disk %90+
    disk_pct = _cmd("df / | tail -1 | awk '{print $5}'").replace('%', '').strip()
    if disk_pct.isdigit() and int(disk_pct) >= 90:
        _cmd("sudo docker system prune -af --volumes 2>/dev/null")
        _cmd("sudo journalctl --vacuum-time=3d 2>/dev/null")
        actions.append(f"disk:emergency_cleanup({disk_pct}%)")
    elif disk_pct.isdigit() and int(disk_pct) >= 85:
        _cmd("sudo docker system prune -f 2>/dev/null")
        _cmd("sudo journalctl --vacuum-time=7d 2>/dev/null")
        actions.append(f"disk:cleanup({disk_pct}%)")

    # 4. Embedding daemon
    emb = _cmd("curl -s -o /dev/null -w '%{http_code}' http://localhost:8767/health 2>&1 || echo 'dead'")
    if emb.strip() == "dead":
        _cmd("sudo docker restart ollama 2>/dev/null")  # embedding ollama üstünde olabilir
        actions.append("embedding:restart_attempt")

    # 5. Token guard
    try:
        sys.path.insert(0, '/opt/jeff-brain')
        from brain.accounting import TokenGuard
        tg = TokenGuard()
        status = tg.check().get('status', 'ok')
        if status == 'stop':
            actions.append("token:STOP")
        elif status == 'flash':
            actions.append("token:FLASH")
    except:
        pass

    entry = {
        "timestamp": now.isoformat(),
        "actions": actions,
        "action_count": len(actions),
    }
    _log(entry)

    if actions:
        print(f"[{now.strftime('%H:%M UTC')}] HEALTH: {' | '.join(actions)}")
    else:
        print(f"[{now.strftime('%H:%M UTC')}] HEALTH: her sey yolunda")


if __name__ == "__main__":
    heal()
