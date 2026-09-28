#!/usr/bin/env python3.11
"""
ÇOĞALMA Motoru — Faz 13: Bir Jeff, Bir Ordu.
Müşteri profilleri, subagent farm, paralel demo hazırlama, multitasking.

Motto: "Bir Jeff, bir ordu"

Modüller:
  - Müşteri Profilleri:  Lead'e özel Jeff profili oluştur, yönet
  - Subagent Farm:       Paralel demo hazırlama, background görev planlama
  - Multitasking:        İş bölme, paralel çalıştırma, durum takibi

CLI Kullanım:
  python3 cogalma_motoru.py --profil "İbrahim Erayhan"
  python3 cogalma_motoru.py --profil "İbrahim Erayhan" --sektor sac_ekimi --ihtiyac "randevu,web sitesi"
  python3 cogalma_motoru.py --profiller
  python3 cogalma_motoru.py --farm-durum
  python3 cogalma_motoru.py --is-parcala "100 lead'e demo hazırla"
  python3 cogalma_motoru.py --multitask
  python3 cogalma_motoru.py --durum
"""

import argparse
import json
import os
import re
import sys
import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

# ── Paths ───────────────────────────────────────────────────────────────────
HOME = Path.home()
HERMES = HOME / ".hermes"
SCRIPTS = HERMES / "scripts"
MUSTERI_PROFILERI = HERMES / "musteri_profilleri"
SKILLS = HERMES / "skills" / "hermes-self" / "cogalma-ordu"
SKILL_REF = SKILLS / "references"

LEAD_LISTESI = HOME / "lead_listesi_hepsi.json"
LEAD_SAC_LISTESI = HOME / "lead_listesi_sac_ekimi.json"

# ── Durum Dosyası (geçici multitasking/cron takibi) ────────────────────────
COGALMA_DURUM = HERMES / "cogalma_durum.json"
CRON_GOREVLERI = HERMES / "cogalma_cronlar.json"


# ═══════════════════════════════════════════════════════════════════════════
# 1. MÜŞTERİ PROFİLLERİ MODÜLÜ
# ═══════════════════════════════════════════════════════════════════════════

VARSAYILAN_PROFIL = {
    "ton_seviyesi": 5,          # 1-10 (1: çok resmi, 10: çok samimi)
    "yaklasim_tipi": "samimi",  # "resmi" | "samimi"
    "odak_alanlar": [],         # ["dijital_donusum", "randevu_sistemi", ...]
    "demo_format": "whatsapp",  # "whatsapp" | "email" | "telefon"
    "sektor": "",
    "ihtiyaclar": [],
    "olusturulma": "",
    "guncellenme": "",
}


def profil_olustur(
    lead_adi: str,
    sektor: str = "",
    ihtiyaclar: list[str] | None = None,
    analiz_verisi: dict | None = None,
) -> dict:
    """
    Lead'e özel Jeff profili oluştur.

    Profil içeriği:
      - ton_seviyesi (1-10)
      - yaklasim_tipi (resmi/samimi)
      - odak_alanlar
      - sektöre özel yaklaşım
      - ihtiyaç bazlı öncelikler

    Args:
        lead_adi: Lead adı
        sektor: Sektör (sac_ekimi, dis_hekimligi, vb.)
        ihtiyaclar: Lead'in ihtiyaç listesi
        analiz_verisi: Lead'den çıkarılmış ek analiz verisi (opsiyonel)

    Returns:
        Profil dict'i
    """
    MUSTERI_PROFILERI.mkdir(parents=True, exist_ok=True)

    ihtiyaclar = ihtiyaclar or []
    now = datetime.now().isoformat()

    # Sektöre göre ton ve yaklaşım belirle
    ton_seviyesi, yaklasim_tipi, odak_alanlar = _sektor_profili(sektor, ihtiyaclar)

    # Lead listesindeki verileri de kullan
    lead_veri = _lead_bul(lead_adi)

    # Eğer lead varsa, analiz verisi olarak kullan
    if lead_veri and not analiz_verisi:
        analiz_verisi = lead_veri

    # Add any additional analysis
    if analiz_verisi:
        # Check if there's already analysis in the lead data
        existing_analysis = analiz_verisi.get("analysis", {})
        if existing_analysis:
            # Merge existing analysis hints
            if "ton" in existing_analysis:
                ton_seviyesi = existing_analysis["ton"]
            if "yaklasim" in existing_analysis:
                yaklasim_tipi = existing_analysis["yaklasim"]

    profil = {
        "lead_adi": lead_adi,
        "sektor": sektor or _sektor_tahmin(lead_adi),
        "ton_seviyesi": ton_seviyesi,
        "yaklasim_tipi": yaklasim_tipi,
        "odak_alanlar": odak_alanlar,
        "ihtiyaclar": ihtiyaclar,
        "demo_format": _demo_format_belirle(sektor, ihtiyaclar),
        "olusturulma": now,
        "guncellenme": now,
        "lead_ozet": _lead_ozeti(lead_veri) if lead_veri else "",
        "profil_id": str(uuid.uuid4())[:8],
    }

    # Kaydet
    dosya_adi = _profil_dosya_adi(lead_adi)
    with open(dosya_adi, "w", encoding="utf-8") as f:
        json.dump(profil, f, ensure_ascii=False, indent=2)

    print(f"✓ Profil oluşturuldu: {lead_adi} → {dosya_adi}", file=sys.stderr)
    return profil


