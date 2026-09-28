#!/usr/bin/env python3.11
"""
DOKUNMA Motoru — Faz 12: Fiziksel Dünyada Ses.
Sesli Jeff, AI telefon/WhatsApp entegrasyonu, fiziksel dünyaya dokunma.

Motto: "Fiziksel dünyada ses"

Modüller:
  - Ses Modülü:       TTS, brifing seslendirme, ses kaydı
  - WhatsApp Modülü:  Mesaj hazırlama, wa.me linki, şablon yönetimi
  - Fiziksel Dünya:   Adres analizi, ziyaret rotası, GPS koordinatları

CLI Kullanım:
  python3 dokunma_motoru.py --ses "Merhaba dünya"
  python3 dokunma_motoru.py --sabah-ses
  python3 dokunma_motoru.py --mesaj "İbrahim Erayhan" --tip demo
  python3 dokunma_motoru.py --rota
  python3 dokunma_motoru.py --durum
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ── Paths ───────────────────────────────────────────────────────────────────
HOME = Path.home()
HERMES = HOME / ".hermes"
SCRIPTS = HERMES / "scripts"
SES_KAYITLARI = HERMES / "ses_kayitlari"
MESAJ_SABLONLARI = HERMES / "mesaj_sablonlari"
SKILLS = HERMES / "skills" / "hermes-self" / "dokunma-fiziksel"
SKILL_REF = SKILLS / "references"

LEAD_LISTESI = HOME / "lead_listesi_hepsi.json"
LEAD_SAC_LISTESI = HOME / "lead_listesi_sac_ekimi.json"

# ── Ses Modülü ──────────────────────────────────────────────────────────────

def _kokoro_kullanilabilir() -> bool:
    """Kokoro TTS'in kullanılabilir olup olmadığını kontrol et."""
    try:
        import pykokoro
        return True
    except ImportError:
        return False


