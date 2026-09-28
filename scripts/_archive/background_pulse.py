#!/usr/bin/env python3.11
"""Every 3 hours: check time, services, and state. Silent unless something's wrong."""
import subprocess, os, json
from pathlib import Path
from datetime import datetime

STATUS_FILE = Path.home() / ".hermes" / "background_status.json"
STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)

now = datetime.now().astimezone()
issues = []

# 1. Record time accurately
time_data = {
    "iso": now.isoformat(),
    "hour": now.hour,
    "minute": now.minute,
    "tz": "Europe/Istanbul (+03)"
}

# 2. Check critical services
# ollama runs via process (not systemd), others via systemd
PROCESS_SERVICES = {
    "ollama": ["/bin/ollama", "serve"],
}
SYSTEMD_SERVICES = {
    "hermes-embedding-daemon": "hermes-embedding-daemon",
}

for name, proc in PROCESS_SERVICES.items():
    try:
        r = subprocess.run(
            ["pgrep", "-f", " ".join(proc)],
            capture_output=True, timeout=5
        )
        if r.returncode != 0:
            issues.append(f"{name} → process not running")
    except Exception as e:
        issues.append(f"{name} → kontrol basarisiz: {e}")

for name, svc in SYSTEMD_SERVICES.items():
    r = subprocess.run(["systemctl", "is-active", svc], capture_output=True, timeout=5)
    status = r.stdout.decode().strip()
    if status not in ("active", "activating"):
        issues.append(f"{name} → {status}")

# 3. Check disk
try:
    r = subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
    lines = r.stdout.strip().split("\n")
    if len(lines) >= 2:
        parts = lines[1].split()
        used_pct = parts[4].rstrip("%") if len(parts) >= 5 else "?"
        if used_pct.isdigit() and int(used_pct) > 85:
            issues.append(f"Disk doluyor: {used_pct}%")
except Exception:
    pass

# 4. Write status
state = {
    "time": time_data,
    "last_check": now.isoformat(),
    "issues": issues,
    "healthy": len(issues) == 0,
}
STATUS_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))

# Only output if there's an issue (empty stdout = silent delivery)
if issues:
    print(f"[{now.strftime('%H:%M')}] Sorun tespit edildi:")
    for i in issues:
        print(f"  ⚠️ {i}")
else:
    # Silent — no output means no delivery to Bilal
    pass
