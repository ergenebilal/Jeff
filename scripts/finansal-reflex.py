#!/usr/bin/env python3
"""
Finansal Reflex v1.0 — Bütçe/Ödeme Takip Sistemi
Jeff (Hermes Agent) — Gelir-gider takibi, ödeme hatırlatma, bütçe yönetimi.

Veri kaynakları:
1. Memory'deki finans bilgileri (Denizbank, KMH, sigorta)
2. Gumroad API (gelir)
3. Manuel kayıt (kurye geliri, nakit akışı)
4. Token guard (AI maliyeti)

Çıktılar:
- Ödeme uyarısı (bugün/vadesi yaklaşan)
- Bütçe durumu
- Gelir-gider dengesi
"""

import json
import os
import subprocess
import sys
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

# === VERİTABANI ===

# Statik finans verisi (memory'den + session_search'ten derlendi)
FINANCIAL_DATA = {
    "debts": [
        {
            "name": "Denizbank Ticari Kart",
            "total": 35925,
            "minimum_payment": 9000,
            "due_date": "2026-06-11",
            "severity": "kritik",
            "category": "borc",
            "note": "Asgari ~9000 TL, tamamı 35925 TL. 11 Haziran Perşembe.",
        },
        {
            "name": "Yapı Kredi KMH",
            "total": 7000,
            "minimum_payment": 7000,
            "due_date": "2026-06-15",
            "severity": "uyari",
            "category": "borc",
            "note": "KMH, faiz işliyor. 15 Haziran Pazartesi.",
        },
        {
            "name": "Motor Sigortası",
            "total": None,  # Bilinmiyor — kazalı dosya açık
            "minimum_payment": None,
            "due_date": "2026-06-14",
            "severity": "uyari",
            "category": "sigorta",
            "note": "Kazalı dosya nedeniyle yüksek çıkabilir. 14 Haziran Pazar.",
        },
    ],
    "income_sources": {
        "kurye_daily_target": 3000,
        "kurye_daily_ideal": 3500,
        "ai_monthly_target": 0,  # Henüz 0
    },
    "monthly_fixed_costs": {
        "motor_benzin": 7875,
        "araba_mazot": 6000,
        "muhasebe": 2500,
        "yemek": 3500,
        "telefon": 600,
        "api": 600,
        "sunucu": 300,
        "kahve": 250,
        "total": 21625,
    },
    "last_updated": "2026-06-09",
}


def get_today():
    """Bugünün tarihi"""
    return date.today()


def days_until(target_date_str):
    """Vadeye kalan gün sayısı"""
    try:
        target = datetime.strptime(target_date_str, "%Y-%m-%d").date()
        delta = (target - get_today()).days
        return delta
    except (ValueError, TypeError):
        return None


def check_urgent_payments():
    """Bugün/yakında ödenmesi gerekenleri kontrol et"""
    today = get_today()
    alerts = []

    for debt in FINANCIAL_DATA["debts"]:
        days = days_until(debt["due_date"])
        if days is None:
            continue

        debt_info = {
            "name": debt["name"],
            "due_date": debt["due_date"],
            "days_left": days,
            "amount": debt["minimum_payment"] or debt["total"],
            "severity": debt["severity"],
            "note": debt["note"],
        }

        if days < 0:
            debt_info["status"] = "gecmis"
            debt_info["severity"] = "kritik"
            alerts.append(debt_info)
        elif days == 0:
            debt_info["status"] = "bugun"
            debt_info["severity"] = "kritik"
            alerts.append(debt_info)
        elif days <= 3:
            debt_info["status"] = "acil"
            alerts.append(debt_info)
        elif days <= 7:
            debt_info["status"] = "yaklasan"
            alerts.append(debt_info)
        else:
            debt_info["status"] = "izle"
            alerts.append(debt_info)

    return alerts


def calculate_weekly_need(alerts):
    """Bu hafta için gereken minimum nakit"""
    total = 0
    for a in alerts:
        if a["status"] in ("gecmis", "bugun", "acil", "yaklasan") and a["amount"]:
            total += a["amount"]
    return total


def check_gumroad_income():
    """Gumroad API'den satış/gelir verisi al"""
    try:
        result = subprocess.run(
            ["gumroad", "products", "list", "--json"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            products = data.get("products", [])
            total_sales = sum(p.get("sales_count", 0) for p in products)
            total_revenue = sum(p.get("sales_usd_cents", 0) for p in products) / 100
            return {"status": "ok", "total_sales": total_sales, "total_revenue_usd": total_revenue}
        return {"status": "error", "message": result.stderr}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def generate_report():
    """Tam finansal durum raporu"""
    today = get_today()
    alerts = check_urgent_payments()
    weekly_need = calculate_weekly_need(alerts)
    gumroad = check_gumroad_income()

    report = {
        "timestamp": str(datetime.now(timezone.utc)),
        "today": str(today),
        "urgent_payments": alerts,
        "weekly_minimum_need": weekly_need,
        "gumroad_income": gumroad,
        "monthly_fixed_costs": FINANCIAL_DATA["monthly_fixed_costs"]["total"],
        "recommendation": "",
    }

    # Öneri üret
    urgent = [a for a in alerts if a["status"] in ("gecmis", "bugun", "acil")]
    approaching = [a for a in alerts if a["status"] in ("yaklasan",)]

    if urgent:
        report["recommendation"] = f"⚠️ Acil ödemeler: {', '.join(a['name'] for a in urgent)}. "
        report["recommendation"] += f"Bu hafta minimum {weekly_need} TL lazım. Kurye planı yap."
    elif approaching:
        report["recommendation"] = f"📅 Yaklaşan ödemeler var. Hazırlıklı ol."
    else:
        report["recommendation"] = "✅ Vadesi gelmiş acil ödeme yok."

    if gumroad.get("status") == "ok" and gumroad["total_sales"] == 0:
        report["recommendation"] += " Gumroad'da hala 0 satış — pazarlama başlatılmalı."

    return report


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        report = generate_report()
        # Kısa çıktı
        alerts = report["urgent_payments"]
        print(f"💳 Finansal Reflex — {report['today']}")
        print()
        for a in alerts:
            icon = {"gecmis": "🔴", "bugun": "🔴", "acil": "🟡", "yaklasan": "🟢", "izle": "⚪"}
            print(f"  {icon.get(a['status'], '⚪')} {a['name']}: {a['days_left']} gün | {a.get('amount', '?')} TL")
        print(f"\n📊 Haftalık minimum nakit ihtiyacı: ~{report['weekly_minimum_need']} TL")
        print(f"📦 Gumroad: {report['gumroad_income'].get('total_sales', 0)} satış, ${report['gumroad_income'].get('total_revenue_usd', 0)}")
        print(f"\n💡 {report['recommendation']}")

    elif len(sys.argv) > 1 and sys.argv[1] == "check":
        # Ödeme günü kontrolü — cron için
        alerts = check_urgent_payments()
        today_alerts = [a for a in alerts if a["status"] in ("gecmis", "bugun", "acil")]
        if today_alerts:
            report = generate_report()
            print(json.dumps(report, indent=2, ensure_ascii=False))
        else:
            print(json.dumps({"status": "clean", "today": str(get_today())}))

    else:
        report = generate_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