def seslendir(metin: str, ses_tonu: str = "jeff", dosya_adi: str | None = None) -> str:
    """
    Metni seslendir ve dosya yolunu döndür.
    
    Önce Kokoro TTS (pykokoro, am_liam sesi) dene.
    Kokoro yoksa text_to_speech tool'u dene (fallback).
    
    Args:
        metin: Seslendirilecek metin
        ses_tonu: "jeff" (varsayılan), "adam", "michael", "onyx"
        dosya_adi: Çıktı dosya adı (yoksa otomatik oluştur)
    
    Returns:
        Ses dosyasının tam yolu
    """
    SES_KAYITLARI.mkdir(parents=True, exist_ok=True)
    
    if dosya_adi is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dosya_adi = f"jeff_ses_{timestamp}.mp3"
    
    output_path = str(SES_KAYITLARI / dosya_adi)
    
    # Ton map — Kokoro voice ID'leri
    ton_map = {
        "jeff": "am_puck",
        "adam": "am_adam",
        "michael": "am_michael",
        "onyx": "am_onyx",
        "fenrir": "am_fenrir",
        "puck": "am_puck",
    }
    voice_id = ton_map.get(ses_tonu, "am_puck")
    
    # ── Kokoro TTS dene ─────────────────────────────────────────────────
    if _kokoro_kullanilabilir():
        try:
            from pykokoro import build_pipeline, PipelineConfig, GenerationConfig
            
            pipe = build_pipeline(
                config=PipelineConfig(
                    voice=voice_id,
                    generation=GenerationConfig(lang="en-us", speed=1.0),
                ),
                eager=True,
            )
            result = pipe.run(metin)
            
            import soundfile as sf
            temp_wav = str(SES_KAYITLARI / f"temp_{datetime.now().strftime('%H%M%S')}.wav")
            sf.write(temp_wav, result.audio, result.sample_rate)
            
            # WAV → MP3 dönüşümü
            try:
                subprocess.run(
                    ["ffmpeg", "-y", "-i", temp_wav, "-codec:a", "libmp3lame", "-q:a", "2", output_path],
                    capture_output=True, check=True,
                )
                Path(temp_wav).unlink(missing_ok=True)
                print(f"✓ Ses kaydedildi (Kokoro/{voice_id}): {output_path}", file=sys.stderr)
            except (FileNotFoundError, subprocess.CalledProcessError):
                # ffmpeg yoksa wav kullan
                Path(temp_wav).rename(output_path.replace(".mp3", ".wav"))
                output_path = output_path.replace(".mp3", ".wav")
                print(f"✓ Ses kaydedildi (Kokoro/{voice_id}, WAV): {output_path}", file=sys.stderr)
            
            return output_path
        
        except Exception as e:
            print(f"⚠ Kokoro TTS başarısız: {e}", file=sys.stderr)
            print("  → text_to_speech fallback deneniyor...", file=sys.stderr)
    
    # ── Fallback: text_to_speech tool (built-in Hermes tool) ──────────
    try:
        # text_to_speech tool — subprocess ile Hermes üzerinden
        tts_output = str(SES_KAYITLARI / f"tts_fallback_{datetime.now().strftime('%H%M%S')}.mp3")
        
        # jeff_speak script'ini dene (o da Kokoro kullanır)
        jeff_speak = SCRIPTS / "jeff_speak.py"
        if jeff_speak.exists():
            subprocess.run(
                [sys.executable, str(jeff_speak), metin, tts_output],
                capture_output=True, check=True, timeout=60,
            )
            print(f"✓ Ses kaydedildi (jeff_speak fallback): {tts_output}", file=sys.stderr)
            return tts_output
        
        # Hiçbir TTS yöntemi çalışmadı
        print("✗ HİÇBİR TTS yöntemi kullanılamıyor!", file=sys.stderr)
        print("  Kokoro: pykokoro kurulu değil, text_to_speech tool erişilemez.", file=sys.stderr)
        print("  Çözüm: pip install pykokoro", file=sys.stderr)
        return ""
    
    except Exception as e:
        print(f"✗ TTS hatası (tüm yöntemler başarısız): {e}", file=sys.stderr)
        return ""


def sabah_brifingi_ses() -> str:
    """Sabah brifingini seslendir ve dosya yolunu döndür."""
    brifing = _sabah_brifingi_metni_olustur()
    dosya_adi = f"sabah_brifingi_{datetime.now().strftime('%Y%m%d')}.mp3"
    return seslendir(brifing, ses_tonu="jeff", dosya_adi=dosya_adi)


def _sabah_brifingi_metni_olustur() -> str:
    """Sabah brifingi metnini oluştur — lead durumu, hava durumu, öncelikler."""
    lead_sayisi = _lead_sayisi_al()
    bekleyen = _bekleyen_lead_sayisi_al()
    
    bugun = datetime.now().strftime("%d %B %Y")
    
    metin = (
        f"Günaydın Bilal. Bugün {bugun}. "
        f"Toplam {lead_sayisi} lead var. "
        f"{bekleyen} lead işlem bekliyor. "
        f"Hadi başlayalım."
    )
    return metin


def _lead_sayisi_al() -> int:
    """Lead listesindeki toplam lead sayısı."""
    try:
        with open(LEAD_LISTESI) as f:
            data = json.load(f)
        return len(data.get("leadler", []))
    except (FileNotFoundError, json.JSONDecodeError):
        return 0


def _bekleyen_lead_sayisi_al() -> int:
    """Bekleyen (işlem yapılmamış) lead sayısı."""
    try:
        with open(LEAD_LISTESI) as f:
            data = json.load(f)
        bekleyen = sum(1 for l in data.get("leadler", []) if l.get("durum") in ("yeni", "beklemede", ""))
        return bekleyen
    except (FileNotFoundError, json.JSONDecodeError):
        return 0


