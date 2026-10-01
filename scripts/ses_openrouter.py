#!/usr/bin/env python3
"""OpenRouter uzerinden ses cevirme denemesi (ses destekli modeller)."""
import base64, json, pathlib, urllib.request, urllib.error

AUDIO = "/home/hermes/.hermes/cache/audio/audio_bcfca0c18016.ogg"
KEYFILE = "/home/hermes/.hermes/.env"
raw = pathlib.Path(AUDIO).read_bytes()
b64 = base64.b64encode(raw).decode()

key = ""
for line in pathlib.Path(KEYFILE).read_text(errors="ignore").splitlines():
    if line.startswith("OPENROUTER_API_KEY="):
        key = line.split("=", 1)[1].strip().strip('"').strip("'")
print(f"  OpenRouter anahtari: {len(key)} karakter")

PROMPT = ("Bu ses kaydini kelimesi kelimesine Turkce yaziya cevir. "
          "Sadece konusulan metni yaz; aciklama ekleme.")

MODELS = [
    "google/gemini-2.0-flash-001",
    "google/gemini-flash-1.5",
    "google/gemini-2.5-flash",
    "openai/gpt-4o-audio-preview",
]


def call(model):
    body = {"model": model, "max_tokens": 700,
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": PROMPT},
                {"type": "input_audio", "input_audio": {"data": b64, "format": "ogg"}},
            ]}]}
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=150).read())
        return "OK|" + r["choices"][0]["message"]["content"].strip()[:300]
    except urllib.error.HTTPError as e:
        return f"HTTP {e.code}|" + e.read().decode()[:160]
    except Exception as e:
        return f"{type(e).__name__}|" + str(e)[:130]


for m in MODELS:
    out = call(m)
    tag, _, msg = out.partition("|")
    print(f"\n--- {m}\n    [{tag}] {msg.replace(chr(10),' ')[:240]}")
