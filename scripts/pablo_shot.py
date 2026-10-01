#!/usr/bin/env python3
"""Pablo'dan ekran goruntusu al ve kaydet. Cikti: kaydedilen dosya yolu."""
import base64, json, pathlib, subprocess, sys, time, urllib.request, urllib.error

BRIDGE = "http://100.80.122.74:7700"
ENV = "/etc/jeff-bridge.env"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/hermes/raporlar/pablo-ekran.png"


def bridge_key():
    out = subprocess.run(["sudo", "grep", "-E", "^BRIDGE_KEY=", ENV],
                         capture_output=True, text=True).stdout
    return out.split("=", 1)[1].strip().strip('"').strip("'")


H = {"X-Bridge-Key": bridge_key(), "Content-Type": "application/json"}


def post(path, body):
    req = urllib.request.Request(BRIDGE + path, data=json.dumps(body).encode(), headers=H)
    return json.loads(urllib.request.urlopen(req, timeout=60).read())


r = post("/pablo/task", {"type": "screenshot", "payload": {}, "policy": {}})
tid = r.get("task_id")
if not tid:
    print("GONDERILEMEDI:", json.dumps(r)[:300])
    sys.exit(1)

for i in range(40):
    time.sleep(2)
    row = subprocess.run(
        ["sudo", "sqlite3", "/home/hermes/jeff2/bridge/bridge.db",
         f"SELECT payload FROM alfred_results WHERE task_id='{tid}';"],
        capture_output=True, text=True).stdout.strip()
    if not row:
        continue
    l1 = json.loads(row)
    l2 = l1.get("result")
    if isinstance(l2, str):
        l2 = json.loads(l2)
    l3 = l2.get("result")
    if isinstance(l3, str):
        try:
            l3 = json.loads(l3)
        except Exception:
            pass
    if isinstance(l3, dict) and l3.get("screenshot_b64"):
        data = base64.b64decode(l3["screenshot_b64"])
        p = pathlib.Path(OUT)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        png_ok = data[:4] == b"\x89PNG"
        print(f"kaydedildi: {p}")
        print(f"olcu: {l3.get('width')}x{l3.get('height')} | {len(data)} bayt | PNG: {png_ok}")
        break
    print(f"  {2*(i+1)}s bekleniyor...")
else:
    print("zaman asimi")
