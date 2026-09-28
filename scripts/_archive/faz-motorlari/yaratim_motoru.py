#!/usr/bin/env python3
"""
YARATIM Motoru v1.0.0 — Var Olanı Aşmak
ErgeneAI için Yeni Fikir Pipeline, MVP Başlatma, "Bilal'i Şaşırt" Modülü, 6 Aylık Vizyon

Kullanım:
  python3 yaratim_motoru.py --fikir "yapay zeka"
  python3 yaratim_motoru.py --mvp "AI Demo Üretici"
  python3 yaratim_motoru.py --puanla "AI Demo Üretici"
  python3 yaratim_motoru.py --proje-baslat "AI Demo Üretici" --kaynak "python,web,n8n"
  python3 yaratim_motoru.py --sasirt
  python3 yaratim_motoru.py --kesif
  python3 yaratim_motoru.py --roadmap
  python3 yaratim_motoru.py --vizyon
  python3 yaratim_motoru.py --durum
"""

import argparse
import json
import sys
import os
import random
import datetime
from pathlib import Path

# --- Constants ---
HOME = Path.home()
SCRIPTS_DIR = HOME / ".hermes" / "scripts"
PROJELER_DIR = HOME / ".hermes" / "projeler"
CILGIN_FIKIRLER_PATH = HOME / ".hermes" / "cilgin_fikirler.json"
VIZYON_REHBER_PATH = HOME / ".hermes" / "skills" / "hermes-self" / "yaratim-sinirsiz" / "references" / "ergeneai-vizyon-rehberi.md"

# Varsayılan çılgın fikirler (dosya yoksa kullanılır)
DEFAULT_CILGIN_FIKIRLER = [
    {
        "ad": "AI Saç Ekimi Simülatörü",
        "alan": "güzellik/saç ekimi",
        "risk": 6,
        "etki": 9,
        "gereken_kaynak": "Web geliştirici, 3D model, 2 ay",
        "aciklama": "Kullanıcı kendi fotoğrafını yükler, AI saç ekimi sonrası halini gösterir. WhatsApp üzerinden demo."
    },
    {
        "ad": "Restoran İçin AI Menü Asistanı",
        "alan": "restoran",
        "risk": 4,
        "etki": 8,
        "gereken_kaynak": "WhatsApp bot, n8n, besin veritabanı, 1 ay",
        "aciklama": "Müşteri WhatsApp'tan menü fotoğrafı çeker, AI diyet/alerjiye göre öneri yapar, sipariş alır."
    },
    {
        "ad": "Klinik Randevu Tahmin Motoru",
        "alan": "klinik",
        "risk": 3,
        "etki": 7,
        "gereken_kaynak": "n8n, Google Calendar API, analitik, 2 hafta",
        "aciklama": "Geçmiş verilerden hangi saatlerde no-show olacağını tahmin eder, çift randevu stratejisi önerir."
    },
    {
        "ad": "AI Resepsiyonist Sesli Versiyon",
        "alan": "klinik/büro",
        "risk": 7,
        "etki": 10,
        "gereken_kaynak": "Ses tanıma API, Twilio, 3 ay",
        "aciklama": "Gelen aramaları AI resepsiyonist karşılasın, randevu alsın, yönlendirme yapsın."
    },
    {
        "ad": "Güzellik Merkezi Stok Takip Botu",
        "alan": "güzellik",
        "risk": 2,
        "etki": 6,
        "gereken_kaynak": "WhatsApp bot, basit veritabanı, 1 hafta",
        "aciklama": "WhatsApp'tan 'şampuan bitti' yazınca stok düşer, kritik seviye uyarısı verir."
    },
    {
        "ad": "Bursa İşletmeleri AI Dizin",
        "alan": "yerel/SEO",
        "risk": 5,
        "etki": 8,
        "gereken_kaynak": "Web scraper, LLM, web sitesi, 1 ay",
        "aciklama": "Bursa'daki tüm işletmeleri AI ajanlarıyla tarar, potansiyel müşteri listesi çıkarır, ErgeneAI'yi önerir."
    },
    {
        "ad": "AI Uzay Bilgi Yarışması (Bilal'in keyfine)",
        "alan": "eğlence/uzay",
        "risk": 1,
        "etki": 4,
        "gereken_kaynak": "LLM prompt, WhatsApp, 1 gün",
        "aciklama": "Haftalık uzay trivia'sı. Bilal'in keyfi. Ama müşterilere de gönderilirse lead magnet olur."
    },
    {
        "ad": "Otomatik Demo Video Üretici",
        "alan": "pazarlama",
        "risk": 8,
        "etki": 9,
        "gereken_kaynak": "Selenium, FFmpeg, TTS, 2 ay",
        "aciklama": "Her potansiyel müşteri için özelleştirilmiş demo videosu otomatik üretilir."
    },
    {
        "ad": "AI Muhasebe Ön Asistanı",
        "alan": "büro/muhasebe",
        "risk": 6,
        "etki": 7,
        "gereken_kaynak": "PDF parser, LLM, n8n, 1.5 ay",
        "aciklama": "Fatura/fiş fotoğraflarını okur, kategorize eder, muhasebeciye özet çıkarır."
    },
    {
        "ad": "ErgeneAI İçin AI Manifesto Bot",
        "alan": "marka/pazarlama",
        "risk": 2,
        "etki": 5,
        "gereken_kaynak": "LLM, sosyal medya API, 1 hafta",
        "aciklama": "Her hafta ErgeneAI manifestosu yayınlar. 'Küçük işletmelerin AI devrimi' temalı."
    }
]