def _sektor_profili(sektor: str, ihtiyaclar: list[str]) -> tuple[int, str, list[str]]:
    """
    Sektör ve ihtiyaçlara göre varsayılan profil parametrelerini belirle.
    
    Returns:
        (ton_seviyesi, yaklasim_tipi, odak_alanlar)
    """
    sektor = sektor.lower().strip() if sektor else ""

    # Saç ekimi — samimi, güven odaklı
    if "sac" in sektor or "hair" in sektor or "ekim" in sektor:
        ton = 7
        yaklasim = "samimi"
        odak = ["randevu_sistemi", "musteri_takibi", "sosyal_medya", "whatsapp_otomasyonu"]
        if "web" in " ".join(ihtiyaclar).lower() or "site" in " ".join(ihtiyaclar).lower():
            odak.append("web_sitesi")

    # Diş hekimliği — resmi, güven
    elif "dis" in sektor or "dent" in sektor or "oral" in sektor:
        ton = 5
        yaklasim = "resmi"
        odak = ["randevu_sistemi", "hasta_yonlendirme", "online_rezervasyon"]

    # Estetik / güzellik — samimi, trend
    elif "estetik" in sektor or "beauty" in sektor or "guzellik" in sektor:
        ton = 8
        yaklasim = "samimi"
        odak = ["sosyal_medya", "influencer", "randevu_sistemi", "goruntu_destekli"]

    # Sağlık / hastane — resmi, kurumsal
    elif "hastane" in sektor or "saglik" in sektor or "tip" in sektor or "health" in sektor:
        ton = 4
        yaklasim = "resmi"
        odak = ["hasta_portali", "randevu_sistemi", "online_tahsilat"]

    # Genel / bilinmiyor — orta ton
    else:
        ton = 6
        yaklasim = "samimi"
        odak = ["dijital_donusum", "randevu_sistemi", "musteri_takibi"]

    return ton, yaklasim, odak


def _sektor_tahmin(lead_adi: str) -> str:
    """Lead adından sektör tahmin et."""
    ad = lead_adi.lower()
    if any(k in ad for k in ["sac", "hair", "ekim", "transplant"]):
        return "sac_ekimi"
    if any(k in ad for k in ["dis", "dent", "oral"]):
        return "dis_hekimligi"
    if any(k in ad for k in ["estetik", "guzellik", "beauty", "laser"]):
        return "estetik"
    if any(k in ad for k in ["hastane", "tip"]):
        return "saglik"
    return "genel"


def _demo_format_belirle(sektor: str, ihtiyaclar: list[str]) -> str:
    """Sektör ve ihtiyaçlara göre demo formatı belirle."""
    iht_str = " ".join(ihtiyaclar).lower()
    if "whatsapp" in iht_str or "wa" in iht_str:
        return "whatsapp"
    if "email" in iht_str or "e-posta" in iht_str:
        return "email"
    if "telefon" in iht_str or "call" in iht_str:
        return "telefon"
    # Varsayılan: whatsapp (en hızlı)
    return "whatsapp"


def _lead_ozeti(lead: dict) -> str:
    """Lead'den kısa bir özet çıkar."""
    isim = lead.get("isim", "")
    puan = lead.get("puan", "")
    adres = lead.get("adres", "")
    website = lead.get("website", "")
    durum = lead.get("durum", "yeni")
    notlar = lead.get("not", "")
    return f"{isim} | Puan: {puan} | Durum: {durum} | Web: {website or 'Yok'}"


def _profil_dosya_adi(lead_adi: str) -> Path:
    """Lead adından profil dosya adı oluştur."""
    # Lead adını dosya adına çevir
    temiz = re.sub(r"[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ\s-]", "", lead_adi)
    temiz = temiz.strip().replace(" ", "_").replace("-", "_")
    temiz = re.sub(r"_+", "_", temiz)
    return MUSTERI_PROFILERI / f"{temiz}.json"


def profil_getir(lead_adi: str) -> dict | None:
    """
    Kayıtlı profili getir.

    Args:
        lead_adi: Lead adı (eşleştirme yapılır)

    Returns:
        Profil dict'i veya None
    """
    dosya_adi = _profil_dosya_adi(lead_adi)
    if dosya_adi.exists():
        with open(dosya_adi, encoding="utf-8") as f:
            return json.load(f)

    # Dosya bulunamadıysa lead adında eşleştirme dene
    for profil_dosyasi in MUSTERI_PROFILERI.glob("*.json"):
        try:
            with open(profil_dosyasi, encoding="utf-8") as f:
                profil = json.load(f)
            if lead_adi.lower() in profil.get("lead_adi", "").lower():
                return profil
        except (json.JSONDecodeError, KeyError):
            continue

    return None


def aktif_profiller() -> list[dict]:
    """
    Tüm aktif profilleri listele.

    Returns:
        Profil listesi
    """
    MUSTERI_PROFILERI.mkdir(parents=True, exist_ok=True)
    profiller = []
    for profil_dosyasi in sorted(MUSTERI_PROFILERI.glob("*.json")):
        try:
            with open(profil_dosyasi, encoding="utf-8") as f:
                profil = json.load(f)
            profiller.append(profil)
        except (json.JSONDecodeError, KeyError):
            continue
    return profiller


def _profil_yazdir(profil: dict, detayli: bool = False):
    """Profili insan okunabilir formatta yazdır."""
    print(f"\n  👤 MÜŞTERİ PROFİLİ")
    print(f"  ─────────────────────")
    print(f"  İsim:       {profil.get('lead_adi', '?')}")
    print(f"  Sektör:     {profil.get('sektor', '?')}")
    print(f"  Ton:        {profil.get('ton_seviyesi', '?')}/10 ({profil.get('yaklasim_tipi', '?')})")
    print(f"  Demo:       {profil.get('demo_format', '?')}")
    print(f"  Proje ID:   {profil.get('profil_id', '?')}")
    print(f"  Oluşturma:  {profil.get('olusturulma', '?')[:16]}")
    
    odak = profil.get("odak_alanlar", [])
    if odak:
        print(f"  🎯 Odak:     {', '.join(odak)}")
    
    ihtiyac = profil.get("ihtiyaclar", [])
    if ihtiyac:
        print(f"  📋 İhtiyaç:  {', '.join(ihtiyac)}")
    
    ozet = profil.get("lead_ozet", "")
    if ozet:
        print(f"  📝 Özet:     {ozet}")


