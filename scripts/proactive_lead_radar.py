#!/usr/bin/env python3
"""
CyberGene Proactive Lead Radar v1.0
7/24 Otonom Bursa ve Çevre Sanayi/Klinik Fırsat Tarayıcısı
Sitesi çökmüş, SSL'i patlamış veya puanı düşmüş hedefleri otonom tespit eder.
"""

import os
import sys
import json
import time
import urllib.request
import socket

RADAR_OUTPUT = os.path.expanduser("~/.hermes/proactive_leads.json")

TARGET_DOMAINS = [
    {"name": "Vetorka Veteriner", "domain": "vetorka.com"},
    {"name": "Vena Veteriner", "domain": "venaveteriner.com"},
    {"name": "Best Vet", "domain": "bestvetveteriner.com"},
    {"name": "ESGRUP METAL", "domain": "esgrupmetal.com"}
]

def check_domain_status(domain):
    """Domain canlılık, DNS ve HTTP durumunu denetler"""
    try:
        # DNS Check
        ip = socket.gethostbyname(domain)
    except Exception:
        return "DNS_FAILED", "DNS çözülemiyor / Domain ölü"

    try:
        url = f"https://{domain}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return "ONLINE", f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        return "HTTP_ERROR", f"HTTP Hata: {e.code}"
    except urllib.error.URLError as e:
        if "CERTIFICATE_VERIFY_FAILED" in str(e.reason):
            return "SSL_FAILED", "SSL Sertifikası Geçersiz / Patlak"
        return "CONNECTION_FAILED", f"Bağlantı Hatası: {e.reason}"
    except Exception as e:
        return "UNKNOWN_ERROR", str(e)

def run_radar_sweep():
    leads = []
    print("=== CYBERGENE PROAKTİF FIRSAT RADARI BAŞLADI ===")
    
    for target in TARGET_DOMAINS:
        name = target["name"]
        domain = target["domain"]
        status_code, detail = check_domain_status(domain)
        
        print(f"[*] Tarandı: {name} ({domain}) -> Durum: {status_code} | {detail}")
        
        if status_code != "ONLINE":
            leads.append({
                "name": name,
                "domain": domain,
                "status": status_code,
                "detail": detail,
                "detected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "opportunity": "Yüksek (Sitesi Çökmüş / Teknik Kusurlu)"
            })

    # Kaydet
    os.makedirs(os.path.dirname(RADAR_OUTPUT), exist_ok=True)
    with open(RADAR_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)
        
    print(f"=== TARAMA BİTTİ: {len(leads)} Fırsat Tespit Edildi ===")
    return leads

if __name__ == "__main__":
    run_radar_sweep()
