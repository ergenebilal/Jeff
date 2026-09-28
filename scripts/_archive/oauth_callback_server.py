#!/usr/bin/env python3
"""Callback server for Google OAuth"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse, json

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        code = params.get("code", [None])[0]
        error = params.get("error", [None])[0]
        
        if code:
            with open("/tmp/google_auth_code.txt", "w") as f:
                f.write(code)
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Yetkilendirme Basarili!</h1><p>Kod alindi. Simdi Telegram'a don.</p></body></html>")
            print(f"\n✅ KOD ALINDI: {code[:30]}...", flush=True)
        elif error:
            self.send_response(400)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            desc = params.get("error_description", [""])[0]
            self.wfile.write(f"<html><body><h1>Hata</h1><p>{error}: {desc}</p></body></html>".encode())
            print(f"\n❌ HATA: {error}: {desc}", flush=True)
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Google OAuth Callback</h1><p>Bu sayfa sadece callback icin.</p></body></html>")
    
    def log_message(self, format, *args):
        pass

print("🌐 Google OAuth callback sunucusu baslatiliyor...", flush=True)
server = HTTPServer(("0.0.0.0", 8899), Handler)
print("✅ http://0.0.0.0:8899 dinleniyor", flush=True)
server.serve_forever()