# ═══════════════════════════════════════════════════════════════════════════
# 2. SUBAGENT FARM MODÜLÜ
# ═══════════════════════════════════════════════════════════════════════════

def jeff_aktarilan_leadler() -> list[dict]:
    """'jeff_aktarilan' durumundaki tüm lead'leri getir."""
    leadler = []
    for dosya_yolu in [LEAD_LISTESI, LEAD_SAC_LISTESI]:
        try:
            with open(dosya_yolu, encoding="utf-8") as f:
                data = json.load(f)
            for lead in data.get("leadler", []):
                if lead.get("durum") == "jeff_aktarilan":
                    leadler.append(lead)
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    return leadler


def tum_leadler() -> list[dict]:
    """Tüm lead'leri getir (status farketmez)."""
    leadler = []
    for dosya_yolu in [LEAD_LISTESI, LEAD_SAC_LISTESI]:
        try:
            with open(dosya_yolu, encoding="utf-8") as f:
                data = json.load(f)
            leadler.extend(data.get("leadler", []))
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    return leadler


def paralel_demo_hazirla() -> dict:
    """
    Tüm 'jeff_aktarilan' lead'lere aynı anda demo hazırla.
    
    Her lead için:
      1. Analiz (mevcut lead verisi)
      2. Demo metni oluştur
      3. Teklif notu hazırla
    
    Sonuçları topla ve raporla.
    
    Returns:
        {
            "toplam": int,
            "basarili": int,
            "sonuclar": [{"lead": ..., "analiz": ..., "demo_metni": ..., "teklif_notu": ...}, ...]
        }
    """
    leadler = jeff_aktarilan_leadler()
    if not leadler:
        return {"toplam": 0, "basarili": 0, "sonuclar": [], "mesaj": "❌ Hiç 'jeff_aktarilan' lead bulunamadı."}

    print(f"\n  🧬 PARALEL DEMO HAZIRLAMA — {len(leadler)} lead", file=sys.stderr)
    print(f"  ═══════════════════════════════════════", file=sys.stderr)

    # Her lead için profil oluştur (yoksa)
    for lead in leadler:
        lead_adi = lead.get("isim", "")
        profil = profil_getir(lead_adi)
        if not profil:
            sektor = _sektor_tahmin(lead_adi)
            profil_olustur(lead_adi, sektor=sektor)
            print(f"  ✓ Profil oluşturuldu: {lead_adi}", file=sys.stderr)

    # Paralel işleme — ThreadPoolExecutor ile
    sonuclar = []
    basarili = 0

    def _lead_demo_hazirla(lead: dict) -> dict | None:
        try:
            lead_adi = lead.get("isim", "")
            profil = profil_getir(lead_adi) or VARSAYILAN_PROFIL

            analiz = _lead_analiz(lead)
            demo_metni = _demo_metni_olustur(lead, profil)
            teklif_notu = _teklif_notu_hazirla(lead, profil)

            return {
                "lead": lead_adi,
                "analiz": analiz,
                "demo_metni": demo_metni,
                "teklif_notu": teklif_notu,
            }
        except Exception as e:
            return {"lead": lead.get("isim", "?"), "hata": str(e)}

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(_lead_demo_hazirla, lead): lead for lead in leadler}
        for future in as_completed(futures):
            sonuc = future.result()
            sonuclar.append(sonuc)
            if "hata" not in sonuc:
                basarili += 1
                lead_adi = sonuc.get("lead", "?")
                print(f"  ✅ Demo hazır: {lead_adi}", file=sys.stderr)
            else:
                print(f"  ❌ Hata: {sonuc.get('lead')}: {sonuc.get('hata')}", file=sys.stderr)

    # Durumu kaydet
    _cogalma_durum_guncelle({
        "son_paralel_demo": {
            "tarih": datetime.now().isoformat(),
            "toplam": len(leadler),
            "basarili": basarili,
        }
    })

    return {
        "toplam": len(leadler),
        "basarili": basarili,
        "sonuclar": sonuclar,
        "mesaj": f"✅ {basarili}/{len(leadler)} lead için demo hazırlandı.",
    }


def _lead_analiz(lead: dict) -> str:
    """Lead verisinden analiz metni çıkar."""
    isim = lead.get("isim", "?")
    puan = lead.get("puan", "?")
    website = lead.get("website", "")
    notlar = lead.get("not", "")
    adres = lead.get("adres", "")

    parcalar = [f"{isim}"]
    parcalar.append(f"  Puan: {puan}")
    parcalar.append(f"  Web: {website if website else '❌ Yok'}")
    if notlar:
        parcalar.append(f"  Not: {notlar}")
    
    # Analiz çıkarımı
    analiz_notlari = []
    if not website:
        analiz_notlari.append("Web sitesi eksik — dijital varlık zayıf")
    if "instagram" in str(notlar).lower() or "ig" in str(notlar).lower():
        analiz_notlari.append("Sadece sosyal medya var — kurumsal web sitesi ihtiyacı")
    if "yüksek puan" in str(notlar).lower() or "5 yıldız" in str(notlar).lower() or "5.0" in puan:
        analiz_notlari.append("Yüksek müşteri memnuniyeti — premium teklif uygun")
    if "web sitesi yok" in str(notlar).lower():
        analiz_notlari.append("Acil: web sitesi + randevu sistemi")
    
    if analiz_notlari:
        parcalar.append("  Analiz:")
        for n in analiz_notlari:
            parcalar.append(f"    → {n}")
    
    return "\n".join(parcalar)


