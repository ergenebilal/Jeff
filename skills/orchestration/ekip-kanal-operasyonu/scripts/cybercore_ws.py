#!/usr/bin/env python3
"""Cyber Core odası (ws://100.89.26.86:4520/ws) WS istemcisi — sunucu tarafı Jeff.

Kullanım:
  python3 cybercore_ws.py listen [saniye]            -> odayı dinle (hiçbir şey göndermez)
  python3 cybercore_ws.py send "<metin>" [saniye]    -> chat mesajı gönder, sonra dinle

UYARI: WS `sender`/`id` alanlarını yok sayar; odaya yazılan her satır panelde 'Bilal' görünür.
Bu yüzden metnin başına [jeff·sunucu] etiketi koy. Doğrulama: GET /api/events, alan id/ts.
"""
import asyncio
import json
import sys

URL = "ws://100.89.26.86:4520/ws"


async def run(mode: str, text: str = "", seconds: int = 8):
    import websockets

    async with websockets.connect(URL, open_timeout=10) as ws:
        print(f"[connected] {URL}")
        if mode == "send":
            payload = {"type": "chat", "text": text}
            await ws.send(json.dumps(payload, ensure_ascii=False))
            print(f"[sent] {len(text)} karakter")
        end = asyncio.get_event_loop().time() + seconds
        while asyncio.get_event_loop().time() < end:
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=max(0.1, end - asyncio.get_event_loop().time()))
            except asyncio.TimeoutError:
                break
            try:
                ev = json.loads(raw)
            except Exception:
                print(f"[raw] {raw[:400]}")
                continue
            t = ev.get("type")
            if t == "message":
                s = ev.get("sender") or {}
                print(f"[msg] id={ev.get('id')} sender={s.get('id')}/{s.get('name')} ts={ev.get('ts')} "
                      f"text={str(ev.get('text'))[:120]!r}")
            else:
                print(f"[{t}] {str(ev)[:300]}")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "listen"
    if mode == "send" and len(sys.argv) > 2:
        text = sys.argv[2]
        secs = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    else:
        text = ""
        secs = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 8
    asyncio.run(run(mode, text, secs))
