#!/usr/bin/env python3
"""PowerShell betigini base64 (UTF-16LE) ile Pablo'ya gonder.

Kullanim:
  python3 pablo_ps.py 'Get-Date'
  python3 pablo_ps.py --file betik.ps1
"""
import base64, json, subprocess, sys, pathlib, time

BRIDGE = "http://100.80.122.74:7700"
ENV = "/etc/jeff-bridge.env"


def bridge_key():
    out = subprocess.run(["sudo", "grep", "-E", "^BRIDGE_KEY=", ENV],
                         capture_output=True, text=True).stdout
    return out.split("=", 1)[1].strip().strip('"').strip("'")


KEY = bridge_key()
H = {"X-Bridge-Key": KEY, "Content-Type": "application/json"}

argv = sys.argv[1:]
if argv and argv[0] == "--file":
    PS = pathlib.Path(argv[1]).read_text()
else:
    PS = " ".join(argv)

# PowerShell -EncodedCommand UTF-16LE base64 bekler
enc = base64.b64encode(PS.encode("utf-16-le")).decode()
CMD = f'powershell -NoProfile -EncodedCommand {enc}'

import urllib.request, urllib.error


def post(path, body):
    req = urllib.request.Request(BRIDGE + path, data=json.dumps(body).encode(), headers=H)
    try:
        return json.loads(urllib.request.urlopen(req, timeout=60).read())
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "_body": e.read().decode()[:400]}


r = post("/pablo/task", {"type": "shell", "payload": {"cmd": CMD}, "policy": {}})
tid = r.get("task_id")
if not tid:
    print("GONDERILEMEDI:", json.dumps(r)[:400])
    sys.exit(1)
print(f"gorev: {tid[:8]}")

for i in range(40):
    time.sleep(2)
    row = subprocess.run(
        ["sudo", "sqlite3", "/home/hermes/jeff2/bridge/bridge.db",
         f"SELECT payload FROM alfred_results WHERE task_id='{tid}';"],
        capture_output=True, text=True).stdout.strip()
    if not row:
        continue
    lvl1 = json.loads(row)
    lvl2 = lvl1.get("result")
    if isinstance(lvl2, str):
        lvl2 = json.loads(lvl2)
    lvl3 = lvl2.get("result")
    if isinstance(lvl3, str):
        try:
            lvl3 = json.loads(lvl3)
        except Exception:
            pass
    print(f"\nsure: {2*(i+1)} sn")
    if isinstance(lvl3, dict):
        for k in ("status", "ok", "stdout", "stderr", "exit_code", "error"):
            v = lvl3.get(k, lvl2.get(k))
            if v not in (None, ""):
                print(f"  {k}: {str(v)[:2000]}")
    else:
        print("  ham:", str(lvl3)[:800])
    break
else:
    print("zaman asimi")