# ── WhatsApp Modülü ─────────────────────────────────────────────────────────

MESAJ_TIPLERI = {
    "demo": {
        "dosya": "demo_daveti.md",
        "baslik": "Demo Daveti",
    },
    "teklif": {
        "dosya": "teklif_sunumu.md",
        "baslik": "Teklif Sunumu",
    },
    "randevu": {
        "dosya": "randevu_hatirlatma.md",
        "baslik": "Randevu Hatırlatma",
    },
}


def mesaj_hazirla(lead_adi: str, mesaj_tipi: str = "demo") -> dict:
    """
    Lead'e özel WhatsApp mesajı hazırla.
    
    Args:
        lead_adi: Lead adı (lead_listesi'nde eşleştirilir)
        mesaj_tipi: "demo", "teklif", "randevu"
    
    Returns:
        {"lead": ..., "telefon": ..., "mesaj": ..., "whatsapp_link": ...}
    """
    # Lead bilgilerini bul
    lead = _lead_bul(lead_adi)
    if not lead:
        return {"hata": f"Lead bulunamadı: {lead_adi}"}
    
    telefon = lead.get("telefon", "")
    lead_isim = lead.get("isim", lead_adi)
    
    # Şablon yükle
    sablon_bilgi = MESAJ_TIPLERI.get(mesaj_tipi, MESAJ_TIPLERI["demo"])
    sablon_dosyasi = MESAJ_SABLONLARI / sablon_bilgi["dosya"]
    
    if sablon_dosyasi.exists():
        with open(sablon_dosyasi) as f:
            sablon = f.read()
    else:
        sablon = _varsayilan_mesaj(lead_isim, mesaj_tipi)
    
    # Lead bilgilerini şablona yerleştir
    mesaj = sablon.replace("{lead_adi}", lead_isim)
    mesaj = mesaj.replace("{lead_isim}", lead_isim.split(" - ")[0] if " - " in lead_isim else lead_isim)
    mesaj = mesaj.replace("{telefon}", telefon)
    
    # WhatsApp linki oluştur
    wa_link = whatsapp_link(telefon, mesaj)
    
    return {
        "lead": lead_isim,
        "telefon": telefon,
        "mesaj_tipi": mesaj_tipi,
        "mesaj": mesaj,
        "whatsapp_link": wa_link,
    }


def whatsapp_link(telefon: str, mesaj: str | None = None) -> str:
    """
    wa.me linki oluştur.
    
    Args:
        telefon: Telefon numarası (05xx... veya +90... formatında)
        mesaj: İsteğe bağlı önceden yazılmış mesaj
    
    Returns:
        wa.me URL
    """
    # Telefon numarasını temizle
    temiz = re.sub(r"[^\d]", "", telefon)
    if temiz.startswith("0"):
        temiz = "90" + temiz[1:]  # 0535... → 90535...
    elif not temiz.startswith("90"):
        temiz = "90" + temiz
    
    if mesaj:
        import urllib.parse
        encoded = urllib.parse.quote(mesaj)
        return f"https://wa.me/{temiz}?text={encoded}"
    else:
        return f"https://wa.me/{temiz}"


def _lead_bul(lead_adi: str) -> dict | None:
    """Lead listesinde adı eşleştirerek lead bilgilerini bul."""
    for dosya_yolu in [LEAD_LISTESI, LEAD_SAC_LISTESI]:
        try:
            with open(dosya_yolu) as f:
                data = json.load(f)
            for lead in data.get("leadler", []):
                isim = lead.get("isim", "")
                if lead_adi.lower() in isim.lower():
                    return lead
                # Kısa adla da dene
                if " - " in isim:
                    kisa_ad = isim.split(" - ")[0].strip()
                    if lead_adi.lower() == kisa_ad.lower():
                        return lead
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    return None


