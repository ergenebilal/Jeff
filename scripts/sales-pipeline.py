#!/usr/bin/env python3
"""
Sales Pipeline — Otomatik pazarlama + satış takip sistemi
Çalışma: Her gün 08:00 (cron'da)
Yapar:
  1. Gumroad satış sorgula (API)
  2. Trend analizi (web araması + Firecrawl)
  3. Günlük rapor hazırla
  4. Satış hedefi takibi ($50/ay)
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta

import urllib.request
import urllib.parse
import json

CONFIG_PATH = os.path.expanduser("~/.config/gumroad/config.json")
with open(CONFIG_PATH) as f:
    config = json.load(f)
GUMROAD_TOKEN = config["access_token"]
GUMROAD_URL = "https://api.gumroad.com/v2"

def get_sales():
    """Gumroad API'den satış verilerini al"""
    import urllib.request
    data = urllib.parse.urlencode({"access_token": GUMROAD_TOKEN}).encode()
    req = urllib.request.Request(f"{GUMROAD_URL}/sales", data=data, method="GET")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def get_products():
    import urllib.request
    req = urllib.request.Request(f"{GUMROAD_URL}/products?access_token={GUMROAD_TOKEN}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

def format_report(sales_data, products_data):
    now = datetime.now()
    lines = []
    lines.append(f"📊 GÜNLÜK SATIŞ RAPORU — {now.strftime('%d %B %Y %H:%M')}")
    lines.append("")

    # Products
    products = products_data.get("products", [])
    total_sales = sum(p.get("sales_count", 0) for p in products)
    total_revenue = sum(p.get("sales_usd_cents", 0) for p in products) / 100.0

    lines.append(f"📦 {len(products)} ürün yayında")
    lines.append(f"💰 Toplam satış: {total_sales} adet | ${total_revenue:.2f}")
    lines.append("")

    # Per product
    for p in products:
        name = p["name"]
        sales = p.get("sales_count", 0)
        rev = p.get("sales_usd_cents", 0) / 100.0
        price = p["price"] / 100.0
        tags = p.get("tags", [])
        lines.append(f"  • {name} — ${price}")
        lines.append(f"    Satış: {sales} | Gelir: ${rev:.2f}")
        lines.append(f"    Etiketler: {', '.join(tags)}")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Revenue targets
    target = 50.0
    remaining = max(0, target - total_revenue)
    days_in_month = 30
    day_of_month = now.day
    days_left = max(1, days_in_month - day_of_month)
    daily_target = remaining / days_left

    if total_revenue >= target:
        lines.append(f"🎯 HEDEF AŞILDI! ${total_revenue:.2f} / ${target:.0f} — {remaining:.0f} üstü")
    else:
        lines.append(f"🎯 $50/ay hedefi: ${total_revenue:.2f} / ${target:.0f}")
        lines.append(f"📅 Kalan {days_left} gün — günlük ${daily_target:.2f} gerekli")

    # Recommendations
    lines.append("")
    lines.append("💡 Öneriler:")
    
    # Check for products with low tags
    for p in products:
        tags = p.get("tags", [])
        name = p["name"]
        sales = p.get("sales_count", 0)
        if len(tags) < 3 and sales == 0:
            lines.append(f"  ⚠️ {name}: Sadece {len(tags)} etiket — daha fazla ekle")

    # Price optimization suggestions
    cheap_products = [p for p in products if p["price"] / 100.0 < 20 and p.get("sales_count", 0) == 0]
    if cheap_products:
        lines.append(f"  📉 {len(cheap_products)} düşük fiyatlı ürün henüz satmadı — fiyat artırılabilir")

    return "\n".join(lines)

def main():
    try:
        sales_data = get_sales()
        products_data = get_products()
        report = format_report(sales_data, products_data)
        print(report)
    except Exception as e:
        print(f"❌ Hata: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