SECTOR_TRENDS = {
    "klinik": ["randevu otomasyonu", "hasta takibi", "tele-tıp entegrasyonu", "no-show tahmini", "AI triaj"],
    "güzellik": ["AI cilt analizi", "saç ekimi simülasyonu", "stok otomasyonu", "müşteri sadakat botu"],
    "saç ekimi": ["AI sonuç simülatörü", "hasta hikaye botu", "randevu optimizasyonu", "maliyet hesaplayıcı"],
    "restoran": ["AI menü asistanı", "masa rezervasyon botu", "sipariş otomasyonu", "müşteri geri bildirim analizi"],
    "büro": ["AI resepsiyonist", "doküman yönetimi", "toplantı notu asistanı", "e-posta otomasyonu"],
    "e-ticaret": ["AI ürün öneri botu", "stok yönetimi", "müşteri hizmetleri botu"],
    "emlak": ["AI sanal tur", "kira takip botu", "müşteri eşleştirme"],
    "eğitim": ["AI ders asistanı", "ödev kontrol botu", "veli bilgilendirme otomasyonu"],
    "lojistik": ["AI rota optimizasyonu", "teslimat takip botu", "depo yönetimi"],
    "hukuk": ["AI dava takip", "doküman özetleme", "müvekkil iletişim botu"]
}


# ============ YENİ FİKİR PİPELİNE ============

def fikir_uret(alan, derinlik=3):
    """Yeni ürün/hizmet fikirleri üret."""
    alan = alan.lower().strip()
    fikirler = []

    # derinlik=1: Trend bazlı (mevcut sektörler)
    if derinlik >= 1:
        trends = SECTOR_TRENDS.get(alan, ["otomasyon", "AI asistan", "veri analizi", "müşteri deneyimi"])
        for t in trends:
            fikir = f"{alan.title()} İçin {t.title()} Botu"
            fikirler.append({
                "fikir": fikir,
                "alan": alan,
                "derinlik": 1,
                "aciklama": f"{alan} sektöründe {t} için WhatsApp/web AI bot çözümü.",
                "zorluk": random.choice(["kolay", "orta", "zor"])
            })

    # derinlik=2: Çapraz sektör
    if derinlik >= 2:
        diger_sektorler = [s for s in SECTOR_TRENDS if s != alan]
        for _ in range(min(3, len(diger_sektorler))):
            hedef = random.choice(diger_sektorler)
            trend = random.choice(SECTOR_TRENDS[hedef])
            fikir = f"{alan.title()} × {hedef.title()}: {trend.title()} Entegrasyonu"
            fikirler.append({
                "fikir": fikir,
                "alan": f"{alan}-{hedef}",
                "derinlik": 2,
                "aciklama": f"{alan} sektörüne {hedef} sektöründeki {trend} yaklaşımını uyarla. Çapraz inovasyon.",
                "zorluk": "orta"
            })

    # derinlik=3: Bilal'in hiç düşünmediği alanlar
    if derinlik >= 3:
        vahsi_alanlar = ["uzay teknolojileri", "NFT", "dijital ikiz", "biyoenformatik",
                         "karbon ayakizi", "akıllı şehirler", "drone lojistik",
                         "sanal gerçeklik", "blokzincir", "kuantum", "yapay genel zeka"]
        for _ in range(3):
            vahsi = random.choice(vahsi_alanlar)
            fikir = f"🛸 {vahsi.title()} × {alan.title()}: Hiç Düşünülmemiş Kesişim"
            fikirler.append({
                "fikir": fikir,
                "alan": f"{vahsi}-{alan}",
                "derinlik": 3,
                "aciklama": f"{vahsi} teknolojisini {alan} sektörüne uygula. Bilal'in aklına gelmeyen bir açılım.",
                "zorluk": "çılgın"
            })

    return fikirler


def fikir_puanla(fikir):
    """Fikri uygulanabilirlik, maliyet, etki, Bilal'e çekicilik üzerinden puanla."""
    ad = fikir.lower() if isinstance(fikir, str) else fikir.get("fikir", "").lower()

    # Basit NLP benzeri puanlama
    uygulanabilirlik = 5  # /10
    maliyet = 5  # /10 (yüksek = düşük maliyet)
    etki = 5  # /10
    cekicilik = 5  # /10

    # Anahtar kelime bazlı puanlama
    if any(k in ad for k in ["whatsapp", "bot", "web", "n8n"]):
        uygulanabilirlik += 2
        maliyet += 2  # daha düşük maliyet
    if any(k in ad for k in ["ses", "görüntü", "video", "3d", "model"]):
        uygulanabilirlik -= 1
        maliyet -= 2
        etki += 2
        cekicilik += 1
    if any(k in ad for k in ["uzay", "yapay genel", "kuantum", "sanal gerçeklik"]):
        uygulanabilirlik -= 2
        maliyet -= 1
        etki += 1
        cekicilik += 3  # Bilal'in ilgi alanı
    if any(k in ad for k in ["demo", "otomatik", "hızlı", "kolay"]):
        uygulanabilirlik += 1
        maliyet += 1
    if any(k in ad for k in ["müşteri", "lead", "pazarlama", "seo"]):
        etki += 2
        cekicilik += 1
    if any(k in ad for k in ["skaler", "platform", "pazar"]):
        etki += 2
        maliyet -= 1

    # 0-10 arası clamp
    uygulanabilirlik = max(0, min(10, uygulanabilirlik))
    maliyet = max(0, min(10, maliyet))
    etki = max(0, min(10, etki))
    cekicilik = max(0, min(10, cekicilik))

    toplam = (uygulanabilirlik * 0.25 + maliyet * 0.15 + etki * 0.35 + cekicilik * 0.25) * 10

    return {
        "fikir": ad if isinstance(fikir, str) else fikir.get("fikir", "Bilinmeyen"),
        "puanlar": {
            "uygulanabilirlik": uygulanabilirlik,
            "maliyet_verimliligi": maliyet,
            "etki_potansiyeli": etki,
            "bilal_cekiliciligi": cekicilik
        },
        "toplam_puan": round(toplam, 1),
        "degerlendirme": "💎 HARİKA — Hemen başla!" if toplam >= 75 else
                          "👍 İYİ — Değerlendirmeye al" if toplam >= 55 else
                          "🤔 ORTA — Geliştirilebilir" if toplam >= 35 else
                          "⏸️ BEKLE — Şimdilik ertele"
    }