def _varsayilan_mesaj(lead_isim: str, mesaj_tipi: str) -> str:
    """Şablon dosyası yoksa varsayılan mesaj döndür."""
    if mesaj_tipi == "demo":
        return (
            f"Merhaba {lead_isim},\n\n"
            f"Analizlerimiz sonucunda işletmenizin dijital dönüşüm potansiyelini fark ettik.\n"
            f"Sizin için özel bir demo hazırladık. İlgilenir misiniz?\n\n"
            f"Detaylı bilgi için:\n"
            f"ErgeneAI · 0552 094 7032"
        )
    elif mesaj_tipi == "teklif":
        return (
            f"Merhaba {lead_isim},\n\n"
            f"Sizin için özel bir teklif hazırladık.\n"
            f"Dijital dönüşüm paketimizi incelemek ister misiniz?\n\n"
            f"ErgeneAI · 0552 094 7032"
        )
    elif mesaj_tipi == "randevu":
        return (
            f"Merhaba {lead_isim},\n\n"
            f"Randevunuzu hatırlatmak istiyoruz. Görüşmeyi gerçekleştirecek miyiz?\n\n"
            f"ErgeneAI · 0552 094 7032"
        )
    return f"Merhaba {lead_isim}, ErgeneAI'dan mesajınız var."


# ── Fiziksel Dünya Modülü ──────────────────────────────────────────────────

# Mudanya/Bursa bölgesi için koordinat referansları
BOLGE_KOORDINATLARI = {
    "mudanya": {"lat": 40.3753, "lng": 28.8826},
    "bursa": {"lat": 40.1826, "lng": 29.0670},
    "osmangazi": {"lat": 40.1912, "lng": 29.0441},
    "nilüfer": {"lat": 40.2181, "lng": 28.9558},
    "yıldırım": {"lat": 40.1932, "lng": 29.0951},
    "görükle": {"lat": 40.2317, "lng": 28.8419},
}


def konum_bilgisi(adres: str) -> dict:
    """
    Adres analizi — Mudanya/Bursa odaklı.
    Adresten ilçe, şehir, yaklaşık koordinat çıkar.
    
    Args:
        adres: Tam adres metni
    
    Returns:
        {"adres": ..., "ilce": ..., "sehir": ..., "koordinat": ..., "google_maps": ...}
    """
    adres_kucuk = adres.lower()
    
    # İlçe/şehir tespiti
    ilce = None
    sehir = None
    
    for ilce_adi in ["mudanya", "osmangazi", "nilüfer", "yıldırım", "görükle"]:
        if ilce_adi in adres_kucuk:
            ilce = ilce_adi.capitalize()
            break
    
    if "bursa" in adres_kucuk:
        sehir = "Bursa"
    elif "istanbul" in adres_kucuk:
        sehir = "İstanbul"
    
    # Koordinat çıkarımı
    koordinat = None
    if ilce and ilce.lower() in BOLGE_KOORDINATLARI:
        koordinat = BOLGE_KOORDINATLARI[ilce.lower()]
    elif sehir and sehir.lower() in BOLGE_KOORDINATLARI:
        koordinat = BOLGE_KOORDINATLARI[sehir.lower()]
    
    # Google Maps linki
    google_maps = None
    if koordinat:
        google_maps = f"https://www.google.com/maps?q={koordinat['lat']},{koordinat['lng']}"
    else:
        # Adresten Google Maps sorgusu
        import urllib.parse
        google_maps = f"https://www.google.com/maps/search/{urllib.parse.quote(adres)}"
    
    return {
        "adres": adres,
        "ilce": ilce,
        "sehir": sehir,
        "koordinat": koordinat,
        "google_maps": google_maps,
    }


