#!/usr/bin/env python3
"""Lead Stratejisti — Otomatik lead analizi ve demo hazırlık pipeline'ı."""
import json, os, sys, datetime

LEADS_FILE = os.path.expanduser("~") + "/lead_listesi_hepsi.json"

def lead_oku():
    if not os.path.isfile(LEADS_FILE):
        print("❌ Lead dosyası bulunamadı")
        return []
    with open(LEADS_FILE) as f:
        return json.load(f)

def lead_kaydet(leads):
    with open(LEADS_FILE, "w", encoding="utf-8") as f:
        json.dump(leads, f, ensure_ascii=False, indent=2)

def puanla(lead):
    """Lead'in öncelik puanını hesapla (0-10)."""
    puan = 5  # Temel puan
    web = lead.get("website", "").strip()
    not_str = lead.get("not", "")
    
    # Web sitesi yoksa yüksek öncelik (+3)
    if not web:
        puan += 3
    elif "instagram.com" in web.lower() or not web.startswith("http") and web:
        puan += 2  # Sadece IG varsa +2
    elif web:
        puan += 1  # Web sitesi var ama geliştirilebilir
    
    # Çok yorum varsa önemli işletme
    yorum_sayisi = 0
    puan_str = lead.get("puan", "")
    if "yorum" in puan_str.lower():
        try:
            yorum_sayisi = int(puan_str.split("(")[-1].split(" ")[0])
            if yorum_sayisi > 200:
                puan += 2
            elif yorum_sayisi > 100:
                puan += 1
        except:
            pass
    
    # Mudanya'da ise yüz yüze satış avantajı
    adres = lead.get("adres", "")
    if "mudanya" in adres.lower():
        puan += 2
    # Bursa merkezde ise
    elif "bursa" in adres.lower() or "osmangazi" in adres.lower() or "nilüfer" in adres.lower() or "yıldırım" in adres.lower():
        puan += 1
    
    # Telefon varsa ulaşılabilir
    tel = lead.get("telefon", "")
    if tel:
        puan += 1
    
    # Not'ta fırsat işareti
    if "web sitesi yok" in not_str.lower():
        puan += 2
    if "mudanya" in not_str.lower():
        puan += 1
    
    return min(puan, 10)

def eksik_analizi(lead):
    """Lead'in dijital eksiklerini tespit et."""
    web = lead.get("website", "").strip()
    eksikler = []
    
    if not web:
        eksikler.append("❌ Web sitesi yok — Google'da görünmez, müşteri güveni düşük")
        eksikler.append("❌ Online randevu sistemi yok — 7/24 hizmet veremiyor")
        eksikler.append("❌ Dijital kartvizit yok — WhatsApp'ta profesyonel görünmüyor")
    elif "instagram.com" in web.lower():
        eksikler.append("❌ Sadece Instagram var — kurumsal web sitesi eksik")
        eksikler.append("❌ Google My Business optimize değil")
        eksikler.append("❌ Online randevu sistemi yok")
    else:
        eksikler.append("⚠️ Web sitesi var ama mobil uyum kontrolü gerek")
        eksikler.append("❌ Online randevu sistemi entegre değil")
    
    if "not" in lead.get("not", "").lower():
        if "e-posta" in lead.get("not", "").lower() or "mail" in lead.get("not", "").lower():
            pass  # İletişim kurulmuş
    
    return eksikler

