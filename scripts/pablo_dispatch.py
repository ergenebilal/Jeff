#!/usr/bin/env python3
"""Pablo'ya (Windows PC) zararsiz bir 'shell' gorevi gonderir, sonucu bekler, GERCEK ciktiyi yazdirir.

SADECE tani/durum amacli kullan: dosya/pencere/surec kontrolu, echo, dir/ls, tarih,
ekran durumu gibi salt-okunur komutlar. Gonderim/yazma/degisiklik iceren hicbir seye
bunu KULLANMA (WhatsApp, e-posta, dosya silme/yazma, paylasim, vb.) - bunlar ayri,
onay gerektiren bir yoldan gitmeli. Bu betik approval kapisini atlar (5.2/5.3 boslugu,
bkz. knowledge/concepts/approval-gate-composability-gap.md), bu yuzden yalniz okuma
amacli komutlarla sinirli tutulmalidir.

Kullanim: python3 pablo_dispatch.py "KOMUT"
Ornek:    python3 pablo_dispatch.py "dir C:\\CyberGene"
"""
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE = "http://100.80.122.74:7700"



# P109: current node evidence is required before creating any new work.
def _p109_admission(action):
    __import__('sys').path.insert(0, '/home/hermes/.local/lib/jeff-pablo-guard')
    from pablo_readiness_gate import admission
    return admission(action)

def bridge_key():
    r = subprocess.run(
        ["sudo", "grep", "-E", "^BRIDGE_KEY=", "/etc/jeff-bridge.env"],
        capture_output=True, text=True)
    return r.stdout.strip().split("=", 1)[-1].strip().strip('"')


def call(path, key, data=None, method=None):
    req = urllib.request.Request(
        BASE + path,
        data=json.dumps(data).encode() if data is not None else None,
        headers={"X-Bridge-Key": key, "Content-Type": "application/json"},
        method=method or ("POST" if data is not None else "GET"))
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"_http": e.code, "_body": e.read().decode()[:300]}


def main():
    readiness = _p109_admission('shell')
    if readiness['admitted'] is not True:
        print(json.dumps(readiness, ensure_ascii=False)); return 3
    if len(sys.argv) < 2:
        print("Kullanim: python3 pablo_dispatch.py \"KOMUT\"", file=sys.stderr)
        return 2
    cmd = sys.argv[1]
    key = bridge_key()
    if not key:
        print("BRIDGE_KEY okunamadi", file=sys.stderr)
        return 1

    r = call("/alfred/task", key, {"type": "shell", "payload": {"cmd": cmd}, "policy": {}})
    if "_http" in r:
        print(f"Gorev gonderilemedi: HTTP {r['_http']} {r['_body']}")
        return 1
    task_id = r["task_id"]

    for _ in range(15):
        time.sleep(3)
        status = call(f"/alfred/task/{task_id}", key)
        st = status.get("status") if isinstance(status, dict) else None
        if st in ("unverified", "legacy_unverified"):
            break
    else:
        print("45 sn icinde sonuc gelmedi.")
        return 1

    result = call(f"/alfred/task/{task_id}/result", key)
    if "_http" in result:
        print(f"Sonuc okunamadi: HTTP {result['_http']} {result['_body']}")
        return 1
    payload = json.loads(result["result"]) if isinstance(result.get("result"), str) else result.get("result")
    inner = (payload or {}).get("result") or {}
    print(f"worker_status: {payload.get('status') if payload else result.get('worker_status')}")
    if inner:
        print(f"stdout: {inner.get('stdout', '')}")
        print(f"stderr: {inner.get('stderr', '')}")
        print(f"exit_code: {inner.get('exit_code')}")
    elif payload and payload.get("error"):
        print(f"error: {payload['error']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