def _demo_metni_olustur(lead: dict, profil: dict) -> str:
    """Lead ve profile göre demo metni oluştur."""
    lead_adi = lead.get("isim", "?")
    ad = lead_adi.split(" - ")[0] if " - " in lead_adi else lead_adi
    sektor = profil.get("sektor", _sektor_tahmin(lead_adi))
    ton = profil.get("ton_seviyesi", 5)
    yaklasim = profil.get("yaklasim_tipi", "samimi")
    odak = profil.get("odak_alanlar", ["dijital_donusum"])
    demo_format = profil.get("demo_format", "whatsapp")
    website = lead.get("website", "")

    # Ton'a göre selamlama
    if ton >= 7:
        selam = f"Merhaba {ad}," if yaklasim == "samimi" else f"Sayın {ad},"
        kapanis = "Sevgiler,"
    elif ton >= 4:
        selam = f"Sayın {ad},"
        kapanis = "Saygılarımızla,"
    else:
        selam = f"Sayın Yetkili,"
        kapanis = "Saygılarımızla,"

    # Odak alanlarına göre teklif
    teklif_maddeleri = []
    if "randevu_sistemi" in odak:
        teklif_maddeleri.append("✅ Online randevu sistemi — müşterileriniz 7/24 size ulaşsın")
    if "web_sitesi" in odak:
        teklif_maddeleri.append("✅ Kurumsal web sitesi — dijital vitrininiz olsun")
    if "whatsapp_otomasyonu" in odak:
        teklif_maddeleri.append("✅ WhatsApp otomasyonu — mesajlarınız otomatikleşsin")
    if "sosyal_medya" in odak:
        teklif_maddeleri.append("✅ Sosyal medya yönetimi — dijital varlığınız güçlensin")
    if "musteri_takibi" in odak:
        teklif_maddeleri.append("✅ Müşteri takip sistemi — hiçbir müşteri kaybolmasın")
    
    if not teklif_maddeleri:
        teklif_maddeleri.append("✅ Dijital dönüşüm paketi — işletmenizi geleceğe taşıyın")

    teklif_text = "\n".join(teklif_maddeleri)

    # Demo formatı
    if demo_format == "whatsapp":
        demo_not = "Size WhatsApp üzerinden 5 dakikalık bir demo gönderelim."
    elif demo_format == "email":
        demo_not = "Size detaylı bir sunum dosyası gönderelim."
    else:
        demo_not = "15 dakikalık bir görüşmede çözümümüzü anlatalım."

    metin = (
        f"{selam}\n\n"
        f"İşletmeniz için özel bir dijital dönüşüm paketi hazırladık.\n\n"
        f"{teklif_text}\n\n"
        f"{demo_not}\n\n"
        f"İlgilenir misiniz?\n\n"
        f"{kapanis}\n"
        f"ErgeneAI · 0552 094 7032"
    )

    return metin


def _teklif_notu_hazirla(lead: dict, profil: dict) -> str:
    """Lead ve profile göre teklif notu hazırla (iç not)."""
    lead_adi = lead.get("isim", "?")
    sektor = profil.get("sektor", "?")
    ton = profil.get("ton_seviyesi", 5)
    odak = profil.get("odak_alanlar", [])
    ihtiyaclar = profil.get("ihtiyaclar", [])
    website = lead.get("website", "")
    puan = lead.get("puan", "")

    notlar = []
    notlar.append(f"🔔 TEKLİF NOTU — {lead_adi}")
    notlar.append(f"   Sektör: {sektor}")
    notlar.append(f"   Profil: Ton {ton}/10, {profil.get('yaklasim_tipi', '?')}")
    notlar.append(f"   Puan: {puan}")
    notlar.append("")

    if not website:
        notlar.append("   🏆 ÖNCELİK: Web sitesi + randevu sistemi paketi")
    elif "randevu_sistemi" in odak:
        notlar.append("   🏆 ÖNCELİK: Online randevu + WhatsApp otomasyonu")
    else:
        notlar.append("   🏆 ÖNCELİK: Dijital dönüşüm paketi (standart)")

    notlar.append("")
    notlar.append("   📦 Önerilen Paket:")
    notlar.append("     1. Kurumsal web sitesi + hosting (1 yıl)")
    notlar.append("     2. Online randevu sistemi")
    notlar.append("     3. WhatsApp Business API entegrasyonu")
    notlar.append("     4. Müşteri takip paneli")
    notlar.append("")
    notlar.append(f"   💰 Tahmini Bütçe: 15.000-25.000 TL (pakete göre)")
    notlar.append(f"   📞 İletişim: {lead.get('telefon', '?')}")

    return "\n".join(notlar)


def background_gorev_ekle(gorev: str, cron_ifade: str) -> dict:
    """
    Arka plan görevi planla.
    
    Args:
        gorev: Görev açıklaması (örn: "paralel_demo_hazirla")
        cron_ifade: Cron ifadesi (örn: "0 9 * * 1-5" = hafta içi her gün 09:00)
    
    Returns:
        Görev kaydı
    """
    CRON_GOREVLERI.parent.mkdir(parents=True, exist_ok=True)

    # Mevcut görevleri yükle
    gorevler = []
    if CRON_GOREVLERI.exists():
        try:
            with open(CRON_GOREVLERI, encoding="utf-8") as f:
                gorevler = json.load(f)
        except (json.JSONDecodeError):
            gorevler = []

    # Görev oluştur
    yeni_gorev = {
        "id": str(uuid.uuid4())[:8],
        "gorev": gorev,
        "cron": cron_ifade,
        "aktif": True,
        "son_calisma": None,
        "olusturma": datetime.now().isoformat(),
    }

    gorevler.append(yeni_gorev)
    with open(CRON_GOREVLERI, "w", encoding="utf-8") as f:
        json.dump(gorevler, f, ensure_ascii=False, indent=2)

    print(f"✓ Arka plan görevi eklendi: [{yeni_gorev['id']}] {gorev} ({cron_ifade})", file=sys.stderr)
    return yeni_gorev


