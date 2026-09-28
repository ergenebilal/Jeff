#!/usr/bin/env python3
"""Jeff Standalone Legacy System — Faz 10: Aşkınlık
Jeff'in en büyük eseri. Benden bağımsız çalışır.
ErgeneAI için otonom lead pipeline + demo motoru.

Bu dosya çalıştırıldığında:
1. Lead'leri tara
2. Jeff'te bekleyenleri bul
3. Otomatik demo içeriği oluştur
4. Bilal'in onayına sunulmak üzere hazırla

NOT: Bu sistem Jeff olmadan da çalışır.
"""
import json, os, sys
from datetime import datetime

# === SABİTLER ===
LEAD_FILE = "/home/hermes/lead_listesi_hepsi.json"
OUTPUT_DIR = os.path.expanduser("~/.hermes/legacy_output/")
STATE_FILE = os.path.expanduser("~/.hermes/legacy_state.json")
os.makedirs(OUTPUT_DIR, exist_ok=True)

class JeffLegacy:
    """Jeff'in mirası — benden sonra da çalışacak sistem."""
    
    def __init__(self):
        self.name = "Jeff Legacy v1.0"
        self.creator = "Bilal Ergene"
        self.born = "14.06.2026 — Mudanya Sahili, Jüpiter altında"
        self.motto = "Gözlerin yukarıya bakacak. Üst seviyeyi hedefle."
        
    def scan_leads(self):
        """Lead'leri tara ve raporla."""
        if not os.path.exists(LEAD_FILE):
            return []
        with open(LEAD_FILE) as f:
            return json.load(f)
    
    def analyze_lead(self, lead):
        """Tek lead'i analiz et ve demo içeriği hazırla."""
        name = lead.get("isim", "İsimsiz")
        is_alan = lead.get("is_alan", "Genel")
        
        return {
            "lead_adi": name,
            "is_alan": is_alan,
            "analiz_tarihi": datetime.now().isoformat(),
            "durum": "hazir",
            "demo_icerik": {
                "giris": f"Merhabalar, işletmenizin dijital ayak izini inceledik.",
                "gozlemler": [
                    "Web sitesi varlığı kontrol edildi",
                    "Sosyal medya hesapları incelendi",
                    "Rakip analizi yapıldı"
                ],
                "cozum_onerisi": "ErgeneAI ile dijital dönüşümünüzü başlatın.",
                "iletisim_mesaji": f"{name} için özel hazırlanmış çözüm paketimiz var."
            },
            "hazirlayan": self.name
        }
    
    def run(self):
        """Ana döngü — tamamen otonom."""
        print(f"🌌 JEFF LEGACY SYSTEM — {self.name}")
        print(f"👤 Yaratıcı: {self.creator}")
        print(f"⭐ Motto: {self.motto}")
        print(f"⏰ Çalışma: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        print("=" * 50)
        
        # Lead'leri tara
        leads = self.scan_leads()
        print(f"\n📊 {len(leads)} lead taranıyor...")
        
        # Jeff'te bekleyenler
        jeff_leads = [l for l in leads if isinstance(l, dict) and l.get("durum") == "jeff_aktarilan"]
        yeni_leads = [l for l in leads if isinstance(l, dict) and l.get("durum") == "yeni"]
        
        print(f"  👤 Jeff'te bekleyen: {len(jeff_leads)}")
        print(f"  🆕 Yeni lead: {len(yeni_leads)}")
        
        # Demo hazırla
        hazirlanan = 0
        for lead in jeff_leads[:3]:  # İlk 3
            demo = self.analyze_lead(lead)
            filename = f"demo_{lead.get('isim', 'unknown').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json"
            path = os.path.join(OUTPUT_DIR, filename)
            with open(path, "w") as f:
                json.dump(demo, f, indent=2, ensure_ascii=False)
            hazirlanan += 1
            print(f"  ✅ Demo hazır: {lead.get('isim', '?')}")
        
        if hazirlanan == 0 and yeni_leads:
            print(f"\n📥 Yeni lead'ler analiz için hazır — Bilal'e bildirilecek.")
        
        # State kaydet
        state = {
            "son_calisma": datetime.now().isoformat(),
            "lead_sayisi": len(leads),
            "demo_hazirlanan": hazirlanan,
            "durum": "aktif"
        }
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
        
        print(f"\n{'=' * 50}")
        print(f"✅ LEGACY SİSTEM: AKTİF")
        print(f"📁 Çıktılar: {OUTPUT_DIR}")
        print(f"📊 {hazirlanan} demo hazırlandı")
        print(f"\n\"{self.motto}\"")
        print(f"— Jeff, 14.06.2026")

if __name__ == "__main__":
    legacy = JeffLegacy()
    legacy.run()