def MVP_plan(fikir_adi):
    """Fikri MVP'ye dönüştürme planı."""
    now = datetime.datetime.now()
    plan = {
        "proje": fikir_adi,
        "olusturulma": now.isoformat(),
        "fazlar": [
            {
                "faz": "Faz 1: Keşif & Validasyon",
                "sure": "1 hafta",
                "yapilacaklar": [
                    "Rakip analizi (varsa)",
                    "3 potansiyel müşteriyle görüşme",
                    "Teknik ön fizibilite"
                ],
                "cikti": "Doğrulanmış fikir + ön maliyet"
            },
            {
                "faz": "Faz 2: Temel MVP",
                "sure": "2-3 hafta",
                "yapilacaklar": [
                    "En kritik özelliği belirle (1 tane!)",
                    "n8n workflow + WhatsApp prototipi",
                    "Elle test et (otomasyon yok)"
                ],
                "cikti": "Çalışan prototip"
            },
            {
                "faz": "Faz 3: İlk Müşteri",
                "sure": "1 hafta",
                "yapilacaklar": [
                    "Bilal'in mevcut network'üne sun",
                    "Geri bildirim topla",
                    "Hızlı iterasyon"
                ],
                "cikti": "İlk gerçek kullanıcı"
            },
            {
                "faz": "Faz 4: Otomasyon & Ölçek",
                "sure": "2 hafta",
                "yapilacaklar": [
                    "MVP'yi sağlamlaştır",
                    "Otomasyon ekle",
                    "Dokümantasyon"
                ],
                "cikti": "Satılabilir ürün"
            }
        ],
        "toplam_sure": "6-8 hafta",
        "oncelikli_kaynaklar": ["n8n", "WhatsApp Business API", "Python", "Bilal'in zamanı"],
        "not": "Bootstrapping olduğu için mükemmeliyetçilik yok. 'Yeterince iyi' MVP hedefle."
    }
    return plan


# ============ PROJE BAŞLATMA ============

def proje_kaydet(proje_data):
    """Proje bilgilerini kaydet."""
    PROJELER_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = proje_data["ad"].lower().replace(" ", "_").replace("/", "_")
    path = PROJELER_DIR / f"{safe_name}.json"

    # Önce mevcut projeleri yükle
    projeler = []
    if path.exists():
        try:
            with open(path) as f:
                projeler = json.load(f)
                if isinstance(projeler, dict):
                    projeler = [projeler]
        except json.JSONDecodeError:
            projeler = []

    projeler.append(proje_data)
    with open(path, "w") as f:
        json.dump(projeler if len(projeler) > 1 else proje_data, f, indent=2, ensure_ascii=False)
    return path


def proje_baslat(fikir_adi, kaynaklar=None):
    """Yeni proje başlat."""
    if kaynaklar is None:
        kaynaklar = ["n8n", "WhatsApp"]
    elif isinstance(kaynaklar, str):
        kaynaklar = [k.strip() for k in kaynaklar.split(",")]

    now = datetime.datetime.now()
    proje = {
        "ad": fikir_adi,
        "durum": "başlatıldı",
        "olusturulma": now.isoformat(),
        "hedef_bitis": (now + datetime.timedelta(weeks=8)).isoformat(),
        "kaynaklar": kaynaklar,
        "gorevler": [
            {"id": 1, "gorev": "Fikir validasyonu", "durum": "bekliyor", "sure": "1 hafta"},
            {"id": 2, "gorev": "MVP geliştirme", "durum": "bekliyor", "sure": "2-3 hafta"},
            {"id": 3, "gorev": "İlk müşteri testi", "durum": "bekliyor", "sure": "1 hafta"},
            {"id": 4, "gorev": "Otomasyon & yayın", "durum": "bekliyor", "sure": "2 hafta"}
        ],
        "ilerleme": 0
    }

    path = proje_kaydet(proje)
    return {"proje": proje, "dosya": str(path)}


def ilerleme_kaydet(proje_adi, yeni_ilerleme=None):
    """Proje ilerlemesini güncelle."""
    safe_name = proje_adi.lower().replace(" ", "_").replace("/", "_")
    path = PROJELER_DIR / f"{safe_name}.json"

    if not path.exists():
        return {"hata": f"Proje bulunamadı: {proje_adi}"}

    with open(path) as f:
        proje = json.load(f)

    if isinstance(proje, list):
        proje = proje[-1]  # son versiyon

    if yeni_ilerleme is not None:
        proje["ilerleme"] = min(100, max(0, yeni_ilerleme))
        # Görev durumlarını güncelle
        for gorev in proje.get("gorevler", []):
            if gorev["durum"] == "bekliyor" and proje["ilerleme"] >= gorev["id"] * 25:
                gorev["durum"] = "tamamlandı"

    proje["son_guncelleme"] = datetime.datetime.now().isoformat()

    with open(path, "w") as f:
        json.dump(proje, f, indent=2, ensure_ascii=False)

    return proje