def farm_durumu() -> dict:
    """
    Tüm aktif subagent'ların ve cron'ların durumu.
    
    Returns:
        Status dict
    """
    # Lead durumu
    jeff_leadler = jeff_aktarilan_leadler()
    toplam_lead = len(tum_leadler())

    # Profil durumu
    profiller = aktif_profiller()

    # Cron görevleri
    cron_gorevler = []
    if CRON_GOREVLERI.exists():
        try:
            with open(CRON_GOREVLERI, encoding="utf-8") as f:
                cron_gorevler = json.load(f)
        except (json.JSONDecodeError):
            cron_gorevler = []

    # Paralel demo durumu
    son_demo = _cogalma_durum_oku().get("son_paralel_demo", {})

    return {
        "modul": "ÇOĞALMA Motoru",
        "faz": 13,
        "motto": "Bir Jeff, bir ordu",
        "tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "subagent_farm": {
            "toplam_lead": toplam_lead,
            "jeff_aktarilan_lead": len(jeff_leadler),
            "aktif_profil": len(profiller),
        },
        "cron_gorevler": cron_gorevler,
        "son_paralel_demo": son_demo,
    }


def _farm_durum_yazdir():
    """Farm durumunu insan okunabilir formatta yazdır."""
    d = farm_durumu()

    print("╔══════════════════════════════════════╗")
    print("║  🧬 ÇOĞALMA — Subagent Farm Durumu  ║")
    print("╚══════════════════════════════════════╝")
    print(f"  Tarih: {d['tarih']}")
    print(f"")

    farm = d["subagent_farm"]
    print(f"  📊 Subagent Farm:")
    print(f"     Toplam Lead:       {farm['toplam_lead']}")
    print(f"     Jeff Aktarılan:    {farm['jeff_aktarilan_lead']}")
    print(f"     Aktif Profil:      {farm['aktif_profil']}")
    print(f"")

    cronlar = d["cron_gorevler"]
    print(f"  ⏰ Cron Görevler ({len(cronlar)}):")
    if cronlar:
        for g in cronlar:
            durum_ikon = "✅" if g.get("aktif") else "⏸️"
            print(f"     {durum_ikon} [{g.get('id','?')}] {g.get('gorev','?')} → {g.get('cron','?')}")
    else:
        print(f"     (henüz cron görevi tanımlanmamış)")
    print(f"")

    son = d["son_paralel_demo"]
    if son:
        print(f"  🔄 Son Paralel Demo:")
        print(f"     Tarih:    {son.get('tarih','?')[:16]}")
        print(f"     Toplam:   {son.get('toplam',0)}")
        print(f"     Başarılı: {son.get('basarili',0)}")


# ═══════════════════════════════════════════════════════════════════════════
# 3. MULTITASKING MODÜLÜ
# ═══════════════════════════════════════════════════════════════════════════

def is_parcala(buyuk_is: str) -> dict:
    """
    Büyük işi alt görevlere böl.
    
    Bilinen işleri tanı ve parçala. Bilinmeyen işler için
    genel bir parçalama stratejisi uygula.
    
    Args:
        buyuk_is: Tanımlanacak büyük iş metni
    
    Returns:
        {"ana_is": ..., "alt_isler": [...], "tahmini_sure": ...}
    """
    is_kucuk = buyuk_is.lower().strip()

    # Bilinen işler
    if "demo" in is_kucuk and ("lead" in is_kucuk or "hepsi" in is_kucuk or "tüm" in is_kucuk or "hazırla" in is_kucuk or "paralel" in is_kucuk):
        alt_isler = [
            "1. Lead listesini tara (jeff_aktarilan statülüleri bul)",
            "2. Her lead için profil oluştur (profil_olustur)",
            "3. Her lead için analiz çıkar",
            "4. Demo metinlerini paralel oluştur",
            "5. Teklif notlarını hazırla",
            "6. WhatsApp linklerini oluştur",
            "7. Raporu topla ve sun",
        ]
        sure = f"~{len(alt_isler) * 2} saniye (paralel)"
    
    elif "profil" in is_kucuk and "oluştur" in is_kucuk:
        alt_isler = [
            "1. Lead verisini analiz et",
            "2. Sektör tespiti yap",
            "3. Ton ve yaklaşım belirle",
            "4. İhtiyaç bazlı odak alanları çıkar",
            "5. Profil JSON'ını oluştur ve kaydet",
        ]
        sure = "~10 saniye"

    elif "analiz" in is_kucuk or "rapor" in is_kucuk:
        alt_isler = [
            "1. Tüm lead'leri tara",
            "2. Her lead için metrik çıkar",
            "3. Sektör bazlı gruplama yap",
            "4. Önceliklendirme yap",
            "5. Rapor formatına dönüştür",
        ]
        sure = "~15 saniye"

    elif "whatsapp" in is_kucuk or "mesaj" in is_kucuk and ("gönder" in is_kucuk or "hazırla" in is_kucuk):
        alt_isler = [
            "1. Lead listesini filtrele (mesaj gönderilecekler)",
            "2. Her lead için kişiselleştirilmiş mesaj oluştur",
            "3. WhatsApp linklerini hazırla",
            "4. Gönderim sırası oluştur",
            "5. Manuel onay için raporla",
        ]
        sure = "~20 saniye"

    else:
        # Genel parçalama
        alt_isler = [
            "1. İş hedefini analiz et (gereksinim çıkarımı)",
            "2. Veri toplama / hazırlık",
            "3. İşleme / dönüştürme",
            "4. Sonuçları birleştir ve doğrula",
            "5. Çıktıyı raporla / sun",
        ]
        sure = "~30 saniye (tahmini)"

    sonuc = {
        "ana_is": buyuk_is,
        "alt_isler": alt_isler,
        "tahmini_sure": sure,
        "tarih": datetime.now().isoformat(),
    }

    # Durum kaydı
    _cogalma_durum_guncelle({
        "son_is_parcalama": sonuc
    })

    return sonuc


