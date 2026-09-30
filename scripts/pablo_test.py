#!/usr/bin/env python3
"""Kopru uzerinden Pablo'ya zararsiz test gorevi gonder ve sonucu bekle."""
import json, os, time, uuid, urllib.request, urllib.error, subprocess

BASE = "http://100.80.122.74:7700"

# anahtari ortam dosyasindan al (ekrana yazdirilmaz)
key = subprocess.run(
    ["sudo", "grep", "-E", "^BRIDGE_KEY=", "/etc/jeff-bridge.env"],
    capture_output=True, text=True).stdout.strip().split("=", 1)[-1].strip().strip('"')
print(f"anahtar: {'VAR' if key else 'YOK'} ({len(key)} kr)")

def call(path, data=None, method=None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(data).encode() if data is not None else None,
        headers={"X-Bridge-Key": key, "Content-Type": "application/json"},
        method=method or ("POST" if data is not None else "GET"))
    try:
        return json.loads(urllib.request.urlopen(req, timeout=25).read())
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "_body": e.read().decode()[:250]}

print("\n=== once durum ===")
print(" ", call("/health"))

tid = str(uuid.uuid4())
print(f"\n=== test gorevi gonderiliyor (id {tid[:8]}) ===")
r = call("/alfred/task", {
    "task_id": tid,
    "type": "shell",
    "payload": {"cmd": "echo PABLO_CANLI_TEST"},
    "policy": {},
})
print(" ", r)

print("\n=== sonuc bekleniyor (en fazla 45 sn) ===")
for i in range(15):
    time.sleep(3)
    ev = call(f"/alfred/task/{tid}")
    if isinstance(ev, dict):
        st = ev.get("status") or ev.get("_http")
        print(f"  {3*(i+1):>3} sn  durum: {st}")
        if st in ("done", "completed", "verified", "failed", "error", "unverified"):
            print("\n  TAM KAYIT:", json.dumps(ev, ensure_ascii=False)[:700])
            break
    else:
        print(f"  {3*(i+1):>3} sn  {ev}")
else:
    print("\n  >> 45 sn icinde sonuc gelmedi.")
    print("  son kayit:", json.dumps(ev, ensure_ascii=False)[:500])