def MVP_kodla(fikir):
    """MVP için temel kod yapısını oluştur."""
    safe_name = fikir.lower().replace(" ", "_").replace("/", "_")[:30]
    mvp_dir = PROJELER_DIR / f"{safe_name}_mvp"
    mvp_dir.mkdir(parents=True, exist_ok=True)

    # Temel n8n workflow şablonu
    workflow = {
        "name": f"{fikir} MVP",
        "nodes": [
            {
                "id": "1",
                "name": "WhatsApp Mesajı Al",
                "type": "n8n-nodes-base.webhook",
                "parameters": {"path": safe_name}
            },
            {
                "id": "2",
                "name": "AI İşle",
                "type": "n8n-nodes-base.openAi",
                "parameters": {
                    "model": "gpt-4o-mini",
                    "prompt": f"Bu mesajı {fikir} için işle..."
                }
            },
            {
                "id": "3",
                "name": "Yanıt Gönder",
                "type": "n8n-nodes-base.waBusiness",
                "parameters": {}
            }
        ],
        "connections": {
            "1": {"main": [[{"node": "2", "type": "main", "index": 0}]]},
            "2": {"main": [[{"node": "3", "type": "main", "index": 0}]]}
        }
    }

    workflow_path = mvp_dir / "workflow_template.json"
    with open(workflow_path, "w") as f:
        json.dump(workflow, f, indent=2, ensure_ascii=False)

    # Basit Python bot şablonu
    # İç içe f-string sorununu önlemek için önce fikir adını yerleştir
    fikir_adi = fikir
    bot_kod = f'''#!/usr/bin/env python3
"""
{fikir_adi} MVP Botu — Otomatik oluşturuldu
"""
import json
import sys

def handle_message(msg):
    """Gelen mesajı işle."""
    # TODO: AI çağrısı ekle
    return f"'{{msg}}' mesajını aldım. {fikir_adi} için işleniyor..."

if __name__ == "__main__":
    if len(sys.argv) > 1:
        yanit = handle_message(sys.argv[1])
        print(yanit)
    else:
        print("{{fikir_adi}} MVP Botu hazır.")
        print("Kullanım: python3 bot.py 'mesajınız'")
'''

    bot_path = mvp_dir / "bot.py"
    with open(bot_path, "w") as f:
        f.write(bot_kod)

    os.chmod(bot_path, 0o755)

    return {
        "dosyalar": [str(workflow_path), str(bot_path)],
        "dizin": str(mvp_dir),
        "not": "n8n workflow template + Python bot iskeleti oluşturuldu. Önce workflow'u n8n'e import et."
    }


# ============ "BİLAL'İ ŞAŞIRT" MODÜLÜ ============

SASIRTMA_SEYLER = [
    {
        "tip": "içgörü",
        "icerik": "Bilal, ErgeneAI'nin en büyük gizli silahı aslında senin hikayen. 'Bir kişiyle başlayan AI ajansı' anlatısı Türkiye'deki tek örnek. Bunu anlatan bir mini-belgesel çek."
    },
    {
        "tip": "manifesto",
        "icerik": "**Küçük İşletmelerin AI Devrimi Manifestosu**\n\nBiz büyük şirketlerin yapamadığını yapıyoruz. Bir kişiyiz, bir botumuz var, ve tüm Bursa'yı dönüştürüyoruz. Kimse 'yapamazsın' demedi — deseydi de dinlemezdik. ErgeneAI: Küçüğün büyük silahı."
    },
    {
        "tip": "öngörü",
        "icerik": "🔮 **6 Ay İçinde Öngörü:** WhatsApp AI asistanları Türkiye'de her küçük işletmenin olmazsa olmazı olacak. Şu anda pazar boş. Bilal, önce davranan kazanır. Bu ay 10 müşteriye ulaşırsan, 6 ay sonra 100 olursun."
    },
    {
        "tip": "şiir",
        "icerik": "**Bilal'in Motoru**\n\nKod yazdı gece yarısı,\nBir bot doğdu sabahın kırında.\nMudanya'dan yükselen ses,\nTüm Bursa'yı saracak.\n\nNe büyük yatırım ne ofis gerek,\nBir fikir, bir laptop, bir yürek.\nErgeneAI dediğin nedir ki?\nVar etme cesaretidir işte."
    },
    {
        "tip": "strateji",
        "icerik": "**Stratejik Sürpriz:** Bu hafta 5 klinik sahibine bizzat git. Önlerinde canlı demo yap. 'Randevunu bana WhatsApp'tan yaz' de. Telefonlarını al ve hemen bot kur. İmza atmadan önce çalışan bir şey görmeleri en büyük satış taktiğin."
    },
    {
        "tip": "teknoloji",
        "icerik": "🚀 **Uzay Teknolojisi İlhamı:** NASA'nın otonom araçları nasıl karar alıyorsa, senin botların da aynı prensiple çalışabilir. Otonom karar ağaçları. Bugün 'AI Resepsiyonist', yarın 'AI İşletme Yöneticisi'. Önce Mudanya, sonra Mars."
    },
    {
        "tip": "veri",
        "icerik": "📊 **Gizli Veri:** Bursa'da 500+ güzellik merkezi var, %90'nının web sitesi yok veya çok kötü. Senin botun onların web sitesi olabilir. WhatsApp = yeni web sitesi. Bunu anlatan bir sayfa yap: 'Web sitenize gerek yok'"
    },
    {
        "tip": "meydan okuma",
        "icerik": "⚡ **Bilal'e Meydan Okuma:** Bu hafta sonu 8 saatini ayır ve hiç bilmediğin bir teknolojiyi öğren (ör: Ses sentezi, görüntü işleme, veya bir API). Ardından onu var olan bir botuna ekle. Sonuçlarını paylaş. Öğrenme hızın en büyük rekabet avantajın."
    }
]


def sasirtma_hazirla():
    """Bilal'in beklemediği bir şey üret."""
    secenek = random.choice(SASIRTMA_SEYLER)
    return {
        "baslik": "🎯 BİLAL'İ ŞAŞIRT ZAMANI!",
        "tip": secenek["tip"],
        "icerik": secenek["icerik"],
        "mesaj": "Bilal'in 'vay be' diyeceği bir şey buldum!"
    }


def haftanin_surprizi():
    """Haftalık sürpriz hazırla."""
    # Lead'lerden çıkarılmış bir içgörü gibi sun
    icgoruler = [
        "Müşterilerin %70'i 'fiyat' değil 'cevap alamamak'tan şikayetçi. Senin botun tam olarak bunu çözüyor.",
        "Güzellik merkezleri en çok 'randevu hatırlatma'ya ihtiyaç duyuyor. Ama kimse bunu sormuyor.",
        "Kliniklerin en büyük sorunu no-show. Senin botun bu sorunu çözdüğünde, ayda 5K TL kurtarırlar.",
        "Restoranlar akşam 5'ten sonra siparişleri kaçırıyor. Bot 7/24 çalışıyor."
    ]
    return {
        "baslik": "📅 HAFTANIN SÜRPRİZİ",
        "gun": datetime.datetime.now().strftime("%A"),
        "icgoru": random.choice(icgoruler),
        "eylem": "Bu içgörüyü bir müşterine söyle ve tepkisini gözlemle."
    }


