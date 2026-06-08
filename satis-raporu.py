#!/usr/bin/env python3
"""Günlük satış özeti - Gumroad CLI üzerinden"""
import subprocess, json
from datetime import datetime

try:
    result = subprocess.run(
        ["gumroad", "products", "list", "--json"],
        capture_output=True, text=True, timeout=15
    )
    data = json.loads(result.stdout)
    products = data.get("products", [])
    
    print(f"📊 GÜNLÜK SATIŞ RAPORU - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 40)
    
    total_revenue = 0
    for p in products:
        name = p.get("name", "?")[:40]
        price = p.get("price", 0) / 100
        sales = p.get("sales_count", 0)
        revenue = price * sales
        published = "✅" if p.get("published") else "📝"
        total_revenue += revenue
        print(f"{published} {name}")
        print(f"   ${price:.2f} x {sales} sales = ${revenue:.0f}")
    
    print("=" * 40)
    print(f"💰 TOPLAM: ${total_revenue:.0f}")
    print(f"📦 {len(products)} products, {sum(p.get('sales_count',0) for p in products)} total sales")
    
except Exception as e:
    print(f"❌ Rapor hatası: {e}")
