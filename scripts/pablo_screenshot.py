#!/usr/bin/env python3
"""Pablo'ya kopru uzerinden ekran goruntusu gorevi gonder ve sonucu al."""
import json, pathlib, re, sys, time, urllib.request, urllib.error

BASE = "http://100.80.122.74:7700"
ENV = "/etc/jeff-bridge.env"


def bridge_key():
    out = __import__("subprocess").run(
        ["sudo", "grep", "-E", "^BRIDGE_KEY=", ENV],
        capture_output=True, text=True).stdout
    return out.split("=", 1)[1].strip().strip('"').strip("'")


KEY = bridge_key()
H = {"X-Bridge-Key": KEY, "Content-Type": "application/json"}
TASK_TYPE = sys.argv[1] if len(sys.argv) > 1 else "screenshot"


def post(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(), headers=H)
    try:
        return json.loads(urllib.request.urlopen(req, timeout=60).read())
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "_body": e.read().decode()[:300]}


def get(path):
    req = urllib.request.Request(BASE + path, headers=H)
    try:
        return json.loads(urllib.request.urlopen(req, timeout=60).read())
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "_body": e.read().decode()[:300]}


r = post("/pablo/task", {"type": TASK_TYPE, "payload": {}, "policy": {}})
print("gonderildi:", json.dumps(r)[:250])
tid = r.get("task_id")
if not tid:
    sys.exit(1)

print(f"\nbekleniyor (task {tid[:8]})...")
for i in range(30):
    time.sleep(2)
    res = get(f"/pablo/task/{tid}")
    if res.get("status") and res.get("status") not in ("queued", "pending", "running"):
        print(f"\n=== SONUC ({2*(i+1)} sn) ===")
        print(json.dumps(res, ensure_ascii=False)[:3000])
        break
    print(f"  {2*(i+1)}s: {res.get('status','?')}")
else:
    print("\nzaman asimi")
