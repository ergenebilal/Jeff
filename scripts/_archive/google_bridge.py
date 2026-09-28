#!/usr/bin/env python3
"""Google API Entegrasyonu — Token refresh + servis erisimi"""

import os
import json
import urllib.request
import urllib.parse
from datetime import datetime

HOME = os.path.expanduser("~")
ENV_PATH = os.path.join(HOME, ".hermes", ".env")

def _read_env(key: str) -> str:
    """Read a value from .env file"""
    with open(ENV_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith(key + "="):
                return line.split("=", 1)[1]
    return ""

def refresh_token(service: str) -> dict:
    """Refresh Google OAuth access token"""
    client_id = _read_env("GOOGLE_CLIENT_ID")
    client_secret = _read_env("GOOGLE_CLIENT_SECRET")
    prefix = service.upper()
    refresh_tok = _read_env(f"GOOGLE_REFRESH_TOKEN_{prefix}")
    
    if not refresh_tok:
        return {"error": f"No refresh token for {service}"}
    
    data = urllib.parse.urlencode({
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_tok,
        "grant_type": "refresh_token",
    }).encode()
    
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        return result
    except urllib.error.HTTPError as e:
        body = json.loads(e.read())
        return {"error": body.get("error_description", str(e))}

def test_gmail() -> dict:
    """Test Gmail API — read inbox count"""
    tok = refresh_token("GMAIL")
    if "error" in tok:
        return tok
    
    access = tok.get("access_token", "")
    if not access:
        return {"error": "No access token"}
    
    req = urllib.request.Request(
        "https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=1",
        headers={"Authorization": f"Bearer {access}"}
    )
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read())

def test_calendar() -> dict:
    """Test Calendar API — list upcoming events"""
    tok = refresh_token("CALENDAR")
    if "error" in tok:
        return tok
    
    access = tok.get("access_token", "")
    now = datetime.utcnow().isoformat() + "Z"
    
    req = urllib.request.Request(
        f"https://www.googleapis.com/calendar/v3/calendars/primary/events?timeMin={now}&maxResults=5&orderBy=startTime&singleEvents=true",
        headers={"Authorization": f"Bearer {access}"}
    )
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read())

def main():
    print("🔑 Google Entegrasyon Testi")
    print("=" * 50)
    
    # Test Gmail
    print("\n📧 Gmail test...")
    result = test_gmail()
    if "error" in result:
        print(f"   ❌ {result['error']}")
    else:
        count = result.get("resultSizeEstimate", 0)
        print(f"   ✅ {count} mesaj var")
    
    # Test Calendar
    print("\n📅 Calendar test...")
    result = test_calendar()
    if "error" in result:
        print(f"   ❌ {result['error']}")
    else:
        items = result.get("items", [])
        print(f"   ✅ {len(items)} etkinlik bulundu")
        for item in items[:3]:
            start = item.get("start", {}).get("dateTime", item.get("start", {}).get("date", "?"))
            print(f"      • {item.get('summary','?')} — {start}")

if __name__ == "__main__":
    main()