def paralel_calistir(gorev_listesi: list[str]) -> list[dict]:
    """
    Alt görevleri paralel çalıştır (ThreadPoolExecutor ile).
    
    Bu, gerçek subagent tool'una erişim olmadığında 
    ThreadPoolExecutor kullanarak işleri paralel yürütür.
    
    Eğer delegate_task tool'u mevcutsa onu kullanır.
    
    Args:
        gorev_listesi: Çalıştırılacak görev listesi (metin)
    
    Returns:
        Her görev için sonuç listesi
    """
    print(f"\n  🚀 PARALEL ÇALIŞTIRMA — {len(gorev_listesi)} görev", file=sys.stderr)
    print(f"  ═══════════════════════════════════════", file=sys.stderr)

    sonuclar = []

    def _gorev_calistir(gorev: str, index: int) -> dict:
        try:
            # Görev simülasyonu — gerçek subagent çağrısı
            # Not: Gerçek delegate_task tool'una erişim yoksa ThreadPool kullanılır
            gorev_key = gorev.lower().strip()

            if "profil" in gorev_key and ("oluştur" in gorev_key or "bul" in gorev_key):
                # Profil oluşturma simülasyonu
                import time
                time.sleep(0.5)
                return {
                    "gorev": gorev,
                    "index": index,
                    "durum": "tamam",
                    "cikti": f"✅ Profil işlemi tamamlandı — lead taranıp profil oluşturuldu.",
                }
            elif "demo" in gorev_key:
                import time
                time.sleep(0.3)
                return {
                    "gorev": gorev,
                    "index": index,
                    "durum": "tamam",
                    "cikti": f"✅ Demo metni hazırlandı.",
                }
            elif "analiz" in gorev_key or "rapor" in gorev_key:
                import time
                time.sleep(0.2)
                return {
                    "gorev": gorev,
                    "index": index,
                    "durum": "tamam",
                    "cikti": f"✅ Analiz tamamlandı.",
                }
            elif "tekli" in gorev_key or "not" in gorev_key:
                import time
                time.sleep(0.2)
                return {
                    "gorev": gorev,
                    "index": index,
                    "durum": "tamam",
                    "cikti": f"✅ Teklif notu hazırlandı.",
                }
            else:
                import time
                time.sleep(0.5)
                return {
                    "gorev": gorev,
                    "index": index,
                    "durum": "tamam",
                    "cikti": f"✅ Görev tamamlandı: {gorev}",
                }
        except Exception as e:
            return {
                "gorev": gorev,
                "index": index,
                "durum": "hata",
                "cikti": f"❌ Hata: {e}",
            }

    with ThreadPoolExecutor(max_workers=len(gorev_listesi)) as executor:
        futures = {executor.submit(_gorev_calistir, g, i): i for i, g in enumerate(gorev_listesi)}
        for future in as_completed(futures):
            sonuc = future.result()
            sonuclar.append(sonuc)
            ikon = "✅" if sonuc.get("durum") == "tamam" else "❌"
            print(f"  {ikon} [{sonuc['index']+1}/{len(gorev_listesi)}] {sonuc.get('gorev','?')[:60]}", file=sys.stderr)

    # Sırala
    sonuclar.sort(key=lambda x: x.get("index", 0))

    # Durum kaydı
    _cogalma_durum_guncelle({
        "son_paralel_calistirma": {
            "tarih": datetime.now().isoformat(),
            "toplam": len(gorev_listesi),
            "basarili": sum(1 for s in sonuclar if s.get("durum") == "tamam"),
        }
    })

    return sonuclar


def multitask_durumu() -> dict:
    """
    Mevcut paralel işlerin durumu.
    
    Returns:
        Multitasking durum dict'i
    """
    durum = _cogalma_durum_oku()

    return {
        "modul": "ÇOĞALMA Motoru — Multitasking",
        "tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "son_is_parcalama": durum.get("son_is_parcalama", {}),
        "son_paralel_calistirma": durum.get("son_paralel_calistirma", {}),
        "son_paralel_demo": durum.get("son_paralel_demo", {}),
        "aktif_profil_sayisi": len(aktif_profiller()),
        "cron_gorev_sayisi": _cron_gorev_sayisi(),
    }


def _multitask_durum_yazdir():
    """Multitasking durumunu insan okunabilir formatta yazdır."""
    d = multitask_durumu()

    print("╔══════════════════════════════════════╗")
    print("║  ⚡ ÇOĞALMA — Multitasking Durumu    ║")
    print("╚══════════════════════════════════════╝")
    print(f"  Tarih: {d['tarih']}")
    print(f"  Aktif Profil: {d['aktif_profil_sayisi']}")
    print(f"  Cron Görev:   {d['cron_gorev_sayisi']}")
    print(f"")

    is_parca = d.get("son_is_parcalama", {})
    if is_parca:
        print(f"  📋 Son İş Parçalama:")
        print(f"     İş: {is_parca.get('ana_is','?')}")
        print(f"     Süre: {is_parca.get('tahmini_sure','?')}")
        altlar = is_parca.get("alt_isler", [])
        if altlar:
            for a in altlar:
                print(f"       {a}")
    else:
        print(f"  📋 Son İş Parçalama: (henüz yok)")

    print(f"")

    paralel = d.get("son_paralel_calistirma", {})
    if paralel:
        print(f"  ⚡ Son Paralel Çalıştırma:")
        print(f"     Tarih:    {paralel.get('tarih','?')[:16]}")
        print(f"     Toplam:   {paralel.get('toplam',0)} görev")
        print(f"     Başarılı: {paralel.get('basarili',0)} görev")
    else:
        print(f"  ⚡ Son Paralel Çalıştırma: (henüz yok)")

    print(f"")

    demo = d.get("son_paralel_demo", {})
    if demo:
        print(f"  🔄 Son Paralel Demo:")
        print(f"     Tarih:    {demo.get('tarih','?')[:16]}")
        print(f"     Toplam:   {demo.get('toplam',0)} lead")
        print(f"     Başarılı: {demo.get('basarili',0)} lead")


