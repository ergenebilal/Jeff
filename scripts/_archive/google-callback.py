#!/usr/bin/env python3
"""Google OAuth callback server — receives auth code, exchanges for tokens, saves to .env"""

import http.server
import json
import os
import urllib.request
import urllib.parse
import sys
import re

CLIENT_ID = "[REDACTED_CLIENT_ID]"
CLIENT_SECRET = "[REDACTED_CLIENT_SECRET]"
REDIRECT_URI = "http://aiergene.xyz/oauth-callback"
TOKEN_URI = "https://oauth2.googleapis.com/token"
ENV_PATH = os.path.expanduser("~/.hermes/.env")


class CallbackHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        # Health check / test endpoint
        if parsed.path == "/test":
            self._json(200, {"status": "ok", "message": "callback server running"})
            return

        # Root
        if parsed.path == "/":
            self._html(200, "<h1>Google OAuth Callback Server</h1><p>Ready.</p>")
            return

        # Only handle /callback or /oauth-callback
        if parsed.path not in ("/callback", "/oauth-callback"):
            self._json(404, {"error": "Not found"})
            return

        # Check for error from Google
        error = params.get("error", [None])[0]
        if error:
            self._html(400, f"<h2>&#10060; Google OAuth Hatasi</h2><p>{error}</p>")
            print(f"[ERROR] Google returned error: {error}", flush=True)
            return

        code = params.get("code", [None])[0]
        state = params.get("state", [None])[0]

        if not code:
            self._html(400, "<h2>&#10060; Hata</h2><p>Authorization code bulunamadi.</p>")
            return

        print(f"[INFO] Authorization code received! state={state}", flush=True)

        # Exchange code for tokens
        token_data = {
            "code": code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        try:
            req = urllib.request.Request(
                TOKEN_URI,
                data=urllib.parse.urlencode(token_data).encode(),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode())

            access_token = result.get("access_token", "")
            refresh_token = result.get("refresh_token", "")
            expires_in = result.get("expires_in", 3600)
            scope = result.get("scope", "")

            print(f"[INFO] Tokens received! scope={scope}", flush=True)
            print(f"[INFO] Access token: {access_token[:30]}...", flush=True)

            if refresh_token:
                print(f"[INFO] Refresh token: {refresh_token[:30]}...", flush=True)
            else:
                print("[WARN] No refresh token! User may need to revoke and re-auth.", flush=True)

            # Save to .env
            self._save_to_env(access_token, refresh_token, scope, expires_in)

            # Success HTML
            self._html(
                200,
                "<h2>&#9989; Google Hesabina Basariyla Baglandi!</h2>"
                "<p>Token'lar alindi ve .env dosyasina kaydedildi.</p>"
                "<p>Artik Jeff Gmail, Calendar, Drive ve Sheets'e erisebilir.</p>"
                "<p style='color:gray;margin-top:40px'>Bu sayfayi kapatabilirsin.</p>",
            )

        except Exception as e:
            print(f"[ERROR] Token exchange failed: {e}", flush=True)
            self._html(500, f"<h2>&#10060; Token Exchange Hatasi</h2><pre>{e}</pre>")

    def _json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _html(self, status, body):
        html = f"<html><body style='font-family:sans-serif;text-align:center;padding:40px'>{body}</body></html>"
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def _save_to_env(self, access_token, refresh_token, scope, expires_in):
        """Save tokens to .env file"""
        env_content = ""
        if os.path.exists(ENV_PATH):
            with open(ENV_PATH, "r") as f:
                env_content = f.read()

        updates = {
            "GOOGLE_ACCESS_TOKEN": access_token,
            "GOOGLE_REFRESH_TOKEN": refresh_token,
            "GOOGLE_TOKEN_SCOPE": scope,
            "GOOGLE_CLIENT_ID": CLIENT_ID,
            "GOOGLE_CLIENT_SECRET": CLIENT_SECRET,
        }

        for key, value in updates.items():
            if value:
                if re.search(rf"^{key}=.*", env_content, re.MULTILINE):
                    env_content = re.sub(
                        rf"^{key}=.*", f"{key}={value}", env_content, flags=re.MULTILINE
                    )
                else:
                    env_content += f"\n{key}={value}"

        with open(ENV_PATH, "w") as f:
            f.write(env_content.strip() + "\n")

        print(f"[INFO] Tokens saved to {ENV_PATH}", flush=True)

    def log_message(self, format, *args):
        print(f"[HTTP] {args[0]}", flush=True)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8899
    server = http.server.HTTPServer(("0.0.0.0", port), CallbackHandler)
    print(f"[START] Google OAuth callback server running on http://0.0.0.0:{port}", flush=True)
    server.serve_forever()
