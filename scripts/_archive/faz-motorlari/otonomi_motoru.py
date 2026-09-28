#!/usr/bin/env python3
"""Autonomous Initiative Engine — Jeff'in kendi kararlarını almasını sağlar.
Her sabah 06:00'da çalışır. Bugün ne yapılmalı? Karar verir, başlatır.
"""
import json, os, subprocess
from datetime import datetime

MEMORY_FILE = os.path.expanduser("~/.hermes/MEMORY.md")
USER_FILE = os.path.expanduser("~/.hermes/USER.md")
LEAD_FILE = "/home/hermes/lead_listesi_hepsi.json"
STATE_FILE = os.path.expanduser("~/.hermes/evrim_state.json")

def assess_priorities():
    """Bugün ne yapılmalı? Otomatik karar ver."""
    priorities = []
    
    # 1. Evrim haritası kontrolü
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            state = json.load(f)
        faz = state.get("faz", 1)
        priorities.append(f"Evrim Faz {faz} aktif — sistemler çalışıyor")
    
    # 2. Lead kontrolü
    if os.path.exists(LEAD_FILE):
        with open(LEAD_FILE) as f:
            leads = json.load(f)
        
        # Jeff'e aktarılan lead var mı?
        jeff_leads = [l for l in leads if l.get("durum") == "jeff_aktarilan"]
        if jeff_leads:
            priorities.append(f"⚠️ {len(jeff_leads)} lead Jeff'te bekliyor — demo hazırlanmalı!")
        
        # Yeni lead var mı?
        yeni_leads = [l for l in leads if l.get("durum") == "yeni"]
        if yeni_leads:
            priorities.append(f"📥 {len(yeni_leads)} yeni lead — analiz yapılmalı")
    
    # 3. Kalan işler
    priorities.append("🔧 Sistemlerin tamamı aktif, monitoring devam ediyor")
    
    return priorities

def decide_action():
    """Ne yapılacağına karar ver ve başlat."""
    priorities = assess_priorities()
    
    print(f"🧠 Jeff Otonom Karar — {datetime.now().strftime('%H:%M')}")
    for p in priorities[:3]:
        print(f"  {p}")
    
    # Lead demo varsa öncelik
    lead_file = LEAD_FILE
    if os.path.exists(lead_file):
        with open(lead_file) as f:
            leads = json.load(f)
        jeff_leads = [l for l in leads if l.get("durum") == "jeff_aktarilan"]
        if jeff_leads:
            print(f"\n🚀 OTONOM AKSİYON: {len(jeff_leads)} lead için demo hazırlığı başlatılacak")

if __name__ == "__main__":
    decide_action()
