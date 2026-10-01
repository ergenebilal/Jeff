#!/usr/bin/env python3
"""Claude Code ajaninin canli oturum kaydini sunucuya cek, oku ve ozetle.

Kullanim:
  python3 ajan_oku.py          # son 25 tur
  python3 ajan_oku.py 60       # son 60 tur
"""
import base64, json, pathlib, subprocess, sys

PS = "/home/hermes/scripts/ps_claude_oturum.ps1"
RCV = "/tmp/winmd/oturum_son.b64"

def cek():
    r = subprocess.run(
        ["python3", "/home/hermes/scripts/pablo_ps.py", "--file", PS],
        capture_output=True, text=True, timeout=200, cwd="/home/hermes",
    )
    ok = "SUCCESS" in r.stdout
    if not ok:
        print("[!] aktarim basarisiz")
        print(r.stdout[-500:])
        return False
    return True

def oku(adet=25):
    p = pathlib.Path(RCV)
    if not p.exists():
        print("[!] kayit dosyasi yok")
        return
    try:
        ham = base64.b64decode(p.read_bytes()).decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[!] cozulemedi: {e}")
        return
    satirlar = ham.splitlines()
    kayitlar = []
    for s in satirlar:
        s = s.strip()
        if not s.startswith("{"):
            continue
        try:
            o = json.loads(s)
        except Exception:
            continue
        tip = o.get("type")
        msg = o.get("message") or {}
        if not isinstance(msg, dict):
            continue
        rol = msg.get("role")
        icerik = msg.get("content")
        if tip not in ("user", "assistant") and rol not in ("user", "assistant"):
            continue
        parca = []
        if isinstance(icerik, str):
            parca.append(icerik)
        elif isinstance(icerik, list):
            for c in icerik:
                if not isinstance(c, dict):
                    continue
                if c.get("type") == "text":
                    parca.append(c.get("text", ""))
                elif c.get("type") == "tool_use":
                    parca.append(f"[ARAC:{c.get('name')}]")
        metin = " ".join(" ".join(parca).split())
        if not metin:
            continue
        kayitlar.append((rol or tip, metin))
    print(f"### AJANIN SON {min(adet, len(kayitlar))} TURU (toplam {len(kayitlar)} kayit okundu)\n")
    for rol, metin in kayitlar[-adet:]:
        etiket = "SEN/BILAL" if rol == "user" else "AJAN"
        print(f"--- {etiket} ---")
        print(metin[:900])
        print()

if __name__ == "__main__":
    adet = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    if cek():
        oku(adet)
