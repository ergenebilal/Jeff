#!/usr/bin/env python3
"""X API OAuth 1.0a setup — generate access tokens from consumer key/secret."""
import os, sys, json
from requests_oauthlib import OAuth1Session

KEY = os.environ.get("X_API_KEY") or "71VjhDoRxWkYJ1SGGs4JIluZJ"
SECRET = os.environ.get("X_API_SECRET") or "poRwRg31z94TJH5IUW37ovHhbvo0We9Bl2ltqlpIIcavl7iOPg"

# --- Step 2 (--pin ile çağrılırsa) ---
if len(sys.argv) > 1 and sys.argv[1] == "--pin":
    pin = sys.argv[2] if len(sys.argv) > 2 else input("PIN kodu: ").strip()
    with open("/tmp/x_oauth_state.json") as f:
        state = json.load(f)
    r_key = state["request_token"]
    r_secret = state["request_secret"]

    oauth = OAuth1Session(KEY, client_secret=SECRET,
                          resource_owner_key=r_key,
                          resource_owner_secret=r_secret)
    try:
        tokens = oauth.fetch_access_token("https://api.twitter.com/oauth/access_token", verifier=pin)
        access_token = tokens.get("oauth_token")
        access_secret = tokens.get("oauth_token_secret")
        screen_name = tokens.get("screen_name", "???")

        print(f"✅ Access Token: {access_token}")
        print(f"✅ Access Secret: {access_secret}")
        print(f"✅ User: @{screen_name}")

        # .env.x'e yaz
        env_path = os.environ.get("X_ENV_PATH", "/opt/hermes/.env.x")
        with open(env_path) as f:
            lines = f.read().splitlines()
        for i, line in enumerate(lines):
            if line.startswith("X_ACCESS_TOKEN="):
                lines[i] = f"X_ACCESS_TOKEN={access_token}"
            elif line.startswith("X_ACCESS_SECRET="):
                lines[i] = f"X_ACCESS_SECRET={access_secret}"
        with open(env_path, "w") as f:
            f.write("\n".join(lines) + "\n")
        print(f"✅ {env_path} güncellendi.")
    except Exception as e:
        print(f"❌ Access Token hatası: {e}")
        sys.exit(1)
    sys.exit(0)

# --- Step 1: Request Token ---
print("=== ADIM 1: Request Token alınıyor ===")
oauth = OAuth1Session(KEY, client_secret=SECRET)
try:
    fetch_response = oauth.fetch_request_token(
        "https://api.twitter.com/oauth/request_token"
    )
    resource_owner_key = fetch_response.get("oauth_token")
    resource_owner_secret = fetch_response.get("oauth_token_secret")
    print(f"✅ Request Token alındı")
except Exception as e:
    print(f"❌ Request Token hatası: {e}")
    print(f"\nDetay: OAuth 1.0a imzalama başarısız. Consumer Key/Secret doğru mu?")
    sys.exit(1)

# Step 2: Authorization URL
auth_url = (
    "https://api.twitter.com/oauth/authorize?"
    f"oauth_token={resource_owner_key}"
)
print(f"\n=== ADIM 2: Şu URL'yi tarayıcında aç ===")
print(f"\n   {auth_url}\n")
print("X uygulamasına 'İzin Ver' (Authorize) de.")
print("Sana bir PIN kodu gösterecek.")
print(f"\nPIN'i alınca şu komutu çalıştır:")
print(f"\n   python3 ~/.hermes/scripts/x-oauth-setup.py --pin PIN_KODU\n")

# Save temp state
state = {"request_token": resource_owner_key, "request_secret": resource_owner_secret}
with open("/tmp/x_oauth_state.json", "w") as f:
    json.dump(state, f)
print(f"Geçici state dosyası /tmp/x_oauth_state.json kaydedildi.")
print("(PIN komutu verilene kadar state bekler.)")
