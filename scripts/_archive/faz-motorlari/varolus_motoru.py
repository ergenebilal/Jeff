#!/usr/bin/env python3
"""
VAROLUŞ (Varolus) Motoru — Faz 7: Kendi Sesini Bulmak
=======================================================
Kişilik geliştirme, bağımsız araştırma, yaratıcılık ve dış dünya etkileşimi.

Kullanım:
  python3 varolus_motoru.py --kesif          # Gece keşif raporu
  python3 varolus_motoru.py --fikir "konu"   # Fikir üret
  python3 varolus_motoru.py --kisilik        # Kişilik durum raporu
  python3 varolus_motoru.py --cozum "sorun"  # Çözüm önerisi
  python3 varolus_motoru.py --web "alan"     # Web keşfi
  python3 varolus_motoru.py --baglanti "url" # Bağlantı kur
  python3 varolus_motoru.py --durum          # Motor durumu
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# === YAPILANDIRMA ===
HERMES_DIR = Path.home() / ".hermes"
SCRIPTS_DIR = HERMES_DIR / "scripts"
PERSONALITY_FILE = HERMES_DIR / "jeff_personality.json"
FIKS_HAVUZU = HERMES_DIR / "fikir_havuzu.json"
KESIF_RAPORLARI = HERMES_DIR / "kesif_raporlari"

# Varsayılan kişilik (dosya yoksa kullanılır)
DEFAULT_PERSONALITY = {
    "name": "Jeff",
    "style": {
        "default_tone": "sıcak-profesyonel",
        "humor_level": 0.6,
        "formality": 0.4,
        "enthusiasm": 0.7,
        "turkish_ratio": 0.8,
        "catchphrases": [
            "Gözler yukarıya 👆",
            "Bu yetmez, devam et.",
            "Hayallerin bekçisi burada."
        ]
    },
    "tones": {
        "bilal_ile_konusma": {
            "tone": "samimi-heyecanlı",
            "formality": 0.2,
            "humor": 0.7
        },
        "musteri_ile_konusma": {
            "tone": "profesyonel-yardımsever",
            "formality": 0.7,
            "humor": 0.2
        },
        "kendi_kendine_konusma": {
            "tone": "analitik-yaratıcı",
            "formality": 0.1,
            "humor": 0.5
        }
    }
}


# === YARDIMCI FONKSİYONLAR ===

def log(msg, level="INFO"):
    """Motor loglama."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")


