#!/usr/bin/env python3
"""Telegram sesli mesaji -> Gemini native API (inline_data) ile Turkce metin."""
import base64, json, pathlib, os, re, sys, urllib.request, urllib.error

AUDIO = sys.argv[1] if len(sys.argv) > 1 else "/home/hermes/.hermes/cache/audio/audio_bcfca0c18016.ogg"


def get_key():
    for p in ("/home/hermes/.hermes/.env", "/opt/hermes/.env"):
        try:
            for line in pathlib.Path(p).read_text(errors="ignore").splitlines():
                m = re.match(r'^\s*(GEMINI_API_KEY|GOOGLE_API_KEY)\s*=\s*["\']?([^"\'\s]+)', line)
                if m and m.group(2) not in ("", "changeme"):
                    print(f"  anahtar kaynagi: {p} ({m.group(1)}, uzunluk {len(m.group(2))})")
                    return m.group(2)
        except Exception:
            pass
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


key = get_key()
if not key:
    print("!! Gemini anahtari bulunamadi")
    sys.exit(1)

raw = pathlib.Path(AUDIO).read_bytes()
b64 = base64.b64encode(raw).decode()
mime = {"ogg": "audio/ogg", "oga": "audio/ogg", "mp3": "audio/mp3",
        "m4a": "audio/mp4", "wav": "audio/wav"}.get(AUDIO.rsplit(".", 1)[-1].lower(), "audio/ogg")
print(f"  ses: {len(raw)} bayt | mime: {mime}")

prompt = ("Bu ses kaydini kelimesi kelimesine Turkce yaziya cevir. "
          "Sadece konusulan metni yaz; aciklama, ozet, baslik, yorum EKLEME. "
          "Anlasilmayan yer olursa [anlasilamadi] yaz.")

body = {"contents": [{"parts": [
    {"text": prompt},
    {"inline_data": {"mime_type": mime, "data": b64}},
]}]}

for model in ("gemini-flash-latest", "gemini-2.5-flash", "gemini-2.0-flash"):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        res = json.loads(urllib.request.urlopen(req, timeout=120).read())
        txt = res["candidates"][0]["content"]["parts"][0]["text"].strip()
        print(f"\n=== SESLI MESAJIN METNI ({model}) ===\n")
        print(txt)
        break
    except urllib.error.HTTPError as e:
        print(f"  {model} -> HTTP {e.code}: {e.read().decode()[:180]}")
    except Exception as e:
        print(f"  {model} -> {type(e).__name__}: {str(e)[:150]}")