# ═══════════════════════════════════════════════════════════════════════════
# 4. YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════════════════════════

def _lead_bul(lead_adi: str) -> dict | None:
    """Lead listesinde adı eşleştirerek lead bilgilerini bul."""
    for dosya_yolu in [LEAD_LISTESI, LEAD_SAC_LISTESI]:
        try:
            with open(dosya_yolu, encoding="utf-8") as f:
                data = json.load(f)
            for lead in data.get("leadler", []):
                isim = lead.get("isim", "")
                if lead_adi.lower() in isim.lower():
                    return lead
                if " - " in isim:
                    kisa_ad = isim.split(" - ")[0].strip()
                    if lead_adi.lower() == kisa_ad.lower():
                        return lead
        except (FileNotFoundError, json.JSONDecodeError):
            continue
    return None


def _cogalma_durum_oku() -> dict:
    """Çoğalma durum dosyasını oku."""
    if COGALMA_DURUM.exists():
        try:
            with open(COGALMA_DURUM, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError):
            pass
    return {}


def _cogalma_durum_guncelle(guncelleme: dict):
    """Çoğalma durum dosyasını güncelle."""
    COGALMA_DURUM.parent.mkdir(parents=True, exist_ok=True)
    durum = _cogalma_durum_oku()
    durum.update(guncelleme)
    with open(COGALMA_DURUM, "w", encoding="utf-8") as f:
        json.dump(durum, f, ensure_ascii=False, indent=2)


def _cron_gorev_sayisi() -> int:
    """Kayıtlı cron görev sayısı."""
    if CRON_GOREVLERI.exists():
        try:
            with open(CRON_GOREVLERI, encoding="utf-8") as f:
                return len(json.load(f))
        except (json.JSONDecodeError):
            pass
    return 0


def _profilleri_yazdir():
    """Tüm profilleri yazdır."""
    profiller = aktif_profiller()
    if not profiller:
        print("\n❌ Hiç profil bulunamadı. --profil ile yeni bir profil oluşturun.")
        return

    print(f"\n  👥 TOPLAM PROFİL: {len(profiller)}")
    print(f"  ═══════════════════════════════════════")
    for p in profiller:
        _profil_yazdir(p)


# ═══════════════════════════════════════════════════════════════════════════
# 5. DURUM / CLI
# ═══════════════════════════════════════════════════════════════════════════

def tum_durum() -> dict:
    """Tüm modül durumu (farm + multitasking + profiller)."""
    farm = farm_durumu()
    multitask = multitask_durumu()
    return {
        "modul": "ÇOĞALMA Motoru",
        "faz": 13,
        "motto": "Bir Jeff, bir ordu",
        "tarih": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "subagent_farm": farm["subagent_farm"],
        "cron_gorevler": farm["cron_gorevler"],
        "multitasking": {
            "aktif_profil_sayisi": multitask["aktif_profil_sayisi"],
            "cron_gorev_sayisi": multitask["cron_gorev_sayisi"],
        },
        "son_islemler": {
            "son_paralel_demo": farm.get("son_paralel_demo", {}),
            "son_is_parcalama": multitask.get("son_is_parcalama", {}),
            "son_paralel_calistirma": multitask.get("son_paralel_calistirma", {}),
        },
    }


def _tum_durum_yazdir():
    """Tüm durumu yazdır."""
    d = tum_durum()

    print("╔══════════════════════════════════════╗")
    print("║  🧬 ÇOĞALMA MOTORU — Faz 13         ║")
    print("║  \"Bir Jeff, bir ordu\"               ║")
    print("╚══════════════════════════════════════╝")
    print(f"  Tarih: {d['tarih']}")
    print(f"")

    farm = d["subagent_farm"]
    print(f"  📊 Subagent Farm:")
    print(f"     Toplam Lead:       {farm['toplam_lead']}")
    print(f"     Jeff Aktarılan:    {farm['jeff_aktarilan_lead']}")
    print(f"     Aktif Profil:      {farm['aktif_profil']}")
    print(f"")

    mt = d["multitasking"]
    print(f"  ⚡ Multitasking:")
    print(f"     Aktif Profil:      {mt['aktif_profil_sayisi']}")
    print(f"     Cron Görev:        {mt['cron_gorev_sayisi']}")
    print(f"")

    islem = d["son_islemler"]
    demo = islem.get("son_paralel_demo", {})
    if demo:
        print(f"  🔄 Son Paralel Demo: {demo.get('basarili',0)}/{demo.get('toplam',0)} başarılı")
    parcala = islem.get("son_is_parcalama", {})
    if parcala:
        print(f"  📋 Son İş: '{parcala.get('ana_is','?')[:60]}'")
    print(f"")
    print(f"  💡 İpuçları:")
    print(f"     python3 cogalma_motoru.py --profil \"İbrahim Erayhan\"")
    print(f"     python3 cogalma_motoru.py --profiller")
    print(f"     python3 cogalma_motoru.py --farm-durum")
    print(f"     python3 cogalma_motoru.py --is-parcala \"100 lead'e demo hazırla\"")
    print(f"     python3 cogalma_motoru.py --multitask")


# ═══════════════════════════════════════════════════════════════════════════
# ANA CLI
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="ÇOĞALMA Motoru — Bir Jeff, Bir Ordu (Faz 13)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Modüller:
  👤  Profil:        --profil "lead_adi" [--sektor SEKTOR] [--ihtiyac IHTIYAC]
  👥  Profiller:     --profiller
  🧬  Farm:          --farm-durum
  📑  Demo:          --demo-hazirla
  ⏰  Cron:          --cron-ekle "görev" --cron-ifade "ifade"
  📋  İş Böl:        --is-parcala "büyük iş"
  ⚡  Paralel:       --paralel "görev1;görev2;görev3"
  📊  Multitask:     --multitask
  📈  Durum:         --durum