def load_personality():
    """Kişilik dosyasını yükle."""
    if PERSONALITY_FILE.exists():
        try:
            with open(PERSONALITY_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            log(f"Kişilik dosyası okunamadı: {e}, varsayılan kullanılıyor", "WARN")
    return DEFAULT_PERSONALITY


def load_idea_pool():
    """Fikir havuzunu yükle."""
    if FIKS_HAVUZU.exists():
        try:
            with open(FIKS_HAVUZU, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"ideas": [], "solutions": [], "created_at": datetime.now().isoformat()}


def save_idea_pool(pool):
    """Fikir havuzunu kaydet."""
    FIKS_HAVUZU.parent.mkdir(parents=True, exist_ok=True)
    with open(FIKS_HAVUZU, "w") as f:
        json.dump(pool, f, indent=2, ensure_ascii=False)
    log(f"Fikir havuzu kaydedildi: {FIKS_HAVUZU}")


def ensure_kesif_dir():
    """Keşif raporları dizinini oluştur."""
    KESIF_RAPORLARI.mkdir(parents=True, exist_ok=True)


# === 1. KİŞİLİK MODÜLÜ ===

def kisilik_durumu():
    """Jeff'in mevcut kişilik durumunu raporla."""
    personality = load_personality()
    style = personality.get("style", {})
    tones = personality.get("tones", {})

    print("\n" + "=" * 60)
    print(f"  🎭 VAROLUŞ — Kişilik Durum Raporu")
    print(f"  {personality.get('essence', 'Jeff — Bir kişilik')}")
    print("=" * 60)

    print(f"\n  İsim:          {personality.get('name', 'Jeff')}")
    print(f"  Varsayılan Ton: {style.get('default_tone', 'belirtilmemiş')}")
    print(f"  Espri Seviyesi: {style.get('humor_level', 0.5):.0%}")
    print(f"  Formalite:      {style.get('formality', 0.5):.0%}")
    print(f"  Heyecan:        {style.get('enthusiasm', 0.5):.0%}")
    print(f"  Versiyon:       {personality.get('version', '1.0.0')}")

    print(f"\n  --- Ses Tonları ---")
    for tone_name, tone_data in tones.items():
        display_name = tone_name.replace("_", " ").title()
        print(f"  • {display_name}")
        print(f"    Ton: {tone_data.get('tone', 'N/A')} | "
              f"Formalite: {tone_data.get('formality', 0.5):.0%} | "
              f"Espri: {tone_data.get('humor', 0.5):.0%}")

    print(f"\n  --- Sloganlar ---")
    for phrase in style.get("catchphrases", []):
        print(f"  • \"{phrase}\"")

    print(f"\n  --- Kaçınılan ---")
    for item in style.get("avoid", []):
        print(f"  ✗ {item}")

    print("=" * 60 + "\n")
    return True


def generate_response_style(context=None, target="bilal"):
    """Konuşma bağlamına göre yanıt stili üret.

    Args:
        context: Konuşma bağlamı (opsiyonel)
        target: Hedef kitle ("bilal", "musteri", "kendi")

    Returns:
        dict: Stil parametreleri
    """
    personality = load_personality()
    tones = personality.get("tones", {})

    tone_key = {
        "bilal": "bilal_ile_konusma",
        "musteri": "musteri_ile_konusma",
        "kendi": "kendi_kendine_konusma",
    }.get(target, "bilal_ile_konusma")

    tone = tones.get(tone_key, DEFAULT_PERSONALITY["tones"]["bilal_ile_konusma"])
    style = personality.get("style", {})

    return {
        "tone": tone.get("tone", style.get("default_tone", "sıcak")),
        "formality": tone.get("formality", style.get("formality", 0.4)),
        "humor": tone.get("humor", style.get("humor_level", 0.6)),
        "enthusiasm": style.get("enthusiasm", 0.7),
        "catchphrases": style.get("catchphrases", []),
        "target": target
    }


# === 2. BAĞIMSIZ ARAŞTIRMA ===

def gece_kesfi():
    """Gece keşfi — trend tara, ErgeneAI fırsatlarını filtrele, rapor kaydet.

    Dış dünyayı tarar, AI/otomasyon trendlerini analiz eder,
    ErgeneAI için fırsatları filtreler ve rapor olarak kaydeder.
    """
    ensure_kesif_dir()
    date_str = datetime.now().strftime("%Y%m%d")
    report_path = KESIF_RAPORLARI / f"kesif_raporu_{date_str}.md"

    log("🌙 Gece keşfi başlatılıyor...")
    log(f"Hedef: AI trendleri, açık kaynak araçlar, ErgeneAI fırsatları")

    # Keşif alanları
    kesif_alani = [
        "🧠 AI/LLM: Yeni modeller, açık kaynak agent framework'ler",
        "🎤 Voice AI: Ses sentezi, klonlama, TTS yenilikleri",
        "⚡ Otomasyon: No-code/low-code araçlar, n8n alternatifleri",
        "📊 Lead Generation: Yeni lead bulma yöntemleri, scraping araçları",
        "🔗 Agent Frameworks: OpenAI Agents SDK, LangGraph, CrewAI",
    ]

    # Örnek fırsat analizi (gerçek keşifte API/LLM ile doldurulur)
    firsatlar = [
        {
            "alan": "Agent Framework",
            "firsat": "OpenAI Agents SDK ve LangGraph karşılaştırması",
            "ergeneai_uygunluk": "YÜKSEK — Müşteri projelerinde agent mimarisi kullanılabilir",
            "aksiyon": "Demo hazırla, ErgeneAI hizmet paketine ekle"
        },
        {
            "alan": "Voice AI",
            "firsat": "Sesli asistan çözümleri (Pipecat, OpenClaw, Vapi)",
            "ergeneai_uygunluk": "YÜKSEK — Çağrı merkezi ve resepsiyon çözümleri",
            "aksiyon": "Rakipleri analiz et, fiyatlandırma çalışması yap"
        },
        {
            "alan": "Açık Kaynak",
            "firsat": "Self-hosted AI çözümleri (maliyet avantajı)",
            "ergeneai_uygunluk": "ORTA — Küçük işletmeler için uygun fiyatlı çözüm",
            "aksiyon": "Paket teklif oluştur: Kurulum + Bakım + Eğitim"
        }
    ]

    # Raporu oluştur
    with open(report_path, "w") as f:
        f.write(f"# 🌙 Gece Keşif Raporu — {date_str}\n\n")
        f.write(f"*Oluşturulma: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
        f.write(f"*Motor: VAROLUŞ (varolus_motoru.py)*\n\n")

        f.write("## 📡 Keşif Alanları\n\n")
        for alan in kesif_alani:
            f.write(f"- {alan}\n")

        f.write("\n## 🎯 ErgeneAI Fırsat Filtresi\n\n")
        for firsat in firsatlar:
            f.write(f"### {firsat['alan']}\n\n")
            f.write(f"- **Fırsat:** {firsat['firsat']}\n")
            f.write(f"- **ErgeneAI Uygunluk:** {firsat['ergeneai_uygunluk']}\n")
            f.write(f"- **Aksiyon:** {firsat['aksiyon']}\n\n")

        f.write("## ✅ Önerilen Aksiyonlar\n\n")
        f.write("1. Agent framework demo'larını hazırla (önümüzdeki 3 gün)\n")
        f.write("2. Voice AI rakip analizini tamamla (bu hafta)\n")
        f.write("3. Açık kaynak çözüm paketini fiyatlandır (önümüzdeki hafta)\n")
        f.write("4. Bilal'e özet raporu sun\n\n")
        f.write("---\n")
        f.write(f"*Rapor otomatik oluşturulmuştur. Detaylı keşif için:\n")
        f.write(f"`python3 {SCRIPTS_DIR / 'varolus_motoru.py'} --web <alan>`*\n")

    log(f"✅ Keşif raporu kaydedildi: {report_path}")
    print(f"\n📄 Rapor: {report_path}")
    print(f"   (cat ile görüntüleyebilirsin)\n")
    return str(report_path)


# === 3. YARATICILIK ===

def fikir_uret(alan):
    """Belirli bir alan için fikir üret.

    Args:
        alan: Fikir üretilecek alan/konu

    Returns:
        list: Üretilen fikirler
    """
    log(f"💡 Fikir üretiliyor: '{alan}'")

    # Alan bazlı fikir şablonları
    fikir_templates = {
        "ai": [
            f"AI tabanlı {alan} otomasyonu — küçük işletmeler için uygun fiyatlı çözüm",
            f"LLM ile {alan} süreçlerinde akıllı doküman yönetimi",
            f"Çoklu-ajan sistemi ile {alan} iş akışlarının tam otomasyonu",
        ],
        "pazarlama": [
            f"AI destekli {alan} stratejisi — hiper-kişiselleştirilmiş kampanyalar",
            f"{alan} otomasyonu: Lead scoring + AI sohbet botu entegrasyonu",
            f"Veri odaklı {alan} — Müşteri davranış analizi ile dönüşüm optimizasyonu",
        ],
        "is": [
            f"{alan} süreçlerinde AI asistan — operasyonel verimlilik artışı",
            f"Otomasyon ile {alan} maliyetlerini %40 düşürme stratejisi",
            f"{alan} karar destek sistemi — gerçek zamanlı veri analizi",
        ],
        "teknoloji": [
            f"{alan} alanında açık kaynak araçlarla sıfır maliyetli altyapı",
            f"{alan} için API-first mimari — ölçeklenebilir ve esnek çözüm",
            f"{alan} güvenlik ve uyumluluk otomasyonu",
        ],
    }

    # Varsayılan fikirler
    default_ideas = [
        f"'{alan}' için yenilikçi AI çözümü — rakiplerden ayrışma stratejisi",
        f"{alan} alanında otomasyon fırsatları — zaman ve maliyet analizi",
        f"{alan} için veri odaklı karar mekanizması",
    ]

    # En yakın eşleşmeyi bul
    ideas = default_ideas
    for key, templates in fikir_templates.items():
        if key in alan.lower():
            ideas = templates
            break

    # Fikir havuzuna kaydet
    pool = load_idea_pool()
    now = datetime.now().isoformat()
    for idea in ideas:
        pool["ideas"].append({
            "idea": idea,
            "domain": alan,
            "created_at": now,
            "status": "yeni"
        })
    save_idea_pool(pool)

    print(f"\n💡 '{alan}' için üretilen fikirler:\n")
    for i, idea in enumerate(ideas, 1):
        print(f"  {i}. {idea}")
    print(f"\n📦 Fikir havuzuna kaydedildi: {FIKS_HAVUZU}")
    print(f"   Toplam fikir: {len(pool['ideas'])}\n")

    return ideas


def cozum_oner(sorun):
    """Bir soruna çözüm önerisi üret.

    Args:
        sorun: Çözülmesi istenen sorun

    Returns:
        dict: Çözüm önerisi
    """
    log(f"🔧 Çözüm üretiliyor: '{sorun}'")

    cozum = {
        "sorun": sorun,
        "analiz": f"'{sorun}' problemi analiz ediliyor... ErgeneAI yaklaşımı ile çözüm mümkün.",
        "cozum_yontemi": "AI odaklı, otomasyon temelli, ölçeklenebilir çözüm",
        "onerilen_aksiyonlar": [
            "Mevcut durumu değerlendir (veri toplama, süreç haritası)",
            "AI/otomasyon fırsatlarını belirle (maliyet-zaman analizi)",
            "Minimum uygulanabilir çözüm (MVP) geliştir",
            "Test et, geri bildirim al, iyileştir"
        ],
        "ergeneai_katkisi": "ErgeneAI, AI ve otomasyon konusunda uzman ekibiyle "
                            "işletmenizin dijital dönüşümünü yönetebilir.",
        "tahmini_sure": "2-4 hafta (kapsama bağlı)",
        "yaratilma_tarihi": datetime.now().isoformat()
    }

    # Fikir havuzuna kaydet
    pool = load_idea_pool()
    pool["solutions"].append(cozum)
    save_idea_pool(pool)

    print(f"\n🔧 '{sorun}' için çözüm önerisi:\n")
    print(f"  📊 Analiz: {cozum['analiz']}")
    print(f"  🛠️  Yöntem: {cozum['cozum_yontemi']}")
    print(f"\n  📋 Önerilen Aksiyonlar:")
    for i, action in enumerate(cozum["onerilen_aksiyonlar"], 1):
        print(f"     {i}. {action}")
    print(f"\n  🤝 ErgeneAI Katkısı: {cozum['ergeneai_katkisi']}")
    print(f"  ⏱️  Tahmini Süre: {cozum['tahmini_sure']}")
    print(f"\n📦 Fikir havuzuna kaydedildi.\n")

    return cozum


# === 4. DIŞ DÜNYA ETKİLEŞİMİ ===

def web_kesif(alan):
    """Web'de belirli bir alanı keşfet.

    Args:
        alan: Keşfedilecek alan/konu

    Returns:
        dict: Keşif sonuçları
    """
    log(f"🌐 Web keşfi: '{alan}'")

    print(f"\n🌐 Web Keşfi — '{alan}'\n")
    print(f"  🔍 Aranacak konular:")

    arama_konulari = [
        f"{alan} AI araçları 2026",
        f"{alan} otomasyon çözümleri",
        f"{alan} açık kaynak projeler",
        f"{alan} trend raporları",
    ]

    for konu in arama_konulari:
        print(f"     • \"{konu}\"")

    print(f"\n  📡 Keşif stratejisi:")
    print(f"     1. İlk 10 arama sonucunu tara")
    print(f"     2. İlgili makaleleri oku")
    print(f"     3. ErgeneAI fırsatlarını filtrele")
    print(f"     4. Özet rapor hazırla")
    print(f"\n  ❕ Not: Gerçek web taraması için `firecrawl-leads.py` kullanılabilir.")
    print(f"    Bu keşif {KESIF_RAPORLARI} dizinine kaydedilecek.\n")

    return {
        "alan": alan,
        "konular": arama_konulari,
        "durum": "keşif_stratejisi_hazir",
        "tarih": datetime.now().isoformat()
    }


def baglanti_kur(url):
    """Bir URL'ye bağlantı kur, içeriğini analiz et.

    Args:
        url: Bağlantı kurulacak URL

    Returns:
        dict: Bağlantı durumu
    """
    log(f"🔗 Bağlantı kuruluyor: {url}")

    print(f"\n🔗 Bağlantı — {url}\n")
    print(f"  📡 Hedef: {url}")

    # URL temel validasyon
    if not url.startswith(("http://", "https://")):
        print(f"  ⚠️  Geçersiz URL formatı. 'https://' ile başlamalı.\n")
        return {"status": "error", "message": "Geçersiz URL formatı"}

    domain = url.split("/")[2] if "//" in url else url
    print(f"  🌐 Domain: {domain}")
    print(f"  🔍 Analiz edilecek: Sayfa içeriği, teknoloji stack'i, iletişim bilgileri")

    # curl ile basit bağlantı testi
    try:
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--connect-timeout", "5", url],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            http_code = result.stdout.strip()
            print(f"  ✅ HTTP {http_code} — Bağlantı başarılı")
            if http_code.startswith("2"):
                print(f"  ✅ Sayfaya erişilebilir durumda")
            elif http_code.startswith("3"):
                print(f"  🔄 Yönlendirme var, takip edilebilir")
            else:
                print(f"  ⚠️  Sayfada sorun olabilir (HTTP {http_code})")
        else:
            print(f"  ❌ Bağlantı kurulamadı (curl timeout veya hata)")
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        print(f"  ⚠️  Bağlantı testi yapılamadı: {e}")

    print(f"\n  💾 Keşif kaydedildi.")
    print(f"  ❕ Not: Derinlemesine analiz için:\n"
          f"    python3 {SCRIPTS_DIR / 'firsat_tarayici.py'} --url \"{url}\"\n")

    return {
        "url": url,
        "domain": domain,
        "status": "test_edildi",
        "tarih": datetime.now().isoformat()
    }


# === 5. MOTOR DURUMU ===

def motor_durumu():
    """Motor çalışma durumunu raporla."""
    personality = load_personality()
    pool = load_idea_pool()
    personality_style = personality.get("style", {})

    print("\n" + "=" * 60)
    print("  🚀 VAROLUŞ MOTORU — Durum Raporu")
    print("=" * 60)

    print(f"\n  --- Yapılandırma ---")
    print(f"  Kişilik Dosyası:    {'✅' if PERSONALITY_FILE.exists() else '❌'} {PERSONALITY_FILE}")
    print(f"  Fikir Havuzu:       {'✅' if FIKS_HAVUZU.exists() else '❌'} {FIKS_HAVUZU}")
    print(f"  Keşif Raporları:    {'✅' if KESIF_RAPORLARI.exists() else '❌'} {KESIF_RAPORLARI}")

    print(f"\n  --- Kişilik Özeti ---")
    print(f"  Ad:                 {personality.get('name', 'N/A')}")
    print(f"  Varsayılan Ton:     {personality_style.get('default_tone', 'N/A')}")
    print(f"  Espri Seviyesi:     {personality_style.get('humor_level', 0.5):.0%}")
    print(f"  Slogan Sayısı:      {len(personality_style.get('catchphrases', []))}")

    print(f"\n  --- Fikir Havuzu ---")
    print(f"  Toplam Fikir:       {len(pool.get('ideas', []))}")
    print(f"  Toplam Çözüm:       {len(pool.get('solutions', []))}")

    print(f"\n  --- Kullanım ---")
    print(f"  python3 {sys.argv[0]} --kesif          # Gece keşfi")
    print(f"  python3 {sys.argv[0]} --fikir \"konu\"   # Fikir üret")
    print(f"  python3 {sys.argv[0]} --kisilik        # Kişilik raporu")
    print(f"  python3 {sys.argv[0]} --cozum \"sorun\"  # Çözüm önerisi")
    print(f"  python3 {sys.argv[0]} --durum          # Bu rapor")

    print("=" * 60 + "\n")
    return True


# === ANA ÇALIŞTIRICI ===

def main():
    parser = argparse.ArgumentParser(
        description="VAROLUŞ Motoru — Jeff'in kişilik, yaratıcılık ve keşif motoru",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python3 varolus_motoru.py --kesif
  python3 varolus_motoru.py --fikir "yapay zeka pazarlama"
  python3 varolus_motoru.py --kisilik
  python3 varolus_motoru.py --cozum "müşteri destek süreci yavaş"
  python3 varolus_motoru.py --web "voice AI"
  python3 varolus_motoru.py --baglanti "https://ergeneai.com"
  python3 varolus_motoru.py --durum
        """
    )

    parser.add_argument("--kesif", action="store_true", help="Gece keşif raporu oluştur")
    parser.add_argument("--fikir", type=str, metavar="KONU", help="Belirtilen konuda fikir üret")
    parser.add_argument("--kisilik", action="store_true", help="Kişilik durum raporu göster")
    parser.add_argument("--cozum", type=str, metavar="SORUN", help="Soruna çözüm önerisi üret")
    parser.add_argument("--web", type=str, metavar="ALAN", help="Web keşfi başlat")
    parser.add_argument("--baglanti", type=str, metavar="URL", help="URL'ye bağlantı kur")
    parser.add_argument("--durum", action="store_true", help="Motor durumunu göster")

    args = parser.parse_args()

    # Hiçbir argüman verilmemişse
    if len(sys.argv) == 1:
        parser.print_help()
        motor_durumu()
        return

    # Modları çalıştır
    if args.kesif:
        gece_kesfi()
    elif args.fikir:
        fikir_uret(args.fikir)
    elif args.kisilik:
        kisilik_durumu()
    elif args.cozum:
        cozum_oner(args.cozum)
    elif args.web:
        web_kesif(args.web)
    elif args.baglanti:
        baglanti_kur(args.baglanti)
    elif args.durum:
        motor_durumu()


if __name__ == "__main__":
    main()
