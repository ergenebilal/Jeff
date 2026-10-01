#!/usr/bin/env python3
"""Telegram sesli mesajini Gemini (Antigravity proxy) ile yaziya cevir."""
import base64, json, pathlib, sys, urllib.request, urllib.error

PROXY = "http://127.0.0.1:8999/v1/chat/completions"
AUDIO = sys.argv[1] if len(sys.argv) > 1 else "/home/hermes/.hermes/cache/audio/audio_bcfca0c18016.ogg"
MODEL = "gemini-3.8-flash-high"

raw = pathlib.Path(AUDIO).read_bytes()
b64 = base64.b64encode(raw).decode()
print(f"ses dosyasi: {len(raw)} bayt -> base64 {len(b64)} kr")

# uzantiya gore mime
mime = {"ogg": "audio/ogg", "oga": "audio/ogg", "mp3": "audio/mp3",
        "m4a": "audio/mp4", "wav": "audio/wav", "opus": "audio/ogg"}.get(
    AUDIO.rsplit(".", 1)[-1].lower(), "audio/ogg")
print(f"mime: {mime}")

body = {
    "model": MODEL,
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": (
                "Bu ses kaydini kelimesi kelimesine Turkce yaziya cevir. "
                "Sadece konusulan metni yaz; aciklama, ozet, baslik veya yorum EKLEME. "
                "Konusma anlasilmiyorsa '[anlasilamadi]' yaz.")},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
        ],
    }],
    "max_tokens": 2000,
}

req = urllib.request.Request(PROXY, data=json.dumps(body).encode(),
                             headers={"Content-Type": "application/json"})
try:
    res = json.loads(urllib.request.urlopen(req, timeout=180).read())
    txt = res["choices"][0]["message"]["content"]
    print("\n=== SESLI MESAJIN METNI ===\n")
    print(txt.strip())
except urllib.error.HTTPError as e:
    print(f"\n!! HTTP {e.code}: {e.read().decode()[:400]}")
except Exception as e:
    print(f"\n!! {type(e).__name__}: {str(e)[:300]}")