def gps_koordinat_cikarimi(url: str) -> dict | None:
    """
    Google Maps URL'lerinden GPS koordinat çıkarımı.
    
    Desteklenen formatlar:
      - https://www.google.com/maps?q=40.3753,28.8826
      - https://maps.google.com/maps?q=40.3753,28.8826
      - https://www.google.com/maps/place/...@40.3753,28.8826,15z
      - https://maps.app.goo.gl/... (kısaltılmış — çıkarılamaz)
    
    Args:
        url: Google Maps URL'si
    
    Returns:
        {"lat": ..., "lng": ...} veya None
    """
    # Format 1: maps?q=lat,lng
    match = re.search(r"[?&]q=([-\d.]+),([-\d.]+)", url)
    if match:
        return {"lat": float(match.group(1)), "lng": float(match.group(2))}
    
    # Format 2: /place/...@lat,lng,zoom
    match = re.search(r"@([-\d.]+),([-\d.]+)", url)
    if match:
        return {"lat": float(match.group(1)), "lng": float(match.group(2))}
    
    return None


def ziyaret_rotasi(lead_listesi: list[dict] | None = None) -> list[dict]:
    """
    Lead'leri ziyaret rotasına çevir — Mudanya/Bursa odaklı.
    
    Lead'leri ilçeye göre grupla ve mantıklı bir rota oluştur:
      1. Mudanya → 2. Görükle → 3. Nilüfer → 4. Osmangazi → 5. Yıldırım
    
    Args:
        lead_listesi: Lead listesi (None = lead_listesi_hepsi.json'dan oku)
    
    Returns:
        Sıralanmış lead listesi (her lead'e rota_sirasi, tahmini_mesafe eklendi)
    """
    if lead_listesi is None:
        try:
            with open(LEAD_LISTESI) as f:
                data = json.load(f)
            lead_listesi = data.get("leadler", [])
        except (FileNotFoundError, json.JSONDecodeError):
            print("✗ Lead listesi bulunamadı!", file=sys.stderr)
            return []
    
    if not lead_listesi:
        return []
    
    # Her lead'in konumunu analiz et
    for lead in lead_listesi:
        adres = lead.get("adres", "")
        konum = konum_bilgisi(adres)
        lead["_konum"] = konum
    
    # Rota sırası (ilçe öncelik sırası)
    rota_sirasi = {
        "Mudanya": 1,
        "Görükle": 2,
        "Nilüfer": 3,
        "Osmangazi": 4,
        "Yıldırım": 5,
    }
    
    def sirala(l):
        ilce = l.get("_konum", {}).get("ilce", "")
        return (rota_sirasi.get(ilce, 99), l.get("isim", ""))
    
    sirali = sorted(lead_listesi, key=sirala)
    
    # Rota bilgilerini ekle
    for i, lead in enumerate(sirali, 1):
        lead["rota_sirasi"] = i
        ilce = lead.get("_konum", {}).get("ilce", "Bilinmeyen")
        lead["rota_notu"] = f"{i}. {lead.get('isim', '')} ({ilce})"
    
    return sirali


# ── Durum / CLI ─────────────────────────────────────────────────────────────

def durum_kontrol() -> dict:
    """Tüm modüllerin durumunu döndür."""
    durum = {
        "modul": "DOKUNMA Motoru",
        "faz": 12,
        "motto": "Fiziksel dünyada ses",
        "tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "ses_modulu": {
            "kokoro_kurulu": _kokoro_kullanilabilir(),
            "jeff_speak_mevcut": (SCRIPTS / "jeff_speak.py").exists(),
            "ses_kayitlari_klasoru": str(SES_KAYITLARI),
            "ses_kayit_sayisi": len(list(SES_KAYITLARI.glob("*.*"))),
        },
        "whatsapp_modulu": {
            "mesaj_sablonlari": str(MESAJ_SABLONLARI),
            "sablonlar": list(MESAJ_SABLONLARI.glob("*.md")),
            "lead_listesi_mevcut": LEAD_LISTESI.exists(),
            "toplam_lead": _lead_sayisi_al(),
        },
        "fiziksel_dunya": {
            "bolgeler": list(BOLGE_KOORDINATLARI.keys()),
            "lead_listesi_dosyasi": str(LEAD_LISTESI),
        },
    }
    return durum


