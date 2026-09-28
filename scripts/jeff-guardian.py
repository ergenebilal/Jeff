#!/usr/bin/env python3
"""Jeff Guardian — Gemini ile log analizi ve anomali tespit"""
import subprocess, json, os, sys
from datetime import datetime
from pathlib import Path

LOG_FILE = Path.home() / "logs" / "watchdog-jeff.log"
GUARDIAN_LOG = Path.home() / "logs" / "guardian-jeff.log"
GUARDIAN_LOG.parent.mkdir(exist_ok=True)

# Son 10 watchdog kaydını oku
son_loglar = ""
if LOG_FILE.exists():
    with open(LOG_FILE) as f:
        lines = f.readlines()
        son_loglar = "".join(lines[-10:])

# Sistem durumu
gateway = subprocess.run(["pgrep", "-f", "gateway run"], capture_output=True, text=True)
ram = subprocess.run(["free", "-m"], capture_output=True, text=True)
disk = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
uptime = subprocess.run(["uptime", "-p"], capture_output=True, text=True)

# Gemini'ye sor
api_key = ""
with open(Path.home() / ".hermes" / ".env") as f:
    for line in f:
        if line.startswith("GOOGLE_API_KEY="):
            api_key = line.split("=", 1)[1].strip()
            break

if not api_key:
    print("GOOGLE_API_KEY bulunamadi")
    sys.exit(1)

prompt = f"""Sen Jeff'in koruyucususun. Sunucu durumunu analiz et ve sorun varsa raporla.

Son watchdog kayıtları:
{son_loglar}

RAM:
{ram.stdout}

Disk:
{disk.stdout}

Uptime: {uptime.stdout}

Gateway PID: {gateway.stdout.strip() or 'DOWN'}

Eğer bir sorun varsa kisa bir uyari yaz. Sorun yoksa SESSIZ KAL.
"""

payload = json.dumps({
    "contents": [{"parts": [{"text": prompt}]}]
})

import urllib.request
req = urllib.request.Request(
    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}",
    data=payload.encode(),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
        text = result.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        if text.strip():
            with open(GUARDIAN_LOG, "a") as f:
                f.write(f"[{datetime.now().isoformat()}] {text}\n")
            print(text)
except Exception as e:
    print(f"Guardian error: {e}")
