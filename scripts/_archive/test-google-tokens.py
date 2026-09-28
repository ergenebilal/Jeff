#!/usr/bin/env python3
"""Test Google API tokens"""
import os, re, json, urllib.request

# Read token
with open(os.path.expanduser("~/.hermes/.env")) as f:
    env = f.read()

match = re.search(r'^GOOGLE_ACCESS_TOKEN=*** env, re.MULTILINE)
token = match.group(1) if match else None

if not token:
    print("NO TOKEN")
    exit(1)

print(f"Token OK: {token[:20]}...")

# Gmail
req = urllib.request.Request("https://gmail.googleapis.com/gmail/v1/users/me/profile",
    headers={"Authorization": f"Bearer {token}"})
data = json.loads(urllib.request.urlopen(req).read())
print(f"\nGMAIL: {data['emailAddress']} - {data['messagesTotal']} messages")

# Calendar
req = urllib.request.Request("https://www.googleapis.com/calendar/v3/calendars/primary/events?maxResults=2",
    headers={"Authorization": f"Bearer {token}"})
data = json.loads(urllib.request.urlopen(req).read())
events = data.get('items', [])
print(f"\nCALENDAR: {len(events)} upcoming events")
for e in events:
    start = e['start'].get('dateTime', e['start'].get('date', '?'))
    print(f"  - {e['summary']} ({start})")

# Drive
req = urllib.request.Request("https://www.googleapis.com/drive/v3/files?pageSize=3",
    headers={"Authorization": f"Bearer {token}"})
data = json.loads(urllib.request.urlopen(req).read())
print(f"\nDRIVE: {len(data.get('files', []))} files")
for f in data.get('files', []):
    print(f"  - {f['name']} ({f.get('mimeType', '?')})")

print("\n✅ ALL SERVICES WORKING!")
