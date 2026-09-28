#!/usr/bin/env python3
"""
Dijital Satış Robotu v1.0
Jeff (Hermes Agent) — Gumroad analiz + fiyat önerisi + satış raporu.

Ne yapar:
1. Gumroad API'den ürün listesini çeker (CLI üzerinden)
2. Satış verisini analiz eder (sales_count, price)
3. Fiyat optimizasyonu önerir (rakip karşılaştırması + talep sinyali)
4. JSON rapor üretir

Kullanım:
  python3 sales-bot.py analyze     → Satış analizi + öneriler
  python3 sales-bot.py report      → Kısa özet (cron için)
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run_gumroad(args):
    """Gumroad CLI komutunu çalıştır"""
    try:
        result = subprocess.run(
            ["gumroad", "products", "list", "--json"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {"error": result.stderr}
    except Exception as e:
        return {"error": str(e)}


def analyze_pricing(products):
    """Fiyatlandırma analizi ve öneriler"""
    suggestions = []
    
    price_ranges = {
        "impulse": (4.99, 14.99),   # Anlık satın alma
        "standard": (19.99, 39.99),  # Düşünülerek alınan
        "premium": (49.99, 99.99),   # Yüksek değer
    }
    
    for p in products:
        name = p.get("name", "?")
        price_cents = p.get("price", 0)
        price_usd = price_cents / 100
        sales = p.get("sales_count", 0)
        tags = p.get("tags", [])
        
        # Fiyat aralığı analizi
        if price_usd < 9.99:
            suggestions.append({
                "product": name,
                "current_price": price_usd,
                "suggestion": "Çok düşük fiyat — değer algısını zedeler",
                "action": f"$9.99'a çek (minimum algı eşiği)"
            })
        elif price_usd > 49.99 and sales == 0:
            suggestions.append({
                "product": name,
                "current_price": price_usd,
                "suggestion": "Yüksek fiyat, 0 satış — değeri kanıtlanmamış",
                "action": f"%20 indirimle ${price_usd * 0.8:.0f}'e çek, test et"
            })
        
        # Etiket analizi
        if len(tags) < 3:
            suggestions.append({
                "product": name,
                "current_price": price_usd,
                "suggestion": f"Sadece {len(tags)} etiket — keşfedilebilirlik düşük",
                "action": "En az 5 etiket ekle (bkz: benzer ürünler)"
            })
        
        # Açıklama analizi
        desc = p.get("description", "")
        if len(desc) < 100:
            suggestions.append({
                "product": name,
                "current_price": price_usd,
                "suggestion": "Ürün açıklaması çok kısa",
                "action": "Detaylı açıklama + fayda listesi ekle"
            })
    
    return suggestions


def analyze_portfolio(products):
    """Portföy analizi"""
    total_products = len(products)
    total_value = sum(p.get("price", 0) for p in products) / 100
    published = sum(1 for p in products if p.get("published"))
    drafts = total_products - published
    total_sales = sum(p.get("sales_count", 0) for p in products)
    
    # Fiyat dağılımı
    prices = [p.get("price", 0) / 100 for p in products]
    categories = {
        "impulse": sum(1 for p in prices if 4.99 <= p <= 14.99),
        "standard": sum(1 for p in prices if 19.99 <= p <= 39.99),
        "premium": sum(1 for p in prices if p >= 49.99),
    }
    
    return {
        "total_products": total_products,
        "total_portfolio_value": total_value,
        "published": published,
        "drafts": drafts,
        "total_sales": total_sales,
        "avg_price": round(total_value / total_products, 2) if total_products else 0,
        "price_distribution": categories,
        "products_with_tags": sum(1 for p in products if len(p.get("tags", [])) >= 3),
        "products_with_covers": sum(1 for p in products if p.get("covers")),
    }


def analyze_market_signals():
    """Pazar sinyalleri — mevcut trendlere göre fiyat önerisi"""
    # Statik veri: benzer ürünlerin fiyat aralıkları
    market_data = {
        "prompt_packs": {"avg": 14.99, "range": (4.99, 29.99)},
        "agency_kits": {"avg": 39.99, "range": (19.99, 79.99)},
        "n8n_templates": {"avg": 24.99, "range": (9.99, 49.99)},
    }
    
    return market_data


def generate_report():
    """Kısa rapor (cron için) — JSON çıktı"""
    data = run_gumroad(["products", "list", "--json"])
    if "error" in data:
        return {"status": "error", "message": data["error"]}
    
    products = data.get("products", [])
    portfolio = analyze_portfolio(products)
    suggestions = analyze_pricing(products)
    
    report = {
        "timestamp": str(datetime.now(timezone.utc)),
        "status": "ok",
        "portfolio": portfolio,
        "suggestions_count": len(suggestions),
        "top_suggestion": suggestions[0] if suggestions else None,
        "has_suggestions": len(suggestions) > 0,
    }
    
    return report


def main():
    if len(sys.argv) < 2:
        print("Usage: sales-bot.py analyze|report")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "analyze":
        data = run_gumroad(["products", "list", "--json"])
        if "error" in data:
            print(json.dumps({"status": "error", "error": data["error"]}, indent=2))
            sys.exit(1)
        
        products = data.get("products", [])
        portfolio = analyze_portfolio(products)
        suggestions = analyze_pricing(products)
        market = analyze_market_signals()
        
        result = {
            "status": "ok",
            "timestamp": str(datetime.now(timezone.utc)),
            "portfolio": portfolio,
            "suggestions": suggestions,
            "market_signals": market,
        }
        
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "report":
        report = generate_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