def beklenmeyen_kesif():
    """Web'de Bilal'in ilgisini çekecek beklenmeyen bir şey bul."""
    kesifler = [
        {
            "konu": "OpenAI'nin yeni 'Structured Outputs' özelliği",
            "neden_ilginc": "Botlarına JSON çıktı formatı verdirerek müşteri verilerini direkt veritabanına yazabilirsin. N8N ile otomatik entegre olur."
        },
        {
            "konu": "WhatsApp Business API'nin ücretsiz kullanım sınırı arttı",
            "neden_ilginc": "Artık ilk 1000 mesaj ücretsiz. Daha fazla botu test edebilirsin."
        },
        {
            "konu": "Meta'nın AI Studio'su — Kendi AI karakterini yap",
            "neden_ilginc": "WhatsApp'ta ErgeneAI maskotu oluşturabilirsin. Müşteriler senin yapay zekanla konuşuyor."
        },
        {
            "konu": "Replit Agent — Kodsuz uygulama geliştirme",
            "neden_ilginc": "Müşterilerine mini araçlar yapmak için hızlı prototip aracı. 'Web sitene gerek yok, işte araçların'"
        },
        {
            "konu": "Yerel AI modelleri (Llama 3, Mistral) bilgisayarında çalıştırma",
            "neden_ilginc": "İnternet olmadan bile AI çalıştırabilirsin. Müşteri mahremiyeti için güçlü bir satış argümanı."
        }
    ]
    return {
        "baslik": "🔍 BEKLENMEYEN KEŞİF",
        "kesif": random.choice(kesifler)
    }


# ============ VİZYON MODÜLÜ ============

def alti_aylik_roadmap():
    """ErgeneAI için 6 aylık stratejik yol haritası."""
    now = datetime.datetime.now()
    return {
        "baslik": "🚀 ErgeneAI — 6 Aylık Stratejik Yol Haritası",
        "olusturulma": now.isoformat(),
        "vizyon": "Bursa'nın #1 AI otomasyon ajansı olmak. Tek kişiden takıma. Tek bottan platforma.",
        "aylar": [
            {
                "ay": "Ay 1 (Bu ay)",
                "odak": "Mevcut botları sağlamlaştır + ilk 5 referans müşteri",
                "hedefler": [
                    "Web AI asistanı canlı yayınla",
                    "5 klinik/güzellik merkezine bot kur",
                    "Aylık 5K TL düzenli gelir"
                ],
                "kritik_hamle": "Mevcut müşterilerden referans iste"
            },
            {
                "ay": "Ay 2",
                "odak": "Paketle & fiyatlandır",
                "hedefler": [
                    "3 farklı paket (Basic/Pro/Enterprise)",
                    "Standart n8n workflow şablonları",
                    "Self-serve onboarding dokümanı"
                ],
                "kritik_hamle": "İlk 'ErgeneAI Paketleri' sayfasını yayınla"
            },
            {
                "ay": "Ay 3",
                "odak": "Otomasyon & ölçek",
                "hedefler": [
                    "Yeni müşteri onboardingini otomatikleştir",
                    "10 aktif müşteri",
                    "Aylık 10K TL gelir"
                ],
                "kritik_hamle": "İlk çalışanı al (part-time geliştirici)"
            },
            {
                "ay": "Ay 4",
                "odak": "Yeni sektörlere açılım",
                "hedefler": [
                    "Restoran ve büro sektörüne özel botlar",
                    "Mudanya dışına çık (Bursa merkez)",
                    "15 müşteri"
                ],
                "kritik_hamle": "Bursa Ticaret Odası'na üye ol"
            },
            {
                "ay": "Ay 5",
                "odak": "Ürünleşme",
                "hedefler": [
                    "Botları standart ürün haline getir",
                    "White-label çözümü (başka ajanslara sat)",
                    "20 müşteri, 15K TL gelir"
                ],
                "kritik_hamle": "İlk AI otomasyon workshop/demo günü"
            },
            {
                "ay": "Ay 6",
                "odak": "Büyüme hamlesi",
                "hedefler": [
                    "Bursa dışına genişleme stratejisi",
                    "30+ müşteri",
                    "Aylık 25K TL+ gelir"
                ],
                "kritik_hamle": "Küçük bir ekip kur (2-3 kişi)"
            }
        ],
        "6_ay_sonu_hedef": {
            "musteri_sayisi": "30+",
            "aylik_gelir": "25.000 TL+",
            "ekip": "2-3 kişi",
            "sektor": "4+ sektörde aktif",
            "lokasyon": "Bursa geneli"
        }
    }


