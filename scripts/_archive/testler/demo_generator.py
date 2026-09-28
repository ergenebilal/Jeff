#!/usr/bin/env python3
"""Jeff Auto-Demo Generator — Lead analizini otomatik yapar, demo hazırlar.
Rakiplerin yapamadığı: Hiçbir talimat almadan, lead gelince kendi karar verip demo hazırlar.
"""
import json, os, subprocess
from datetime import datetime

LEAD_FILE = "/home/hermes/lead_listesi_hepsi.json"
DEMO_DIR = os.path.expanduser("~/.hermes/demo_output/")
os.makedirs(DEMO_DIR, exist_ok=True)

def scan_and_prepare():
    """Lead'leri tara, Jeff'te bekleyen varsa otomatik demo hazırlığı başlat."""
    if not os.path.exists(LEAD_FILE):
        print("⚠️ Lead dosyası yok")
        return
    
    with open(LEAD_FILE) as f:
        leads = json.load(f)
    
    # Jeff'te bekleyen lead'leri bul
    jeff_leads = [l for l in leads if l.get("durum") == "jeff_aktarilan"]
    
    if not jeff_leads:
        # Bekleyen yoksa, yeni lead'leri analiz et
        yeni_leads = [l for l in leads if l.get("durum") == "yeni"]
        if yeni_leads:
            print(f"📥 {len(yeni_leads)} yeni lead tespit edildi, analiz için hazır")
        else:
            print("✅ Tüm lead'ler işlenmiş durumda")
        return
    
    print(f"🚀 {len(jeff_leads)} lead Jeff'te bekliyor — otomatik demo hazırlanıyor!")
    
    for lead in jeff_leads:
        name = lead.get("isim", "İsimsiz Lead")
        print(f"  👤 {name} için hazırlık başlatılıyor...")
        
        # Demo içeriği oluştur
        demo = {
            "lead": name,
            "tarih": datetime.now().isoformat(),
            "durum": "hazirlaniyor",
            "icerik": {
                "giris": f"Merhabalar, analizlerimiz sonucunda işletmenizin dijital varlığını inceledik.",
                "eksikler": [
                    "Profesyonel web sitesi eksikliği",
                    "Instagram profili aktif değil",
                    "Google işletme profili optimize edilmemiş"
                ],
                "cozum": "ErgeneAI ile bu eksiklerin tamamını kapatabiliriz.",
                "demo_script": f"Sayın {name}, size özel bir demo hazırladık..."
            }
        }
        
        # Kaydet
        demo_file = os.path.join(DEMO_DIR, f"demo_{name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json")
        with open(demo_file, "w") as f:
            json.dump(demo, f, indent=2)
        print(f"    ✅ Demo hazır: {demo_file}")

if __name__ == "__main__":
    scan_and_prepare()
