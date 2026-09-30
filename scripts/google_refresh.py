#!/usr/bin/env python3
"""Google erisimini tazele: arsivdeki uygulama kimligi + tokens.json yenileme anahtari."""
import json, re, sys, urllib.request, urllib.parse, urllib.error, pathlib, datetime

ARCHIVE = "/home/hermes/jeff_repo/scripts/_archive/google-callback.py"
TOKENS  = "/home/hermes/.google-workspace-mcp/tokens.json"

def grab(name):
    """Arsiv scriptinden bir sabitin DEGERINI al (yazdirmadan)."""
    s = pathlib.Path(ARCHIVE).read_text(encoding="utf-8", errors="ignore")
    m = re.search(rf'^{name}\s*=\s*"([^"]+)"', s, re.M)
    return m.group(1) if m else None

cid, csec = grab("CLIENT_ID"), grab("CLIENT_SECRET")
if not cid or not csec:
    print("!! uygulama kimligi arsivde bulunamadi"); sys.exit(1)
print(f"uygulama kimligi: VAR (id {len(cid)} kr, secret {len(csec)} kr)")

tok = json.load(open(TOKENS))
rt = tok.get("refresh_token")
print(f"yenileme anahtari: {'VAR' if rt else 'YOK'}")

# token yenile
data = urllib.parse.urlencode({
    "client_id": cid, "client_secret": csec,
    "refresh_token": rt, "grant_type": "refresh_token",
}).encode()
try:
    r = urllib.request.urlopen(urllib.request.Request(
        "https://oauth2.googleapis.com/token", data=data), timeout=25)
    res = json.loads(r.read())
    at = res.get("access_token")
    print(f"\n>>> TAZELEME BASARILI. yeni anahtar {len(at)} kr, gecerlilik {res.get('expires_in')} sn")
except urllib.error.HTTPError as e:
    body = e.read().decode()[:300]
    print(f"\n>>> TAZELEME BASARISIZ: HTTP {e.code}")
    print(f"    {body}")
    sys.exit(2)

# kim oldugumuzu ve takvimleri gor
def api(url):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {at}"})
    return json.loads(urllib.request.urlopen(req, timeout=25).read())

try:
    cals = api("https://www.googleapis.com/calendar/v3/users/me/calendarList")
    print(f"\n=== TAKVIMLER ({len(cals.get('items',[]))}) ===")
    for c in cals.get("items", []):
        print(f"  {'(ANA)' if c.get('primary') else '     '} {c.get('summary','?')[:45]:45s} | {c.get('id','')[:45]}")
    print(f"\nkimlik: {cals.get('summary','?')}  |  zaman dilimi: {cals.get('timeZone','?')}")
except Exception as e:
    print("takvim listesi alinamadi:", type(e).__name__, str(e)[:150])

# taze token'i kaydet (MCP'nin kullanacagi yere)
tok["access_token"] = at
tok["expiry_date"] = int((datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=res.get("expires_in",3600))).timestamp()*1000)
pathlib.Path(TOKENS).write_text(json.dumps(tok, indent=2), encoding="utf-8")
print(f"\ntaze token kaydedildi: {TOKENS}")