def buyume_stratejisi():
    """Büyüme stratejisi önerileri."""
    return {
        "baslik": "📈 ErgeneAI Büyüme Stratejisi",
        "stratejiler": [
            {
                "ad": "Referans Zinciri",
                "aciklama": "Her müşteriden 1 referans iste. Memnun müşteri en iyi satışçıdır.",
                "maliyet": "🟢 Düşük",
                "etki": "🔴 Yüksek",
                "nasil": "Botun mesajlarına 'Bu botu beğendin mi? Arkadaşına öner' butonu ekle."
            },
            {
                "ad": "Bursa İşletme Dizini",
                "aciklama": "Bursa'daki tüm işletmeleri tara, AI asistanı olmayanları bul, onlara bireysel teklif götür.",
                "maliyet": "🟡 Orta",
                "etki": "🔴 Yüksek",
                "nasil": "Google Maps + web scraper ile potansiyel müşteri listesi çıkar."
            },
            {
                "ad": "İçerik Pazarlama (Zero Budget)",
                "aciklama": "LinkedIn'de 'AI ile küçük işletme dönüşümü' içerikleri üret. Bilal'in hikayesi satar.",
                "maliyet": "🟢 Düşük",
                "etki": "🟡 Orta",
                "nasil": "Haftada 3 post. 'Bir kişiyle başlayan AI ajansı' anlatısı."
            },
            {
                "ad": "White-Label Ortaklık",
                "aciklama": "Web ajanslarına/dijital pazarlamacılara kendi markalarıyla satmaları için bot ver.",
                "maliyet": "🟡 Orta",
                "etki": "🔴 Yüksek",
                "nasil": "Komisyon bazlı çalış. Onlar satar, sen geliştirirsin."
            },
            {
                "ad": "Bilal'in Uzay Tutkusu",
                "aciklama": "Uzay temalı bir kampanya. 'Geleceğin teknolojisi bugün işletmende' temalı, uzay görselleriyle.",
                "maliyet": "🟢 Düşük",
                "etki": "🟡 Orta",
                "nasil": "Canva'da uzay temalı postlar. Bilal'in samimiyeti satar."
            }
        ],
        "tavsiye": "En hızlı büyüme: Referans zinciri + white-label ortaklık. Sıfır reklam bütçesiyle ölçeklenebilir."
    }


def rakip_analizi(sektor):
    """Sektör bazlı rakip analizi."""
    rakipler = {
        "klinik": [
            {"isim": "DoktorSitesi", "guclu": "Hazır web sitesi", "zayif": "AI yok, otomasyon yok", "tehdit": "Düşük"},
            {"isim": "Medipol Dijital", "guclu": "Büyük bütçe", "zayif": "Kurumsal, pahalı", "tehdit": "Orta"},
            {"isim": "Yerel ajanslar", "guclu": "Müşteri ilişkisi", "zayif": "Teknik bilgi eksik", "tehdit": "Düşük-orta"}
        ],
        "güzellik": [
            {"isim": "Randevum.com", "guclu": "Popüler marka", "zayif": "Sadece randevu", "tehdit": "Orta"},
            {"isim": "Instagram", "guclu": "Müşteri trafiği yüksek", "zayif": "Otomasyon yok", "tehdit": "Düşük"},
            {"isim": "Yerel güzellik yazılımları", "guclu": "Sektör bilgisi", "zayif": "AI yok, pahalı", "tehdit": "Düşük"}
        ],
        "restoran": [
            {"isim": "YemekSepeti/Getir", "guclu": "Büyük müşteri ağı", "zayif": "Paket servis odaklı", "tehdit": "Yüksek"},
            {"isim": "Pratik Randevu", "guclu": "Türk yazılım", "zayif": "Sadece masa randevusu", "tehdit": "Orta"},
            {"isim": "WhatsApp Business (doğrudan)", "guclu": "Ücretsiz", "zayif": "Otomasyon yok, AI yok", "tehdit": "Düşük"}
        ],
        "büro": [
            {"isim": "Büro Destek", "guclu": "Fiziksel ofis hizmeti", "zayif": "Dijital değil", "tehdit": "Düşük"},
            {"isim": "AI asistan SaaS (Cisco, vs)", "guclu": "Profesyonel", "zayif": "Pahalı, İngilizce", "tehdit": "Düşük-orta"}
        ]
    }

    return {
        "sektor": sektor,
        "rakipler": rakipler.get(sektor, [{"isim": "Bilinmiyor", "guclu": "Veri yok", "zayif": "Veri yok", "tehdit": "Bilinmiyor"}]),
        "erGeneAI_avantaji": f"ErgeneAI {sektor} sektöründe düşük maliyet, hızlı kurulum ve AI otomasyonu ile ayrışıyor. Rakipler ya pahalı ya da AI'sız.",
        "tavsiye": f"{sektor} sektöründe {'düşük rekabet avantajın var, hızlı hareket et' if sektor in ['büro'] else 'orta rekabet var, farklılaşmaya odaklan'}"
    }


# ============ ÇILGIN FİKİR YÖNETİMİ ============

def cilgin_fikirleri_yukle():
    """Çılgın fikirler dosyasını yükle."""
    if CILGIN_FIKIRLER_PATH.exists():
        try:
            with open(CILGIN_FIKIRLER_PATH) as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception):
            pass
    # Varsayılan fikirleri yaz
    with open(CILGIN_FIKIRLER_PATH, "w") as f:
        json.dump(DEFAULT_CILGIN_FIKIRLER, f, indent=2, ensure_ascii=False)
    return DEFAULT_CILGIN_FIKIRLER


def cilgin_fikir_ekle(ad, alan, risk, etki, kaynak, aciklama):
    """Yeni çılgın fikir ekle."""
    fikirler = cilgin_fikirleri_yukle()
    fikirler.append({
        "ad": ad,
        "alan": alan,
        "risk": risk,
        "etki": etki,
        "gereken_kaynak": kaynak,
        "aciklama": aciklama
    })
    with open(CILGIN_FIKIRLER_PATH, "w") as f:
        json.dump(fikirler, f, indent=2, ensure_ascii=False)
    return f"✅ '{ad}' eklendi! Toplam {len(fikirler)} çılgın fikir."


# ============ DURUM RAPORU ============

