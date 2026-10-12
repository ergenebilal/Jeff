#!/usr/bin/env python3
"""Pablo'ya (Windows) akis indirme gorevi gonder.

Jeton KOMUT SATIRINA ve CIKTIYA yazilmaz: yalnizca bu script icinde dosyadan
okunur, gorev govdesine gomulur. Indirme uzun surdugu icin 'start /b' ile
arka planda baslatilir; gorev hemen doner, sonuc ayrica sorgulanir.

Kullanim:
    python3 pablo_stream_pull.py            # indirmeyi baslat
    python3 pablo_stream_pull.py --check    # bilgisayardaki dosyayi sorgula
"""
import sys
import pathlib
import time

sys.path.insert(0, "/home/hermes/.hermes/skills/system/pablo-execution/scripts")
from pablo_task import post_task, read_result  # type: ignore

TOKF = pathlib.Path("/home/hermes/.hermes/cache/scratch/.stream-token")
URL = "http://100.80.122.74:7711/stream"
DEST = r"%USERPROFILE%\Downloads\jeff-backup-P128.tar.gz"


def send(cmd, timeout=90):
    tid = post_task("shell", {"cmd": cmd})
    print("gorev kimligi:", tid[:8], "| Pablo ~3 sn'de alir")
    t0 = time.time()
    outer, inner = read_result(tid, timeout=timeout)
    if inner is None:
        print("SONUC YOK: Pablo almadi ya da zaman asimi")
        return None, None
    print("sure: %d sn | durum: %s" % (int(time.time() - t0), (outer or {}).get("status")))
    return outer, inner


def main():
    if "--check" in sys.argv:
        cmd = ('if exist "%s" (dir "%s") else (echo DOSYA YOK)' % (DEST, DEST))
        outer, inner = send(cmd, timeout=60)
        if inner:
            print("stdout:", ((inner.get("stdout") or "").strip())[:600])
        return

    token = TOKF.read_text(encoding="utf-8").strip()
    if not token:
        sys.exit("jeton dosyasi bos")
    # start /b = arka planda baslat, gorev hemen doner (aktarim ~10 dk surer)
    cmd = ('start "" /b curl -s -H "X-Token: %s" %s -o "%s"' % (token, URL, DEST))
    outer, inner = send(cmd, timeout=90)
    if inner is not None:
        print("baslatma cikti kodu:", inner.get("exit_code"))
        print("stdout:", ((inner.get("stdout") or "").strip())[:200])
        print("NOT: indirme arka planda suruyor; ~10 dk sonra --check ile sorgula")


if __name__ == "__main__":
    main()
