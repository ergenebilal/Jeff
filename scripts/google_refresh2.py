#!/usr/bin/env python3
"""Tam token dosyasiyla (client_id + secret + refresh) Google erisimini tazele."""
import json, sys, urllib.request, urllib.parse, urllib.error, pathlib, datetime

SRC = "/opt/google-workplace-mcp/tokens.json"
OUT = "/home/hermes/.google-workspace-mcp/tokens.json"

d = json.load(open(SRC))
print("anahtarlar:", ", ".join(d.keys()))
exp = d.get("expiry_date")
if exp:
    try:
        print("mevcut bitis:", datetime.datetime.fromtimestamp(int(exp)/1000, datetime.UTC).strftime("%Y-%m-%d %H:%M"))
    except Exception:
        print("mevcut bitis:", exp)

cid, csec, rt = d.get("client_id"), d.get("client_secret"), d.get("refresh_token")
print(f"client_id={'VAR' if cid else 'YOK'}  secret={'VAR' if csec else 'YOK'}  refresh={'VAR' if rt else 'YOK'}")
if not all([cid, csec, rt]):
    print("!! eksik alan"); sys.exit(1)

data = urllib.parse.urlencode({
    "client_id": cid, "client_secret": csec,
    "refresh_token": rt, "grant_type": "refresh_token",
}).encode()
try:
    res = json.loads(urllib.request.urlopen(urllib.request.Request(
        "https://oauth2.googleapis.com/token", data=data), timeout=25).read())
    at = res["access_token"]
    print(f"\n>>> TAZELEME BASARILI ({res.get('expires_in')} sn)")
except urllib.error.HTTPError as e:
    print(f"\n>>> BASARISIZ HTTP {e.code}: {e.read().decode()[:250]}")
    sys.exit(2)

def api(url):
    return json.loads(urllib.request.urlopen(urllib.request.Request(
        url, headers={"Authorization": f"Bearer {at}"}), timeout=25).read())

cals = api("https://www.googleapis.com/calendar/v3/users/me/calendarList")
print(f"\n=== TAKVIMLER ({len(cals.get('items',[]))}) ===")
for c in cals.get("items", []):
    print(f"  {'ANA' if c.get('primary') else '   '} {c.get('summary','?')[:42]:42s} | {c.get('id','')[:42]}")

# taze token'i diske yaz (eksiksiz)
d["access_token"] = at
d["expiry_date"] = int((datetime.datetime.now(datetime.UTC)
                        + datetime.timedelta(seconds=res.get("expires_in", 3600))).timestamp()*1000)
pathlib.Path(OUT).write_text(json.dumps(d, indent=2), encoding="utf-8")
print(f"\ntaze token yazildi -> {OUT}")
