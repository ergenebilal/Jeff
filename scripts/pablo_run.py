#!/usr/bin/env python3
"""Pablo'ya kopru uzerinden komut gonder, ham sonucu (stdout) dondur.

Kullanim:
  python3 pablo_run.py 'echo merhaba'
  python3 pablo_run.py --type shell 'powershell -Command "Get-Date"'
"""
import json, sys, time, urllib.request, urllib.error, subprocess

BASE = "http://100.80.122.74:7700"
ENV = "/etc/jeff-bridge.env"


def bridge_key():
    out = subprocess.run(["sudo", "grep", "-E", "^BRIDGE_KEY=", ENV],
                         capture_output=True, text=True).stdout
    return out.split("=", 1)[1].strip().strip('"').strip("'")


KEY = bridge_key()
H = {"X-Bridge-Key": KEY, "Content-Type": "application/json"}

argv = sys.argv[1:]
tt = "shell"
if argv and argv[0] == "--type":
    tt = argv[1]
    argv = argv[2:]
CMD = " ".join(argv)


def post(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode(), headers=H)
    try:
        return json.loads(urllib.request.urlopen(req, timeout=60).read())
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "_body": e.read().decode()[:400]}


def get(path):
    req = urllib.request.Request(BASE + path, headers=H)
    try:
        return json.loads(urllib.request.urlopen(req, timeout=60).read())
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "_body": e.read().decode()[:400]}


payload = {"cmd": CMD} if tt == "shell" else {}
r = post("/pablo/task", {"type": tt, "payload": payload, "policy": {}})
tid = r.get("task_id")
if not tid:
    print("GONDERILEMEDI:", json.dumps(r)[:400])
    sys.exit(1)
print(f"gorev: {tid[:8]} ({tt})")

# sonucu veritabanindan oku (uç 'unverified' dondurur, ham sonuc DB'de)
for i in range(40):
    time.sleep(2)
    row = subprocess.run(
        ["sudo", "sqlite3", "/home/hermes/jeff2/bridge/bridge.db",
         f"SELECT payload FROM alfred_results WHERE task_id='{tid}';"],
        capture_output=True, text=True).stdout.strip()
    if not row:
        continue
    try:
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
    except Exception as e:
        print("cozumleme hatasi:", e)
        print(row[:600])
        break

    print(f"\nsure: {2*(i+1)} sn")
    if isinstance(lvl3, dict):
        for k in ("status", "ok", "stdout", "stderr", "exit_code", "error"):
            if k in lvl3 or k in lvl2:
                v = lvl3.get(k, lvl2.get(k))
                if v not in (None, ""):
                    print(f"  {k}: {str(v)[:1500]}")
        extra = {k: v for k, v in lvl3.items()
                 if k not in ("status", "ok", "stdout", "stderr", "exit_code", "error",
                              "screenshot_b64", "screenshot_path", "save_path")}
        if extra:
            print("  ek:", json.dumps(extra, ensure_ascii=False)[:400])
    else:
        print("  ham:", str(lvl3)[:600])
    break
else:
    print("zaman asimi — sonuc gelmedi")
