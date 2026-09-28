#!/usr/bin/env python3
"""Test script to check available Apify actors."""
import json, os, urllib.request

# Read token from env
token = os.environ.get("APIFY_TOKEN")
if not token:
    # Try sourcing from .env
    for line in open("/home/hermes/.env"):
        line = line.strip()
        if line.startswith("APIFY_TOKEN="):
            token = line.split("=", 1)[1].strip()
            break

print(f"Token loaded: {token[:8]}...{token[-4:] if token else 'NOT FOUND'}")

# Search Apify store
req = urllib.request.Request(
    "https://api.apify.com/v2/store/acts?search=google+maps+scraper&limit=5",
    headers={"Authorization": f"Bearer {token}"}
)
resp = json.loads(urllib.request.urlopen(req).read())
for a in resp.get("data", {}).get("items", []):
    print(f"  {a['username']}/{a['name']} - {a['title']}")

# Also try to search for free actors  
req2 = urllib.request.Request(
    "https://api.apify.com/v2/store/acts?search=google+maps&limit=5&pricing=free",
    headers={"Authorization": f"Bearer {token}"}
)
resp2 = json.loads(urllib.request.urlopen(req2).read())
print("\nFree actors:")
for a in resp2.get("data", {}).get("items", []):
    print(f"  {a['username']}/{a['name']} - {a['title']}")
