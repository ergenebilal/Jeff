#!/usr/bin/env python3
"""Chat Mesaj Watchdog — yeni site mesajlarını tespit edip Telegram'a bildirir"""
import json, os, sys

LOG_FILE = os.path.expanduser("~/.hermes/chat_messages.jsonl")
STATE_FILE = os.path.expanduser("~/.hermes/chat_last_notified_id.txt")
HERMES_MSG = os.path.expanduser("~/.hermes/cron/chat_output.txt")

def get_last_notified():
    try:
        with open(STATE_FILE) as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0

def set_last_notified(msg_id):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        f.write(str(msg_id))

def get_messages():
    if not os.path.exists(LOG_FILE):
        return []
    msgs = []
    with open(LOG_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    msgs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return msgs

def main():
    last_id = get_last_notified()
    msgs = get_messages()
    
    # Son bildirilmemiş mesajları bul
    new_msgs = [m for m in msgs if m["id"] > last_id]
    
    if not new_msgs:
        # Yeni mesaj yok — sessiz çık
        return
    
    # En yeni mesajı bildir
    latest = new_msgs[-1]
    ts = latest["timestamp"][:19].replace("T", " ")
    msg = latest["message"]
    ip = latest.get("ip", "bilinmiyor")
    
    # Kısa özet
    preview = msg[:200] + ("..." if len(msg) > 200 else "")
    
    output = (
        f"💬 *ergeneai.com'dan yeni mesaj!*\n\n"
        f"_{ts}_\n"
        f"🌐 IP: `{ip}`\n\n"
        f"{preview}\n\n"
        f"#site-mesajı"
    )
    
    # Cron output dosyasına yaz
    os.makedirs(os.path.dirname(HERMES_MSG), exist_ok=True)
    with open(HERMES_MSG, "w") as f:
        f.write(output)
    
    # State güncelle
    set_last_notified(latest["id"])
    
    print(output)

if __name__ == "__main__":
    main()
