#!/usr/bin/env python3
"""Gateway uzerinden ses gecirme denemesi: birden fazla icerik bicimi."""
import base64, json, pathlib, urllib.request, urllib.error

AUDIO = "/home/hermes/.hermes/cache/audio/audio_bcfca0c18016.ogg"
URL = "http://127.0.0.1:8999/v1/chat/completions"
raw = pathlib.Path(AUDIO).read_bytes()
b64 = base64.b64encode(raw).decode()
PROMPT = "Bu ses kaydini kelimesi kelimesine Turkce yaziya cevir. Sadece konusulan metni yaz."

shapes = {
    "input_audio": [{"type": "text", "text": PROMPT},
                    {"type": "input_audio", "input_audio": {"data": b64, "format": "ogg"}}],
    "image_url":   [{"type": "text", "text": PROMPT},
                    {"type": "image_url", "image_url": {"url": f"data:audio/ogg;base64,{b64}"}}],
    "audio_url":   [{"type": "text", "text": PROMPT},
                    {"type": "audio_url", "audio_url": {"url": f"data:audio/ogg;base64,{b64}"}}],
}


def call(model, content):
    body = {"model": model, "messages": [{"role": "user", "content": content}], "max_tokens": 800}
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=120).read())
        return "OK: " + r["choices"][0]["message"]["content"].strip()[:300]
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}: {e.read().decode()[:150]}"
    except Exception as e:
        return f"{type(e).__name__}: {str(e)[:120]}"


for model in ("gemini-3.8-flash-high", "gemini-3.5-flash"):
    for name, content in shapes.items():
        out = call(model, content)
        verdict = "GECTI" if out.startswith("OK") else "gecti-degil"
        print(f"\n--- {model} / {name}: {verdict}")
        print("    " + out.replace("\n", " ")[:260])
