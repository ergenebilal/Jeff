#!/usr/bin/env python3
"""Stdin'den okunan metni Telegram'a gonderir (.alert.env kimlik bilgileriyle).
Kullanim: echo "mesaj" | python3 send_alert.py
          cat dosya.txt | python3 send_alert.py
"""
import json
import sys
import urllib.request
from pathlib import Path

ENV_FILE = "/home/hermes/.alert.env"


def load_env(path):
    values = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            values[k.strip()] = v.strip().strip("\"'")
    return values


def main():
    text = sys.stdin.read()
    if not text.strip():
        print("bos mesaj, gonderilmedi", file=sys.stderr)
        return 1
    env = load_env(ENV_FILE)
    token, chat_id = env["ALERT_BOT_TOKEN"], env["ALERT_CHAT_ID"]
    body = json.dumps({"chat_id": chat_id, "text": text}).encode()
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=body, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as resp:
        print(f"STATUS: {resp.status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