def demo_hazirla(lead):
    """Lead için kişiselleştirilmiş demo metni oluştur."""
    isim = lead.get("isim", "İşletme")
    kisa_isim = isim.split("-")[0].strip() if "-" in isim else isim.split(" ")[0]
    web = lead.get("website", "").strip()
    
    eksikler = eksik_analizi(lead)
    
    # Eksiklere göre kayıp hesapla
    kayiplar = []
    if not web:
        kayiplar.append("💰 Ayda ortalama 20+ potansiyel müşteri rakibinize gidiyor")
        kayiplar.append("⏱️ Telefon trafiğiniz gereksiz yoğun, personel zaman kaybediyor")
    elif "instagram" in web.lower():
        kayiplar.append("💰 Kurumsal web siteniz olmadığı için güven kaybı yaşıyorsunuz")
        kayiplar.append("📉 Rakipleriniz Google'da üst sırada, siz görünmüyorsunuz")
    
    # Demo metni
    demo = f"""
═══════════════════════════════════════
🎯 {isim} — DEMO HAZIR
═══════════════════════════════════════

📊 ANALİZ ÖZETİ
──────────────
Puan: {lead.get('puan', 'Bilinmiyor')}
Web: {"Yok ❌" if not web else (f"Yalnız IG ⚠️" if "instagram" in web.lower() else "Var ✅")}
Telefon: {"Var" if lead.get('telefon') else 'Yok'}
Adres: {lead.get('adres', 'Bilinmiyor')}

🔍 TESPİT EDİLEN EKSİKLER
─────────────────────────
{chr(10).join(eksikler)}

💰 KAYIP HESAPLAMASI
───────────────────
{chr(10).join(kayiplar)}

✅ ERGENEAI ÇÖZÜMÜ
────────────────
➊ Profesyonel web sitesi (AI destekli, mobil uyumlu)
➋ Online randevu sistemi (7/24 otomatik)
➌ WhatsApp işletme hesabı + otomatik mesajlaşma
➍ Google My Business optimizasyonu
➎ Dijital kartvizit + QR menü

📋 GÖRÜŞME STRATEJİSİ
───────────────────
Sıra: {"⚠️ Acil — web sitesi yok" if not web else ("Öncelikli — dijital varlık zayıf" if "instagram" in web.lower() else "Standart — mevcut altyapıyı geliştir")}
Yaklaşım: Yüz yüze (Mudanya/Bursa)
Kanal: Telefonla ön görüşme → yüz yüze demo
Öneri: İlk ay ücretsiz kurulum teklif et

📝 DEMO METNİ
────────────
"Analizlerimiz sonucunda işletmenizin önemli eksiklerini fark ettik.

{chr(10).join(['❌ ' + e.replace('❌ ', '').replace('⚠️ ', '') for e in eksikler[:3]])}

Bu eksikler nedeniyle:
{kayiplar[0] if kayiplar else ''}

Mesela; online randevu sisteminiz olsa, müşterileriniz 7/24 size ulaşabilir, telefon trafiğiniz %60 azalırdı.

Sizin için özel bir demo hazır. İlgilenirseniz çözümümüzü sunmak isteriz."
"""
    return demo

def sirala(leads):
    """Lead'leri önceliğe göre sırala."""
    puanli = [(puanla(l), l) for l in leads]
    puanli.sort(key=lambda x: -x[0])
    return [l for _, l in puanli]

def tumunu_analiz_et():
    """Tüm lead'leri analiz et ve raporla."""
    leads = lead_oku()
    if not leads:
        return
    
    print(f"📊 LEAD ANALİZİ — {len(leads)} lead")
    print("=" * 50)
    
    sirali = sirala(leads)
    for i, l in enumerate(sirali, 1):
        puan = puanla(l)
        durum = l.get("durum", "yeni")
        web = l.get("website", "").strip()
        web_durum = "❌ Yok" if not web else ("⚠️ IG" if "instagram" in web.lower() else "✅ Var")
        
        print(f"\n{i}. [{puan}/10] {l['isim'][:50]}")
        print(f"   Puan: {l.get('puan', '?')} | Web: {web_durum} | Durum: {durum}")
        print(f"   Adres: {l.get('adres', '?')[:50]}")
        print(f"   📞 {l.get('telefon', 'Yok')}")
        
        if puan >= 8:
            print(f"   🔴 YÜKSEK ÖNCELİK — hemen aksiyon")
        elif puan >= 6:
            print(f"   🟡 ORTA ÖNCELİK — sıradaki")
        else:
            print(f"   🟢 DÜŞÜK ÖNCELİK — zamanı gelince")
    
    # İstatistikler
    ort_puan = sum(puanla(l) for l in leads) / len(leads)
    acil = sum(1 for l in leads if puanla(l) >= 8)
    print(f"\n{'=' * 50}")
    print(f"📈 ÖZET: {len(leads)} lead | Ortalama puan: {ort_puan:.1f}/10 | Acil: {acil} adet")
    return sirali

def tek_demo(isim):
    """Tek bir lead için demo hazırla."""
    leads = lead_oku()
    for l in leads:
        if isim.lower() in l["isim"].lower():
            print(demo_hazirla(l))
            return
    print(f"❌ '{isim}' bulunamadı")
    print(f"Mevcut lead'ler:")
    for l in leads:
        print(f"  - {l['isim']}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--demo":
            isim = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
            tek_demo(isim)
        elif sys.argv[1] == "--sirala":
            sirali = tumunu_analiz_et()
        else:
            print("Kullanım: lead-stratejisti.py [--demo 'isim' | --sirala]")
    else:
        tumunu_analiz_et()