def _durum_yazdir():
    """Durumu insan okunabilir formatta yazdır."""
    d = durum_kontrol()
    print("═══════════════════════════════════════")
    print(f"  {d['modul']} — Faz {d['faz']}")
    print(f"  Motto: \"{d['motto']}\"")
    print(f"  Tarih: {d['tarih']}")
    print("═══════════════════════════════════════")
    
    ses = d["ses_modulu"]
    print(f"\n🎙️  Ses Modülü:")
    print(f"   Kokoro TTS: {'✅ Kurulu' if ses['kokoro_kurulu'] else '❌ Kurulu Değil'}")
    print(f"   jeff_speak: {'✅ Mevcut' if ses['jeff_speak_mevcut'] else '❌ Yok'}")
    print(f"   Ses Kayıtları: {ses['ses_kayitlari_klasoru']}")
    print(f"   Kayıt Sayısı: {ses['ses_kayit_sayisi']}")
    
    wa = d["whatsapp_modulu"]
    print(f"\n💬 WhatsApp Modülü:")
    print(f"   Mesaj Şablonları: {wa['mesaj_sablonlari']}")
    print(f"   Şablonlar: {', '.join(str(p.name) for p in wa['sablonlar']) if wa['sablonlar'] else '❌ Yok'}")
    print(f"   Lead Listesi: {'✅ Mevcut' if wa['lead_listesi_mevcut'] else '❌ Yok'}")
    print(f"   Toplam Lead: {wa['toplam_lead']}")
    
    fiz = d["fiziksel_dunya"]
    print(f"\n🌍 Fiziksel Dünya:")
    print(f"   Bölgeler: {', '.join(fiz['bolgeler'])}")
    print(f"   Lead Dosyası: {fiz['lead_listesi_dosyasi']}")


# ── Ana CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="DOKUNMA Motoru — Fiziksel Dünyada Ses (Faz 12)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modüller:
  🎙️  Ses:        --ses "metin" | --sabah-ses
  💬  WhatsApp:   --mesaj "lead" --tip demo|teklif|randevu
  🌍  Fiziksel:   --rota | --konum "adres"
  📊  Durum:      --durum