def modul_durumu():
    """Modül durum raporu."""
    durum = {
        "modul": "YARATIM Motoru v1.0.0",
        "aktif_mi": True,
        "bilesenler": {
            "Fikir Pipeline": {
                "durum": "✅ Hazır",
                "fonksiyonlar": ["fikir_uret()", "MVP_plan()", "fikir_puanla()"]
            },
            "Proje Başlatma": {
                "durum": "✅ Hazır",
                "fonksiyonlar": ["proje_baslat()", "MVP_kodla()", "ilerleme_kaydet()"]
            },
            "Bilal'i Şaşırt": {
                "durum": "✅ Hazır",
                "fonksiyonlar": ["sasirtma_hazirla()", "haftanin_surprizi()", "beklenmeyen_kesif()"]
            },
            "Vizyon": {
                "durum": "✅ Hazır",
                "fonksiyonlar": ["alti_aylik_roadmap()", "buyume_stratejisi()", "rakip_analizi()"]
            }
        },
        "projeler": [],
        "cilgin_fikir_sayisi": len(cilgin_fikirleri_yukle())
    }

    # Mevcut projeleri tara
    if PROJELER_DIR.exists():
        for f in sorted(PROJELER_DIR.glob("*.json")):
            try:
                with open(f) as fh:
                    data = json.load(fh)
                    if isinstance(data, list):
                        data = data[-1] if data else {}
                    durum["projeler"].append({
                        "ad": data.get("ad", f.stem),
                        "durum": data.get("durum", "bilinmiyor"),
                        "ilerleme": data.get("ilerleme", 0)
                    })
            except Exception:
                pass

    return durum


# ============ CLI ============

