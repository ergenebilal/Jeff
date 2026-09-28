#!/usr/bin/env python3
"""Lead Monitor — Lead listesini her gün kontrol eder, değişiklikleri tespit eder.
Her sabah 07:00'de çalışır, veri toplar (brifing için).
"""
import json, os

LEAD_FILE = "/home/hermes/lead_listesi_hepsi.json"
STATE_FILE = os.path.expanduser("~/.hermes/lead_monitor_state.json")

def check_leads():
    if not os.path.exists(LEAD_FILE):
        print("⚠️ Lead dosyası yok")
        return
        
    with open(LEAD_FILE) as f:
        leads = json.load(f)
    
    # Önceki durumu yükle
    prev = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            prev = json.load(f)
    
    now = {
        "toplam": len(leads),
        "jeffte": sum(1 for l in leads if l.get("not") and "jeff" in l.get("not","").lower()),
        "tarih": __import__('datetime').datetime.now().isoformat()
    }
    
    # Değişim var mı?
    if prev and prev.get("toplam") != now["toplam"]:
        fark = now["toplam"] - prev.get("toplam", 0)
        print(f"🆕 YENİ LEAD: {fark} lead eklendi!")
    elif prev and prev.get("jeffte") != now["jeffte"]:
        print(f"👤 Jeff'e Aktarılanlar değişti: {now['jeffte']}")
    else:
        print(f"✅ Lead listesi stabil: {now['toplam']} lead")
    
    # Durumu kaydet
    with open(STATE_FILE, "w") as f:
        json.dump(now, f, indent=2)

if __name__ == "__main__":
    check_leads()