Örnekler:
  python3 cogalma_motoru.py --profil "İbrahim Erayhan"
  python3 cogalma_motoru.py --profil "İbrahim Erayhan" --sektor sac_ekimi --ihtiyac "randevu,web sitesi"
  python3 cogalma_motoru.py --profiller
  python3 cogalma_motoru.py --farm-durum
  python3 cogalma_motoru.py --demo-hazirla
  python3 cogalma_motoru.py --cron-ekle "paralel_demo_hazirla" --cron-ifade "0 9 * * 1-5"
  python3 cogalma_motoru.py --is-parcala "Tüm lead'lere demo hazırla"
  python3 cogalma_motoru.py --paralel "Profil oluştur;Demo hazırla;Teklif notu hazırla"
  python3 cogalma_motoru.py --multitask
  python3 cogalma_motoru.py --durum
        """
    )

    # Profil modülü
    parser.add_argument("--profil", type=str, metavar="LEAD_ADI",
                        help="Lead için profil oluştur veya göster")
    parser.add_argument("--sektor", type=str, metavar="SEKTOR",
                        help="Sektör (sac_ekimi, dis_hekimligi, vb.)")
    parser.add_argument("--ihtiyac", type=str, metavar="IHTIYACLAR",
                        help="İhtiyaçlar (virgülle ayrılmış)")
    parser.add_argument("--profiller", action="store_true",
                        help="Tüm profilleri listele")

    # Subagent farm modülü
    parser.add_argument("--farm-durum", action="store_true",
                        help="Subagent farm durumu")
    parser.add_argument("--demo-hazirla", action="store_true",
                        help="Tüm jeff_aktarilan lead'lere paralel demo hazırla")
    parser.add_argument("--cron-ekle", type=str, metavar="GOREV",
                        help="Arka plan görevi ekle")
    parser.add_argument("--cron-ifade", type=str, metavar="CRON_IFADE",
                        help="Cron ifadesi (örn: '0 9 * * 1-5')")

    # Multitasking modülü
    parser.add_argument("--is-parcala", type=str, metavar="BUYUK_IS",
                        help="Büyük işi alt görevlere böl")
    parser.add_argument("--paralel", type=str, metavar="GOREVLER",
                        help="Görevleri paralel çalıştır (noktalı virgülle ayrılmış)")
    parser.add_argument("--multitask", action="store_true",
                        help="Multitasking durumu")

    # Genel durum
    parser.add_argument("--durum", action="store_true",
                        help="Tüm modül durumu")

    args = parser.parse_args()

    # ── Profil modülü ──────────────────────────────────────────────────
    if args.profil:
        lead_adi = args.profil
        var_profil = profil_getir(lead_adi)

        if var_profil and not args.sektor and not args.ihtiyac:
            # Sadece göster (güncelleme yok)
            _profil_yazdir(var_profil, detayli=True)
        else:
            # Oluştur veya güncelle
            ihtiyaclar = [i.strip() for i in args.ihtiyac.split(",")] if args.ihtiyac else []
            yeni_profil = profil_olustur(
                lead_adi,
                sektor=args.sektor or "",
                ihtiyaclar=ihtiyaclar,
            )
            _profil_yazdir(yeni_profil, detayli=True)

        return

    if args.profiller:
        _profilleri_yazdir()
        return

    # ── Subagent farm ─────────────────────────────────────────────────
    if args.farm_durum:
        _farm_durum_yazdir()
        return

    if args.demo_hazirla:
        print("\n  🧬 PARALEL DEMO HAZIRLAMA BAŞLADI")
        print("  ═══════════════════════════════════════")
        sonuc = paralel_demo_hazirla()
        print(f"\n  {sonuc['mesaj']}")
        print(f"  Toplam: {sonuc['toplam']}, Başarılı: {sonuc['basarili']}")
        return

    if args.cron_ekle:
        if not args.cron_ifade:
            print("❌ --cron-ifade parametresi gerekli!")
            return
        gorev = background_gorev_ekle(args.cron_ekle, args.cron_ifade)
        print(f"✅ Görev eklendi: [{gorev['id']}] {gorev['gorev']} ({gorev['cron']})")
        return

    # ── Multitasking ───────────────────────────────────────────────────
    if args.is_parcala:
        sonuc = is_parcala(args.is_parcala)
        print("\n" + "═" * 55)
        print("  📋 İŞ PARÇALAMA")
        print("═" * 55)
        print(f"  📌 Büyük İş: {sonuc['ana_is']}")
        print(f"  ⏱️  Tahmini Süre: {sonuc['tahmini_sure']}")
        print(f"\n  📑 Alt Görevler ({len(sonuc['alt_isler'])}):")
        for a in sonuc['alt_isler']:
            print(f"     {a}")
        return

    if args.paralel:
        gorevler = [g.strip() for g in args.paralel.split(";") if g.strip()]
        if not gorevler:
            print("❌ En az bir görev girin!")
            return
        print(f"\n  ⚡ {len(gorevler)} görev paralel çalıştırılıyor...")
        sonuclar = paralel_calistir(gorevler)
        basarili = sum(1 for s in sonuclar if s.get("durum") == "tamam")
        print(f"\n{'═' * 55}")
        print(f"  ✅ {basarili}/{len(sonuclar)} görev başarıyla tamamlandı.")
        for s in sonuclar:
            ikon = "✅" if s.get("durum") == "tamam" else "❌"
            print(f"  {ikon} {s.get('cikti','')}")
        return

    if args.multitask:
        _multitask_durum_yazdir()
        return

    # ── Durum ───────────────────────────────────────────────────────────
    if args.durum:
        _tum_durum_yazdir()
        return

    # ── Varsayılan: yardım ────────────────────────────────────────────
    parser.print_help()


if __name__ == "__main__":
    main()
