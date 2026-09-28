#!/usr/bin/env python3
"""Gumroad ürün denetim raporu"""
import json, urllib.request

with open("/home/hermes/.config/gumroad/config.json") as f:
    config = json.load(f)
TOKEN = config["access_token"]
req = urllib.request.Request(f"https://api.gumroad.com/v2/products?access_token={TOKEN}")
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())

print("=" * 55)
print("GUMROAD URUN DENETIM RAPORU")
print("=" * 55)

all_ok = True
for p in data.get("products", []):
    name = p["name"][:45]
    tags = p.get("tags", [])
    desc = p.get("description", "")
    has_preview = bool(p.get("preview_url"))
    has_files = bool(p.get("files") and len(p["files"]) > 0)
    sales = p.get("sales_count", 0)
    permalink = p.get("custom_permalink", "")
    price = p["price"] / 100
    
    issues = []
    if len(tags) < 5: issues.append("ETIKET")
    if not has_preview: issues.append("THUMBNAIL")
    if not has_files: issues.append("DOSYA")
    if len(desc) < 300: issues.append("ACIKLAMA")
    if "$" not in desc: issues.append("FIYAT_VURGUSU")
    
    if issues: all_ok = False
    
    status = "OK" if not issues else "WARN"
    print(f"\n[{status}] {name}")
    print(f"   Price: ${price:.2f}  Sales: {sales}")
    print(f"   Thumbnail: {'Y' if has_preview else 'N'}  File: {'Y' if has_files else 'N'}")
    print(f"   Tags: {len(tags)}/5  Desc: {len(desc)} chars")
    print(f"   URL: https://ergene.gumroad.com/l/{permalink}")
    if issues:
        print(f"   MISSING: {', '.join(issues)}")

print(f"\n{'=' * 55}")
print(f"RESULT: {'ALL GOOD' if all_ok else 'ISSUES FOUND'}")
print(f"{'=' * 55}")
