#!/usr/bin/env python3
"""Google OAuth — Local server ile token al"""
import os, json, socketserver, threading, urllib.parse, webbrowser
from http import server

HOME = os.path.expanduser("~")
ENV_PATH = os.path.join(HOME, ".hermes", ".env")

# Google Cloud project credentials
CLIENT_ID = ""
CLIENT_SECRET = ""
SCOPES = [
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]

def get_val(key_name):
    with open(ENV_PATH, "rb") as f:
        for line in f:
            p = key_name.encode() + b"="
            if line.startswith(p):
                return line.split(b"=", 1)[1].strip().decode()
    return ""

CLIENT_ID = get_val("GOOGLE_CLIENT_ID")
CLIENT_SECRET = get_val("GOOGLE_CLIENT_SECRET")

auth_code = None

class CallbackHandler(server.BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            auth_code = params["code"][0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>✅ Yetkilendirme basarili!</h1><p>Bu sekmeyi kapatabilirsiniz.</p></body></html>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"<html><body><h1>❌ Hata</h1></body></html>")
    def log_message(self, format, *args):
        pass  # suppress logs

def start_server():
    """Start local HTTP server on port 8899"""
    server_addr = ("", 8899)
    httpd = socketserver.TCPServer(server_addr, CallbackHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd

def exchange_code(code):
    """Exchange authorization code for tokens"""
    import urllib.request
    data = urllib.parse.urlencode({
        "code": code,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": "http://localhost:8899/callback",
        "grant_type": "authorization_code",
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read())

def main():
    global auth_code
    
    # Start local server
    httpd = start_server()
    
    # Generate auth URL
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urllib.parse.urlencode({
            "client_id": CLIENT_ID,
            "redirect_uri": "http://localhost:8899/callback",
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
        })
    )
    
    print("🔐 GOOGLE YETKILENDIRME")
    print("=" * 50)
    print("\n1. Asagidaki linki tarayicinda AÇ:")
    print(f"\n🔗 {auth_url}\n")
    print("2. Google hesabina gir ve 'Izin ver' de")
    print("3. Tarayici otomatik olarak bu server'a yonlendirilecek")
    print("\n⏳ Bekleniyor... (15 saniye timeout)")
    
    # Try to open browser if possible (will fail on server, that's OK)
    try:
        webbrowser.open(auth_url)
    except:
        pass
    
    # Wait for callback
    import time
    for _ in range(30):  # 15 seconds max
        if auth_code:
            break
        time.sleep(0.5)
    
    httpd.shutdown()
    
    if not auth_code:
        print("\n❌ Zaman asimi. Linke tiklayip yetkilendirme yapmadin mi?")
        return
    
    print(f"\n✅ Yetkilendirme kodu alindi! Token aliniyor...")
    
    try:
        tokens = exchange_code(auth_code)
        refresh_token = tokens.get("refresh_token", "")
        access_token = tokens.get("access_token", "")
        
        if not refresh_token:
            print("⚠️ Refresh token gelmedi (ikinci seferde gelmeyebilir)")
            print("   Mevcut access token kaydediliyor...")
        
        # Save to .env
        with open(ENV_PATH, "r") as f:
            lines = f.readlines()
        
        # Remove old tokens
        prefixes = ["GOOGLE_REFRESH_TOKEN_GMAIL", "GOOGLE_ACCESS_TOKEN_GMAIL",
                     "GOOGLE_REFRESH_TOKEN_CALENDAR", "GOOGLE_ACCESS_TOKEN_CALENDAR",
                     "GOOGLE_REFRESH_TOKEN_DRIVE", "GOOGLE_ACCESS_TOKEN_DRIVE",
                     "GOOGLE_REFRESH_TOKEN_SHEETS", "GOOGLE_ACCESS_TOKEN_SHEETS"]
        for p in prefixes:
            lines = [l for l in lines if not l.startswith(p + "=")]
        
        # Add new tokens with ALL scopes
        if refresh_token:
            lines.append(f"GOOGLE_REFRESH_TOKEN_GMAIL={refre...lines.append(f"GOOGLE_REFRESH_TOKEN_CALENDAR={refre...lines.append(f"GOOGLE_REFRESH_TOKEN_DRIVE={refre...lines.append(f"GOOGLE_REFRESH_TOKEN_SHEETS={refre...lines.append(f"GOOGLE_ACCESS_TOKEN_GMAIL={acces...lines.append(f"GOOGLE_ACCESS_TOKEN_CALENDAR={acces...lines.append(f"GOOGLE_ACCESS_TOKEN_DRIVE={acces...lines.append(f"GOOGLE_ACCESS_TOKEN_SHEETS={acces...lines.append(f"#Google OAuth updated: {__import__('datetime').datetime.now().isoformat()}\n")
        
        with open(ENV_PATH, "w") as f:
            f.writelines(lines)
        
        print(f"\n✅ TOKENLAR KAYDEDILDI!")
        print(f"   Refresh: {'VAR' if refresh_token else 'YOK'}")
        print(f"   Access: {'VAR' if access_token else 'YOK'}")
        print(f"   Scope: mail, calendar, drive, sheets")
        print("\n🎉 Google entegrasyonu hazir!")
        
    except Exception as e:
        print(f"\n❌ Hata: {e}")

if __name__ == "__main__":
    main()
