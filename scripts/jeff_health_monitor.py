#!/usr/bin/env python3
"""
Jeff 4.0 Health Monitor — Critic process watch, auto-restart (max 2), alert.
Run by cron every 5 minutes or via jeff4_start.sh health.
Reads /opt/hermes/jeff_v2/config/log_policy.json for config.
"""
import json, os, subprocess, time, sys
from datetime import datetime, timezone
from pathlib import Path

JEFF_DIR = Path("/opt/hermes/jeff_v2")
PID_DIR = JEFF_DIR / "pids"
STATE_FILE = JEFF_DIR / "config" / "health_state.json"
LOG_FILE = Path("/var/log/jeff/health_monitor.log")

CRITICAL_SERVICES = [
    "director-sistem", "director-finans", "director-bilgi",
    "director-kreatif", "director-gelisim", "worker-shared", "worker-kreatif"
]
MAX_RESTARTS = 2
START_SCRIPT = JEFF_DIR / "jeff4_start.sh"

def log(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")
    print(line)

def load_state():
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"restart_counts": {}, "last_alert_sent": None}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))

def check_redis():
    try:
        r = subprocess.run(["redis-cli", "ping"], capture_output=True, timeout=3)
        return r.returncode == 0 and b"PONG" in r.stdout
    except:
        return False

def check_disk():
    s = os.statvfs("/")
    free_gb = (s.f_bavail * s.f_frsize) / (1024**3)
    total_gb = (s.f_blocks * s.f_frsize) / (1024**3)
    pct = (1 - s.f_bavail / s.f_blocks) * 100
    return {"free_gb": round(free_gb, 1), "total_gb": round(total_gb, 1), "pct": round(pct, 1)}

def check_ram():
    try:
        r = subprocess.run(["free", "-b"], capture_output=True, text=True, timeout=3)
        lines = r.stdout.strip().split("\n")
        mem = lines[1].split()
        total = int(mem[1])
        avail = int(mem[6])
        return {"total_gb": round(total/(1024**3), 1), "avail_gb": round(avail/(1024**3), 1)}
    except:
        return {"total_gb": 0, "avail_gb": 0}

def is_running(service):
    pidf = PID_DIR / f"{service}.pid"
    if not pidf.exists():
        return False
    try:
        pid = int(pidf.read_text().strip())
        os.kill(pid, 0)
        return True
    except:
        return False

def restart_service(service, state):
    state["restart_counts"][service] = state["restart_counts"].get(service, 0) + 1
    save_state(state)
    log(f"RESTART [{state['restart_counts'][service]}/{MAX_RESTARTS}] {service}")

    # Tekil servisi başlat
    label = service
    script_map = {
        "worker-shared": "worker_pool.py shared",
        "worker-kreatif": "worker_pool.py kreatif",
        "director-sistem": "director_agent.py sistem",
        "director-finans": "director_agent.py finans",
        "director-bilgi": "director_agent.py bilgi",
        "director-kreatif": "director_agent.py kreatif",
        "director-gelisim": "director_agent.py gelisim",
    }
    script_args = script_map.get(service, "")
    if not script_args:
        log(f"ERROR: Unknown service {service}")
        return False

    script, args = script_args.split(" ", 1)
    logf = Path(f"/var/log/jeff/{label}.log")
    logf.parent.mkdir(parents=True, exist_ok=True)

    try:
        proc = subprocess.Popen(
            ["/usr/bin/python3.12", str(JEFF_DIR / script), args],
            stdout=open(logf, "a"), stderr=subprocess.STDOUT,
            start_new_session=True
        )
        time.sleep(1)
        if proc.poll() is None:
            (PID_DIR / f"{label}.pid").write_text(str(proc.pid))
            log(f"OK {label} restarted (PID {proc.pid})")
            return True
        else:
            log(f"FAIL {label} died immediately (exit {proc.returncode})")
            return False
    except Exception as e:
        log(f"ERROR restarting {label}: {e}")
        return False

def send_alert(service, msg):
    """HQ'ya ve log'a kritik alarm yaz."""
    alert = f"[CRITICAL] {service}: {msg}"
    log(alert)
    try:
        hq_url = "http://localhost:8889/api/alert"
        subprocess.run(["curl", "-s", "-X", "POST", hq_url,
                       "-H", "Content-Type: application/json",
                       "-d", json.dumps({"service": service, "message": msg, "level": "critical"})],
                      timeout=5)
    except:
        pass

def main():
    state = load_state()
    log("=== Health Monitor Check ===")

    # 1. Process check
    dead_count = 0
    for svc in CRITICAL_SERVICES:
        if not is_running(svc):
            cnt = state["restart_counts"].get(svc, 0)
            if cnt < MAX_RESTARTS:
                ok = restart_service(svc, state)
                if not ok and cnt + 1 >= MAX_RESTARTS:
                    send_alert(svc, f"{MAX_RESTARTS} restart denemesi başarısız. Manuel müdahale gerek.")
                    dead_count += 1
            else:
                dead_count += 1
                log(f"SKIP {svc} — restart limiti ({MAX_RESTARTS}) aşıldı")

    # 2. System resources
    disk = check_disk()
    ram = check_ram()
    redis_ok = check_redis()

    if disk["pct"] > 85:
        send_alert("system", f"Disk %{disk['pct']} — {disk['free_gb']}GB kaldı")
    if ram["avail_gb"] < 2:
        send_alert("system", f"RAM kritik — {ram['avail_gb']}GB kaldı")
    if not redis_ok:
        log("WARN Redis ulaşılamıyor")

    # 3. Task success rate (son 24 saat)
    task_log = JEFF_DIR / "memories" / "task_log.jsonl"
    if task_log.exists():
        lines = task_log.read_text().strip().split("\n")[-50:]
        completed = sum(1 for l in lines if '"status":"completed"' in l)
        failed = sum(1 for l in lines if '"status":"failed"' in l)
        total = completed + failed
        if total > 0 and (completed / total) < 0.5:
            log(f"WARN Task success rate düşük: {completed}/{total} (%{int(completed/total*100)})")

    # 4. Summary
    log(f"DONE — dead:{dead_count} disk:%{disk['pct']} ram:{ram['avail_gb']}GB redis:{'ok' if redis_ok else 'fail'}")

    # 5. Reset restart counts for running services
    for svc in CRITICAL_SERVICES:
        if is_running(svc) and state["restart_counts"].get(svc, 0) > 0:
            state["restart_counts"][svc] = 0
    save_state(state)

if __name__ == "__main__":
    main()
