#!/usr/bin/env python3
"""Günlük satış takibi — Gumroad revenue + hedef"""
import json, os, datetime, urllib.request

HOME = os.path.expanduser("~")
TOKEN_FILE = "/home/hermes/.config/gumroad/config.json"
LOG_FILE = os.path.join(HOME, ".hermes", "sales_log.json")

def check():
    if not os.path.isfile(TOKEN_FILE):
        return -1
    with open(TOKEN_FILE) as f:
        token = json.load(f)["access_token"]
    req = urllib.request.Request(f"https://api.gumroad.com/v2/products?access_token={token}")
    resp = urllib.request.urlopen(req)
    data = json.loads(resp.read())
    total = 0
    for p in data.get("products", []):
        total += p.get("sales_count", 0) or 0
    return total

def main():
    today = datetime.date.today().isoformat()
    sales = check()
    
    log = []
    if os.path.isfile(LOG_FILE):
        with open(LOG_FILE) as f:
            log = json.load(f)
    
    log.append({"date": today, "gumroad_sales": sales, "ts": datetime.datetime.now().isoformat()})
    log = log[-90:]
    
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=2)
    
    prev = log[-2].get("gumroad_sales", 0) if len(log) > 1 else 0
    
    if sales > prev:
        print(f"🎉 YENI SATIS! Toplam: {sales} (+{sales - prev})")
    elif sales > 0:
        print(f"💰 Toplam satış: {sales} (değişim yok)")
    else:
        # Sessiz, satış yoksa bildirme
        pass
    
    sys.exit(0)

if __name__ == "__main__":
    main()