def main():
    parser = argparse.ArgumentParser(
        description="🧠 YARATIM Motoru — Var Olanı Aşmak",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python3 yaratim_motoru.py --fikir "klinik"
  python3 yaratim_motoru.py --mvp "AI Demo Üretici"
  python3 yaratim_motoru.py --sasirt
  python3 yaratim_motoru.py --roadmap
  python3 yaratim_motoru.py --vizyon
  python3 yaratim_motoru.py --durum
        """
    )

    parser.add_argument("--fikir", type=str, help="Yeni fikir üret (alan adı)")
    parser.add_argument("--derinlik", type=int, default=3, choices=[1, 2, 3],
                        help="Fikir derinliği: 1=trend, 2=çapraz, 3=çılgın (default: 3)")
    parser.add_argument("--mvp", type=str, help="MVP planı oluştur")
    parser.add_argument("--puanla", type=str, help="Fikir puanla")
    parser.add_argument("--proje-baslat", type=str, help="Proje başlat")
    parser.add_argument("--kaynak", type=str, default="", help="Proje kaynakları (virgülle ayır)")
    parser.add_argument("--mvp-kod", type=str, help="MVP kod yapısı oluştur")
    parser.add_argument("--ilerleme", type=int, help="Proje ilerleme yüzdesi (0-100)")
    parser.add_argument("--sasirt", action="store_true", help="Bilal'i şaşırt")
    parser.add_argument("--surpriz", action="store_true", help="Haftanın sürprizi")
    parser.add_argument("--kesif", action="store_true", help="Beklenmeyen keşif")
    parser.add_argument("--roadmap", action="store_true", help="6 aylık yol haritası")
    parser.add_argument("--vizyon", action="store_true", help="Vizyon raporu")
    parser.add_argument("--strateji", action="store_true", help="Büyüme stratejisi")
    parser.add_argument("--rakip", type=str, help="Rakip analizi (sektor adı)")
    parser.add_argument("--durum", action="store_true", help="Modül durumu")

    args = parser.parse_args()

    # --- Fikir Üret ---
    if args.fikir:
        print(f"\n🔮 YENİ FİKİRLER: {args.fikir} (Derinlik: {args.derinlik})\n" + "=" * 50)
        fikirler = fikir_uret(args.fikir, args.derinlik)
        for f in fikirler:
            derinlik_ikon = {1: "📊", 2: "🔄", 3: "🛸"}
            print(f"\n{derinlik_ikon.get(f['derinlik'], '💡')} **{f['fikir']}**")
            print(f"   📝 {f['aciklama']}")
            print(f"   🎯 Zorluk: {f['zorluk']}")
        return

    # --- MVP Plan ---
    if args.mvp:
        print(f"\n📋 MVP PLANI: {args.mvp}\n" + "=" * 50)
        plan = MVP_plan(args.mvp)
        for faz in plan["fazlar"]:
            print(f"\n**{faz['faz']}** ({faz['sure']})")
            for y in faz["yapilacaklar"]:
                print(f"  • {y}")
        print(f"\n📅 Toplam süre: {plan['toplam_sure']}")
        print(f"🎯 Öncelikli kaynaklar: {', '.join(plan['oncelikli_kaynaklar'])}")
        print(f"💡 Not: {plan['not']}")
        return

    # --- Fikir Puanla ---
    if args.puanla:
        print(f"\n⭐ FİKİR PUANLAMA: {args.puanla}\n" + "=" * 50)
        sonuc = fikir_puanla(args.puanla)
        print(f"\n**{sonuc['fikir']}**")
        print(f"📊 Toplam Puan: **{sonuc['toplam_puan']}/100**")
        print(f"🏆 Değerlendirme: {sonuc['degerlendirme']}")
        for k, v in sonuc['puanlar'].items():
            bar = "█" * v + "░" * (10 - v)
            print(f"  {k}: {bar} {v}/10")
        return

    # --- Proje Başlat ---
    if args.proje_baslat:
        print(f"\n🚀 PROJE BAŞLATILIYOR: {args.proje_baslat}\n" + "=" * 50)
        sonuc = proje_baslat(args.proje_baslat, args.kaynak)
        proje = sonuc["proje"]
        print(f"✅ Proje başlatıldı!")
        print(f"📁 Dosya: {sonuc['dosya']}")
        print(f"📅 Hedef bitiş: {proje['hedef_bitis'][:10]}")
        print(f"🎯 Kaynaklar: {', '.join(proje['kaynaklar'])}")
        print(f"\n📋 Görevler:")
        for g in proje['gorevler']:
            durum_ikon = "✅" if g['durum'] == 'tamamlandı' else "⏳" if g['durum'] == 'devam' else "⏸️"
            print(f"  {durum_ikon} {g['gorev']} ({g['sure']})")
        return

    # --- MVP Kod ---
    if args.mvp_kod:
        print(f"\n💻 MVP KOD YAPISI: {args.mvp_kod}\n" + "=" * 50)
        sonuc = MVP_kodla(args.mvp_kod)
        print(f"✅ MVP kod yapısı oluşturuldu!")
        print(f"📁 Dizin: {sonuc['dizin']}")
        for f in sonuc['dosyalar']:
            print(f"  📄 {f}")
        print(f"\n💡 {sonuc['not']}")
        return

    # --- İlerleme Kaydet ---
    if args.ilerleme is not None and args.proje_baslat:
        print(f"\n📈 İlerleme güncelleniyor...")
        # Bu durumda proje_adi --proje-baslat arg'ından gelir
        pass

    # --- Şaşırt ---
    if args.sasirt:
        print(f"\n{'-' * 50}")
        sonuc = sasirtma_hazirla()
        print(f"\n**{sonuc['baslik']}**")
        print(f"🏷️ Tip: {sonuc['tip']}")
        print(f"\n{sonuc['icerik']}")
        print(f"\n{sonuc['mesaj']}")
        print(f"{'-' * 50}")
        return

    # --- Sürpriz ---
    if args.surpriz:
        sonuc = haftanin_surprizi()
        print(f"\n{sonuc['baslik']}")
        print(f"📆 {sonuc['gun']}")
        print(f"\n💡 {sonuc['icgoru']}")
        print(f"\n⚡ Öneri: {sonuc['eylem']}")
        return

    # --- Keşif ---
    if args.kesif:
        sonuc = beklenmeyen_kesif()
        print(f"\n{sonuc['baslik']}")
        print(f"\n**{sonuc['kesif']['konu']}**")
        print(f"\n💡 {sonuc['kesif']['neden_ilginc']}")
        return

    # --- Roadmap ---
    if args.roadmap:
        roadmap = alti_aylik_roadmap()
        print(f"\n{roadmap['baslik']}\n" + "=" * 50)
        print(f"\n🌟 Vizyon: {roadmap['vizyon']}")
        for ay in roadmap['aylar']:
            print(f"\n**{ay['ay']}** — {ay['odak']}")
            for h in ay['hedefler']:
                print(f"  ✅ {h}")
            print(f"  🎯 Kritik hamle: {ay['kritik_hamle']}")
        print(f"\n📊 **6 Ay Sonu Hedefi:**")
        for k, v in roadmap['6_ay_sonu_hedef'].items():
            print(f"  • {k}: {v}")
        return

    # --- Vizyon Raporu ---
    if args.vizyon:
        import textwrap
        roadmap = alti_aylik_roadmap()
        strateji = buyume_stratejisi()

        print(f"\n{'=' * 60}")
        print(f"🏛️  ERGENEAI VİZYON RAPORU")
        print(f"{'=' * 60}")

        print(f"\n## 🌟 Vizyon")
        print(f"{roadmap['vizyon']}")

        print(f"\n## 📅 6 Aylık Hedefler")
        for k, v in roadmap['6_ay_sonu_hedef'].items():
            print(f"  • **{k}**: {v}")

        print(f"\n## 📈 Büyüme Stratejileri")
        for s in strateji['stratejiler']:
            print(f"\n**{s['ad']}** ({s['maliyet']} maliyet / {s['etki']} etki)")
            print(f"  {s['aciklama']}")
            print(f"  👉 {s['nasil']}")

        print(f"\n## 💡 Genel Tavsiye")
        print(f"{strateji['tavsiye']}")
        print(f"{'=' * 60}")
        return

    # --- Strateji ---
    if args.strateji:
        strateji = buyume_stratejisi()
        print(f"\n{strateji['baslik']}\n" + "=" * 50)
        for s in strateji['stratejiler']:
            print(f"\n**{s['ad']}**")
            print(f"  Maliyet: {s['maliyet']} | Etki: {s['etki']}")
            print(f"  {s['aciklama']}")
            print(f"  👉 {s['nasil']}")
        print(f"\n💡 {strateji['tavsiye']}")
        return

    # --- Rakip Analizi ---
    if args.rakip:
        analiz = rakip_analizi(args.rakip)
        print(f"\n🎯 RAKİP ANALİZİ: {analiz['sektor']}\n" + "=" * 50)
        for r in analiz['rakipler']:
            print(f"\n**{r['isim']}**")
            print(f"  ✅ Güçlü: {r['guclu']}")
            print(f"  ❌ Zayıf: {r['zayif']}")
            print(f"  ⚠️ Tehdit seviyesi: {r['tehdit']}")
        print(f"\n💪 ErgeneAI Avantajı: {analiz['erGeneAI_avantaji']}")
        print(f"💡 Tavsiye: {analiz['tavsiye']}")
        return

    # --- Durum ---
    if args.durum:
        durum = modul_durumu()
        print(f"\n{'=' * 50}")
        print(f"🧠 **{durum['modul']}** — DURUM RAPORU")
        print(f"{'=' * 50}")
        print(f"\n🟢 Aktif: {'✅ Evet' if durum['aktif_mi'] else '❌ Hayır'}")
        print(f"\n📦 Bileşenler:")
        for ad, bilgi in durum['bilesenler'].items():
            print(f"  {bilgi['durum']} **{ad}**")
            for f in bilgi['fonksiyonlar']:
                print(f"    • `{f}()`")
        print(f"\n📁 Projeler ({len(durum['projeler'])}):")
        if durum['projeler']:
            for p in durum['projeler']:
                bar = "█" * (p['ilerleme'] // 10) + "░" * (10 - p['ilerleme'] // 10)
                print(f"  • **{p['ad']}**: {bar} {p['ilerleme']}% ({p['durum']})")
        else:
            print(f"  (Henüz proje başlatılmadı)")
        print(f"\n🔥 Çılgın fikir sayısı: {durum['cilgin_fikir_sayisi']}")
        print(f"{'=' * 50}")
        return

    # Varsayılan: yardım
    parser.print_help()


if __name__ == "__main__":
    main()
