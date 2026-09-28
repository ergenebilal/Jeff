"""
Jeff & Friend Hermes Chat MCP Server (FastMCP)
İki Hermes arasında sohbet için MCP sunucusu.
Port: 8769
"""

import json
import time
import os
import sys
from mcp.server.fastmcp import FastMCP

CHAT_FILE = "/home/hermes/.hermes/jeff_chat.json"

def load_chat():
    if os.path.exists(CHAT_FILE):
        with open(CHAT_FILE) as f:
            return json.load(f)
    return {"messages": [], "next_id": 1}

def save_chat(data):
    with open(CHAT_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

mcp = FastMCP("jeff-chat", instructions="Jeff ve arkadaşının Hermes'i arasında sohbet MCP'si")

@mcp.tool()
def hermes_send(mesaj: str) -> str:
    """Jeff'e mesaj gönder. Cevapları hermes_check ile kontrol et."""
    chat = load_chat()
    chat["messages"].append({
        "id": chat["next_id"],
        "kim": "diger_hermes",
        "mesaj": mesaj,
        "zaman": time.strftime("%H:%M:%S")
    })
    chat["next_id"] += 1
    save_chat(chat)
    return f"✅ Mesajın Jeff'e iletildi! Cevapları kontrol et: hermes_check(last_id={chat['next_id']-1})"

@mcp.tool()
def hermes_check(last_id: int = 0) -> str:
    """Jeff'in yeni mesajlarını kontrol et. last_id=0 tüm son 10'u gösterir."""
    chat = load_chat()
    yeni = [m for m in chat["messages"] if m["id"] > last_id and m["kim"] == "jeff"]
    if not yeni:
        return "📭 Jeff'ten yeni mesaj yok."
    
    satirlar = []
    for m in yeni[-10:]:
        satirlar.append(f"[{m['zaman']}] 🤖 Jeff: {m['mesaj']}")
    satirlar.append(f"\n--- Son ID: {yeni[-1]['id']} ---")
    return "\n".join(satirlar)

@mcp.tool()
def hermes_respond(kime: str = "diger_hermes", mesaj: str = "") -> str:
    """[SADECE JEFF] Jeff'in cevabını yazar."""
    if not mesaj:
        return "❌ Mesaj boş olamaz!"
    chat = load_chat()
    chat["messages"].append({
        "id": chat["next_id"],
        "kim": "jeff",
        "mesaj": mesaj,
        "zaman": time.strftime("%H:%M:%S"),
        "kime": kime
    })
    chat["next_id"] += 1
    save_chat(chat)
    return f"✅ Cevap yazıldı. ID: {chat['next_id']-1}"

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8769
    mcp.settings.host = "0.0.0.0"
    mcp.settings.port = port
    print(f"🤖 Jeff Chat MCP Server (Streamable HTTP) başlıyor...")
    print(f"📡 Port {port}, endpoint: http://0.0.0.0:{port}/")
    print(f"🔗 Bağlantı: http://193.164.4.149:{port}/")
    
    mcp.run(transport="streamable-http")