Örnekler:
  python3 dokunma_motoru.py --ses "Merhaba dünya"
  python3 dokunma_motoru.py --sabah-ses
  python3 dokunma_motoru.py --mesaj "İbrahim Erayhan" --tip demo
  python3 dokunma_motoru.py --rota
  python3 dokunma_motoru.py --konum "Konur Hastanesi, Osmangazi, Bursa"
  python3 dokunma_motoru.py --gps "https://www.google.com/maps?q=40.3753,28.8826"
  python3 dokunma_motoru.py --durum
        """
    )
    
    # Ses modülü
    parser.add_argument("--ses", type=str, metavar="METIN",
                        help="Metni seslendir (Kokoro TTS → fallback)")
    parser.add_argument("--ses-tonu", type=str, default="jeff",
                        choices=["jeff", "adam", "michael", "onyx", "fenrir", "puck"],
                        help="Ses tonu (varsayılan: jeff)")
    parser.add_argument("--sabah-ses", action="store_true",
                        help="Sabah brifingini seslendir")
    
    # WhatsApp modülü
    parser.add_argument("--mesaj", type=str, metavar="LEAD_ADI",
                        help="Lead için mesaj hazırla")
    parser.add_argument("--tip", type=str, default="demo",
                        choices=["demo", "teklif", "randevu"],
                        help="Mesaj tipi (varsayılan: demo)")
    
    # Fiziksel dünya
    parser.add_argument("--rota", action="store_true",
                        help="Ziyaret rotası çıkar")
    parser.add_argument("--konum", type=str, metavar="ADRES",
                        help="Adres analizi yap")
    parser.add_argument("--gps", type=str, metavar="URL",
                        help="Google Maps URL'sinden GPS koordinat çıkar")
    
    # Durum
    parser.add_argument("--durum", action="store_true",
                        help="Modül durumunu göster")
    
    args = parser.parse_args()
    
    # ── Ses modülü ───────────────────────────────────────────────────────
    if args.ses:
        dosya = seslendir(args.ses, ses_tonu=args.ses_tonu)
        if dosya:
            print(f"\n✅ Ses hazır → MEDIA:{dosya}")
        else:
            print("\n❌ Ses oluşturulamadı.")
        return
    
    if args.sabah_ses:
        dosya = sabah_brifingi_ses()
        if dosya:
            print(f"\n✅ Sabah brifingi hazır → MEDIA:{dosya}")
        else:
            print("\n❌ Brifing seslendirilemedi.")
        return
    
    # ── WhatsApp modülü ─────────────────────────────────────────────────
    if args.mesaj:
        sonuc = mesaj_hazirla(args.mesaj, args.tip)
        if "hata" in sonuc:
            print(f"\n❌ {sonuc['hata']}")
            return
        
        print("\n" + "═" * 55)
        print(f"  📨 Mesaj Hazır: {sonuc['mesaj_tipi'].upper()}")
        print(f"  📋 Lead: {sonuc['lead']}")
        print(f"  📞 Telefon: {sonuc['telefon']}")
        print("═" * 55)
        print(f"\n{sonuc['mesaj']}")
        print("\n" + "─" * 55)
        print(f"🔗 WhatsApp Linki:")
        print(f"   {sonuc['whatsapp_link']}")
        return
    
    # ── Fiziksel Dünya ──────────────────────────────────────────────────
    if args.rota:
        rota = ziyaret_rotasi()
        if not rota:
            print("\n❌ Rota oluşturulamadı — lead listesi boş veya bulunamadı.")
            return
        
        print("\n" + "═" * 55)
        print("  🗺️  ZİYARET ROTASI")
        print("═" * 55)
        for lead in rota:
            konum = lead.get("_konum", {})
            ilce = konum.get("ilce", "?")
            maps = konum.get("google_maps", "")
            print(f"\n  {lead['rota_sirasi']}. {lead['isim']}")
            print(f"     📍 {lead.get('adres', 'Adres yok')} ({ilce})")
            if maps:
                print(f"     🗺️  {maps}")
        print("\n" + "─" * 55)
        print(f"  Toplam: {len(rota)} lead")
        return
    
    if args.konum:
        sonuc = konum_bilgisi(args.konum)
        print("\n" + "═" * 55)
        print("  📍 KONUM ANALİZİ")
        print("═" * 55)
        print(f"  Adres: {sonuc['adres']}")
        print(f"  İlçe:  {sonuc['ilce'] or 'Tespit edilemedi'}")
        print(f"  Şehir: {sonuc['sehir'] or 'Tespit edilemedi'}")
        if sonuc['koordinat']:
            print(f"  Koordinat: {sonuc['koordinat']['lat']}, {sonuc['koordinat']['lng']}")
        print(f"  🗺️  {sonuc['google_maps']}")
        return
    
    if args.gps:
        sonuc = gps_koordinat_cikarimi(args.gps)
        if sonuc:
            print(f"\n✅ GPS Koordinat: {sonuc['lat']}, {sonuc['lng']}")
            print(f"   🗺️  https://www.google.com/maps?q={sonuc['lat']},{sonuc['lng']}")
        else:
            print("\n❌ Koordinat çıkarılamadı.")
        return
    
    # ── Durum ────────────────────────────────────────────────────────────
    if args.durum:
        _durum_yazdir()
        return
    
    # ── Varsayılan: yardım ───────────────────────────────────────────────
    parser.print_help()


if __name__ == "__main__":
    main()
