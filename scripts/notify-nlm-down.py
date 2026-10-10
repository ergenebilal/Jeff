#!/usr/bin/env python3
import os
import subprocess
import re
import sys

TOKEN = None
with open("/home/hermes/.hermes/gateway.env") as f:
    for line in f:
        m = re.match(r"TELEGRAM_BOT_TOKEN=(.+)", line.strip())
        if m:
            TOKEN = m.group(1).strip()
            break

if not TOKEN:
    print("NO TOKEN FOUND")
    sys.exit(1)

CHAT = os.environ.get("TELEGRAM_OWNER_CHAT_ID") or os.environ.get("TELEGRAM_CHAT_ID")
if not CHAT:
    print("OWNER CHAT NOT CONFIGURED")
    sys.exit(1)
MSG = "NotebookLM baglantisi koptu! Sunucuda nlm login yapilmasi gerekiyor."

import urllib.request
import urllib.parse

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
data = urllib.parse.urlencode({"chat_id": CHAT, "text": MSG}).encode()
try:
    with urllib.request.urlopen(url, data=data, timeout=20) as resp:
        body = resp.read().decode()
        print(body[:300])
except Exception as e:
    print(f"ERR: {e}")
    sys.exit(1)