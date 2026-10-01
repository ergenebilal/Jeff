#!/usr/bin/env python3
"""Google Workspace OAuth onay akisi — basit, bagimliliksiz.

Kullanim:
  python3 google_onay.py url                  # onay baglantisi uret
  python3 google_onay.py kod "<donen adres>"  # adresteki kodu token'a cevir

Sunucu basiz oldugu icin: baglanti Bilal'in tarayicisinda acilir, onay verilir,
tarayici http://localhost:8765/... adresine yonlenir ve SAYFA ACMAZ (o adres
sunucuda/baska makinede). Onemli olan adres cubugundaki 'code=' degeridir —
tum adres kopyalanip buraya verilir.
"""
import json
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request

DIZIN = pathlib.Path.home() / ".google-workspace-mcp"
CRED = DIZIN / "credentials.json"
TOKEN = DIZIN / "tokens.json"
YONLENDIR = "http://localhost:8765/"
IZINLER = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.send",
]


def kimlik():
    d = json.loads(CRED.read_text())["installed"]
    return d["client_id"], d["client_secret"]


def onay_baglantisi():
    cid, _ = kimlik()
    p = {
        "client_id": cid,
        "redirect_uri": YONLENDIR,
        "response_type": "code",
        "scope": " ".join(IZINLER),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
    }
    print("https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(p))


def kodu_ver(girdi):
    cid, csecret = kimlik()
    # Tum adres verilmisse kodu ayikla; sadece kod verilmisse oldugu gibi al
    kod = girdi.strip()
    if "code=" in kod:
        q = urllib.parse.urlparse(kod.split()[0]).query or kod.split("?", 1)[-1]
        kod = urllib.parse.parse_qs(q).get("code", [""])[0]
    if not kod:
        print("HATA: kod bulunamadi")
        return 1
    veri = urllib.parse.urlencode({
        "code": kod,
        "client_id": cid,
        "client_secret": csecret,
        "redirect_uri": YONLENDIR,
        "grant_type": "authorization_code",
    }).encode()
    istek = urllib.request.Request("https://oauth2.googleapis.com/token", data=veri)
    try:
        with urllib.request.urlopen(istek, timeout=30) as c:
            y = json.loads(c.read())
    except urllib.error.HTTPError as e:
        print("HATA:", e.code, e.read().decode()[:400])
        return 1
    print("gelen alanlar:", sorted(y.keys()))
    if "refresh_token" not in y:
        print("UYARI: yenileme anahtari gelmedi (prompt=consent ile tekrar dene)")
    TOKEN.write_text(json.dumps({
        "access_token": y.get("access_token"),
        "scope": y.get("scope"),
        "token_type": y.get("token_type"),
        "refresh_token": y.get("refresh_token"),
        "expiry_date": None,
        "client_id": cid,
        "client_secret": csecret,
    }, indent=2))
    TOKEN.chmod(0o600)
    print("OK: token yazildi ->", TOKEN)
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "url":
        onay_baglantisi()
    elif len(sys.argv) >= 3 and sys.argv[1] == "kod":
        sys.exit(kodu_ver(sys.argv[2]))
    else:
        print(__doc__)
        sys.exit(1)
