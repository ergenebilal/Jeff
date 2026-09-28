#!/usr/bin/env python3
"""
ORTAKLIK MOTORU — Faz 8: Yol Arkadaşı
CTO Refleksi · Dış Temsil · Proje Yönetimi · İmza Yetkisi

Kullanım:
  python3 ortaklik_motoru.py --analiz "konu" [--baglam "bağlam"]
  python3 ortaklik_motoru.py --rapor "başlık" [--icerik "içerik"]
  python3 ortaklik_motoru.py --rapor-musteri "müşteri" --konu "konu"
  python3 ortaklik_motoru.py --proje --ad "proje adı" [--gorevler "görev1,görev2,..."]
  python3 ortaklik_motoru.py --gorev-ata --gorev "görev" --sorumlu "kişi" --proje "proje adı"
  python3 ortaklik_motoru.py --ilerleme --proje "proje adı"
  python3 ortaklik_motoru.py --yetki-kontrol --karar "karar metni"
  python3 ortaklik_motoru.py --imza-at --karar "karar metni"
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# ── Yollar ──────────────────────────────────────────────────────────────────
HOME = Path.home()
SCRIPTS_DIR = HOME / ".hermes" / "scripts"
ANALIZ_DOSYASI = HOME / ".hermes" / "stratejik_analizler" / "analizler.json"
RAPORLAR_DIR = HOME / ".hermes" / "raporlar"
PROJELER_DIR = HOME / ".hermes" / "projeler"
YETKI_MATRISI = HOME / ".hermes" / "skills" / "hermes-self" / "ortaklik-cto" / "references" / "yetki-matrisi.md"

# ── Yardımcılar ─────────────────────────────────────────────────────────────

def _tarih():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _analiz_dosyasini_yukle():
    """JSON analiz dosyasını yükle, yoksa boş liste döndür."""
    if ANALIZ_DOSYASI.exists():
        with open(ANALIZ_DOSYASI, "r") as f:
            return json.load(f)
    return []

def _analiz_dosyasina_kaydet(analizler):
    with open(ANALIZ_DOSYASI, "w") as f:
        json.dump(analizler, f, indent=2, ensure_ascii=False)

def _proje_dosyasi(ad):
    """Proje adından dosya yolu oluştur."""
    safe_name = ad.replace(" ", "_").replace("/", "-").lower()
    return PROJELER_DIR / f"{safe_name}.json"

def _yetki_matrisini_yukle():
    """Yetki matrisini oku ve kategorize et."""
    yetkiler = {"bagimsiz": [], "danis": [], "bilale_sor": []}
    if not YETKI_MATRISI.exists():
        return yetkiler
    metin = YETKI_MATRISI.read_text()
    current_key = None
    for line in metin.splitlines():
        line_raw = line.strip()
        # Normalize: replace Turkish İ with i and handle common variants
        line_normalized = line_raw.lower().replace("i̇", "i")  # İ → i + combining dot → i
        # Check if this is a section header (###)
        if not line_raw.startswith("###"):
            # Regular content line - add to current section if it's a list item
            if line_normalized.startswith("- ") and current_key:
                item = line_normalized.lstrip("- ").strip()
                yetkiler[current_key].append(item)
            continue
        # Section header matching
        # BAĞIMSIZ.lower() -> bağimsiz (ğ + regular i)
        if "bağimsiz" in line_normalized:
            current_key = "bagimsiz"
        elif "danış" in line_normalized or "danis" in line_normalized:
            current_key = "danis"
        elif "bilal" in line_normalized and ("sor" in line_normalized or "onay" in line_normalized):
            current_key = "bilale_sor"
    return yetkiler


# ═══════════════════════════════════════════════════════════════════════════════
# 1. CTO REFLEKS — Stratejik Analiz
# ═══════════════════════════════════════════════════════════════════════════════

def stratejik_analiz(konu, baglam=""):
    """
    CTO refleksi: konuyu analiz et, risk + öneri + alternatifler döndür.
    """
    # Basit kural tabanlı CTO refleks
    riskler = []
    oneriler = []
    alternatifler = []

    # Risk tespiti
    if any(k in konu.lower() for k in ["acil", "kriz", "sorun", "hata", "bug", "çökme", "crash"]):
        riskler.append("KRİTİK: Acil müdahale gerekiyor — sistem kararlılığı tehlikede.")
        oneriler.append("Öncelikli olarak izolasyon ve hızlı düzeltme (hotfix) uygulanmalı.")
    if any(k in konu.lower() for k in ["yatırım", "bütçe", "ücret", "ödeme", "maliyet"]):
        riskler.append("FİNANSAL: Maliyet/finans kararları dikkatle değerlendirilmeli.")
        oneriler.append("Alternatif bütçe senaryoları hazırlanmalı, en kötü durum hesaplanmalı.")
    if any(k in konu.lower() for k in ["işe alım", "işten çıkarma", "ekip", "kadro"]):
        riskler.append("İK: Takım yapılanması değişikliği — moral ve üretkenlik etkilenebilir.")
    if any(k in konu.lower() for k in ["teklif", "fiyat", "sözleşme", "anlaşma", "partner"]):
        riskler.append("TİCARİ: Ortaklık/teklif koşulları detaylıca incelenmeli, hukuki danışmanlık alınmalı.")
    if any(k in konu.lower() for k in ["yeni ürün", "pazar", "launch", "lansman", "çıkış"]):
        riskler.append("PAZAR: Zamanlama ve rekabet analizi yapılmalı, MVP tanımı netleştirilmeli.")

    # Genel öneriler ve alternatifler
    if not oneriler:
        oneriler.append("Mevcut durum analiz edildi — stratejik bir sapma görünmüyor.")
        oneriler.append("3 aylık yol haritası gözden geçirilmeli.")

    if not riskler:
        riskler.append("DÜŞÜK RİSK: Konu standart iş akışı içinde değerlendirilebilir.")

    alternatifler = [
        f"Plan A: Önerilen yol — {oneriler[0] if oneriler else 'standart akış'}",
        f"Plan B: Önce küçük ölçekli test et, sonra yaygınlaştır.",
        f"Plan C: Dış danışmanlık/ikinci görüş alarak ilerle."
    ]

    # Analiz kaydı
    analiz = {
        "tarih": _tarih(),
        "konu": konu,
        "baglam": baglam,
        "riskler": riskler,
        "oneriler": oneriler,
        "alternatifler": alternatifler
    }

    # Kaydet
    analizler = _analiz_dosyasini_yukle()
    analizler.append(analiz)
    _analiz_dosyasina_kaydet(analizler)

    return analiz


# ═══════════════════════════════════════════════════════════════════════════════
# 2. DIŞ TEMSİL — Raporlama
# ═══════════════════════════════════════════════════════════════════════════════

def rapor_hazirla(baslik, icerik=""):
    """Genel rapor oluştur ve ~/.hermes/raporlar/ altına kaydet."""
    tarih_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = baslik.replace(" ", "_").replace("/", "-").lower()[:40]
    dosya_adi = f"{tarih_stamp}_{safe_title}.md"
    dosya_yolu = RAPORLAR_DIR / dosya_adi

    rapor_icerik = f"""# {baslik}

**Tarih:** {_tarih()}
**Hazırlayan:** ORTAKLIK Motoru (Faz 8)

---

## Özet

{icerik if icerik else "Detaylı rapor içeriği burada yer alacak."}

---

*Bu rapor ORTAKLIK Motoru tarafından otomatik oluşturulmuştur.*
"""
    dosya_yolu.write_text(rapor_icerik)
    print(f"✓ Rapor kaydedildi: {dosya_yolu}")
    return str(dosya_yolu)


def musteri_raporu(musteri, konu):
    """Müşteriye özel rapor hazırla."""
    tarih_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_musteri = musteri.replace(" ", "_").replace("/", "-").lower()[:30]
    safe_konu = konu.replace(" ", "_").replace("/", "-").lower()[:30]
    dosya_adi = f"{tarih_stamp}_musteri_{safe_musteri}_{safe_konu}.md"
    dosya_yolu = RAPORLAR_DIR / dosya_adi

    rapor_icerik = f"""# Müşteri Raporu: {musteri}

**Tarih:** {_tarih()}
**Konu:** {konu}
**Hazırlayan:** ORTAKLIK Motoru (Faz 8)

---

## Durum Değerlendirmesi

Sayın {musteri},

**{konu}** konusundaki güncel durum aşağıda özetlenmiştir.

### İlerleme
- Beklenen çıktılar üzerinde çalışılmaktadır.
- Detaylı teknik rapor ekibimiz tarafından hazırlanmaktadır.

### Sonraki Adımlar
1. İlgili verilerin toplanması ve analizi
2. Ön değerlendirme raporunun hazırlanması
3. Karşılıklı görüşme ve onay süreci

---

*Bu rapor ORTAKLIK Motoru tarafından otomatik oluşturulmuştur.
Herhangi bir sorunuz varsa lütfen iletişime geçiniz.*
"""
    dosya_yolu.write_text(rapor_icerik)
    print(f"✓ Müşteri raporu kaydedildi: {dosya_yolu}")
    return str(dosya_yolu)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. PROJE YÖNETİMİ
# ═══════════════════════════════════════════════════════════════════════════════

def proje_olustur(ad, gorevler=None):
    """Yeni proje oluştur."""
    if gorevler is None:
        gorevler = []
    elif isinstance(gorevler, str):
        gorevler = [g.strip() for g in gorevler.split(",") if g.strip()]

    proje = {
        "ad": ad,
        "olusturma": _tarih(),
        "durum": "aktif",
        "gorevler": {g: {"sorumlu": None, "durum": "bekliyor", "tamamlanma": None} for g in gorevler},
        "tamamlanan_gorev_sayisi": 0,
        "toplam_gorev": len(gorevler)
    }

    dosya = _proje_dosyasi(ad)
    with open(dosya, "w") as f:
        json.dump(proje, f, indent=2, ensure_ascii=False)

    print(f"✓ Proje oluşturuldu: {ad} ({dosya})")
    if gorevler:
        print(f"  Görevler ({len(gorevler)}): {', '.join(gorevler)}")
    return proje


def gorev_ata(gorev, sorumlu, proje_adi):
    """Bir projedeki göreve sorumlu ata."""
    dosya = _proje_dosyasi(proje_adi)
    if not dosya.exists():
        print(f"✗ Proje bulunamadı: {proje_adi}")
        return False

    with open(dosya, "r") as f:
        proje = json.load(f)

    if gorev not in proje["gorevler"]:
        print(f"✗ Görev bulunamadı: '{gorev}' — Mevcut görevler: {list(proje['gorevler'].keys())}")
        return False

    proje["gorevler"][gorev]["sorumlu"] = sorumlu
    proje["gorevler"][gorev]["durum"] = "atanmis"

    with open(dosya, "w") as f:
        json.dump(proje, f, indent=2, ensure_ascii=False)

    print(f"✓ Görev atandı: '{gorev}' → {sorumlu} (Proje: {proje_adi})")
    return True


def ilerleme_raporu(proje_adi):
    """Proje ilerleme raporu oluştur ve göster."""
    dosya = _proje_dosyasi(proje_adi)
    if not dosya.exists():
        print(f"✗ Proje bulunamadı: {proje_adi}")
        return None

    with open(dosya, "r") as f:
        proje = json.load(f)

    toplam = len(proje["gorevler"])
    tamamlanan = sum(1 for g in proje["gorevler"].values() if g["durum"] == "tamamlandi")
    atanmis = sum(1 for g in proje["gorevler"].values() if g["durum"] == "atanmis")
    bekleyen = sum(1 for g in proje["gorevler"].values() if g["durum"] == "bekliyor")
    yuzde = (tamamlanan / toplam * 100) if toplam > 0 else 0

    print(f"{'='*60}")
    print(f"📊 PROJE İLERLEME RAPORU")
    print(f"{'='*60}")
    print(f"  Proje: {proje['ad']}")
    print(f"  Durum: {proje['durum']}")
    print(f"  Oluşturma: {proje['olusturma']}")
    print(f"  İlerleme: %{yuzde:.1f} ({tamamlanan}/{toplam})")
    print(f"  - Tamamlanan: {tamamlanan}")
    print(f"  - Atanmış:    {atanmis}")
    print(f"  - Bekleyen:   {bekleyen}")
    print(f"{'='*60}")

    if proje["gorevler"]:
        print(f"\n  Görev Detayı:")
        for gorev, detay in proje["gorevler"].items():
            durum_ikon = {"tamamlandi": "✓", "atanmis": "◷", "bekliyor": "○"}.get(detay["durum"], "?")
            sorumlu_str = f" → {detay['sorumlu']}" if detay["sorumlu"] else ""
            print(f"    {durum_ikon} {gorev}{sorumlu_str} [{detay['durum']}]")

    return proje


# ═══════════════════════════════════════════════════════════════════════════════
# 4. İMZA YETKİSİ
# ═══════════════════════════════════════════════════════════════════════════════

def _yetki_kategorisi_bul(karar, yetkiler):
    """Karar metnine göre yetki kategorisini tespit et.
    
    Matching stratejisi:
    1. Önce tam phrase eşleşmesi (longest exact substring)
    2. Ardından keyword bazlı eşleşme (individual words)
    """
    karar_lower = karar.lower()

    # Helper: extract meaningful keywords from a matris item
    def _keywords(item):
        """Split item into individual keywords (3+ chars) for flexible matching."""
        return [w for w in item.split() if len(w) >= 3]

    # Faz 1: Exact phrase match (more specific wins)
    for kategori in ["bilale_sor", "danis"]:
        for satir in yetkiler[kategori]:
            if satir in karar_lower:
                return kategori

    # Faz 2: Keyword match (individual words)
    # BİLAL'E SOR — en öncelikli keyword bazlı
    for satir in yetkiler["bilale_sor"]:
        for kw in _keywords(satir):
            if kw in karar_lower:
                return "bilale_sor"
    # DANIŞ
    for satir in yetkiler["danis"]:
        for kw in _keywords(satir):
            if kw in karar_lower:
                return "danis"
    # BAĞIMSIZ (varsayılan)
    return "bagimsiz"


def yetki_kontrol(karar):
    """Kararın yetki seviyesini kontrol et."""
    yetkiler = _yetki_matrisini_yukle()
    kategori = _yetki_kategorisi_bul(karar, yetkiler)

    sonuc = {
        "tarih": _tarih(),
        "karar": karar,
        "kategori": kategori,
        "yetki_verildi": kategori == "bagimsiz",
        "mesaj": ""
    }

    if kategori == "bagimsiz":
        sonuc["mesaj"] = "✅ BAĞIMSIZ — İmza yetkiniz var. Devam edebilirsiniz."
    elif kategori == "danis":
        sonuc["mesaj"] = "⚠️ DANIŞ — Bu karar için danışma gerekiyor. Önce ekiple görüşün."
    elif kategori == "bilale_sor":
        sonuc["mesaj"] = "🔴 BİLAL'E SOR — Bu karar için BİLAL onayı zorunlu. İmza yetkiniz yok."

    return sonuc


def imza_at(karar):
    """Kararı imzala ve logla."""
    kontrol = yetki_kontrol(karar)

    log_kaydi = {
        "tarih": _tarih(),
        "karar": karar,
        "kategori": kontrol["kategori"],
        "yetki_verildi": kontrol["yetki_verildi"],
        "imzalandi": kontrol["yetki_verildi"],
        "red_sebebi": None if kontrol["yetki_verildi"] else kontrol["mesaj"]
    }

    # Log dosyası
    log_dosyasi = HOME / ".hermes" / "stratejik_analizler" / "imza_loglari.json"
    loglar = []
    if log_dosyasi.exists():
        with open(log_dosyasi, "r") as f:
            loglar = json.load(f)
    loglar.append(log_kaydi)
    with open(log_dosyasi, "w") as f:
        json.dump(loglar, f, indent=2, ensure_ascii=False)

    if log_kaydi["imzalandi"]:
        print(f"✅ İMZA ATILDI: \"{karar[:60]}...\" ")
        print(f"   Kategori: {kontrol['kategori'].upper()} | {_tarih()}")
    else:
        print(f"❌ İMZA REDDEDİLDİ: \"{karar[:60]}...\" ")
        print(f"   Sebep: {kontrol['mesaj']}")

    print(f"   Log kaydedildi: {log_dosyasi}")
    return log_kaydi


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="ORTAKLIK Motoru — CTO Refleks · Dış Temsil · Proje Yönetimi · İmza Yetkisi",
        epilog="Örnek: python3 ortaklik_motoru.py --analiz 'yeni ürün lansmanı' --baglam 'Q3 2026'"
    )

    # CTO Refleks
    parser.add_argument("--analiz", type=str, help="Stratejik analiz konusu")
    parser.add_argument("--baglam", type=str, default="", help="Analiz bağlamı")

    # Dış Temsil
    parser.add_argument("--rapor", type=str, help="Rapor başlığı")
    parser.add_argument("--icerik", type=str, default="", help="Rapor içeriği")
    parser.add_argument("--rapor-musteri", type=str, help="Müşteri adı (--konu ile)")
    parser.add_argument("--konu", type=str, default="", help="Konu (müşteri raporu için)")

    # Proje Yönetimi
    parser.add_argument("--proje-olustur", action="store_true", help="Proje oluştur (--ad ile)")
    parser.add_argument("--ad", type=str, help="Proje adı")
    parser.add_argument("--gorevler", type=str, help="Görev listesi (virgülle ayrılmış)")
    parser.add_argument("--gorev-ata", action="store_true", help="Görev ata (--gorev, --sorumlu, --proje ile)")
    parser.add_argument("--gorev", type=str, help="Görev adı")
    parser.add_argument("--sorumlu", type=str, help="Sorumlu kişi")
    parser.add_argument("--ilerleme", action="store_true", help="İlerleme raporu göster (--proje ile)")
    parser.add_argument("--proje", type=str, help="Proje adı (ilerleme/görev-ata/proje-olustur için)")

    # İmza Yetkisi
    parser.add_argument("--yetki-kontrol", action="store_true", help="Yetki kontrolü yap (--karar ile)")
    parser.add_argument("--imza-at", action="store_true", help="Kararı imzala (--karar ile)")
    parser.add_argument("--karar", type=str, help="Karar metni")

    args = parser.parse_args()

    # ── CTO Refleks ──
    if args.analiz:
        sonuc = stratejik_analiz(args.analiz, args.baglam)
        print(f"\n{'='*60}")
        print(f"🧠 CTO REFLEKS — Stratejik Analiz")
        print(f"{'='*60}")
        print(f"  Konu:  {sonuc['konu']}")
        if sonuc['baglam']:
            print(f"  Bağlam: {sonuc['baglam']}")
        print(f"  Tarih: {sonuc['tarih']}")
        print(f"\n  ⚠️  RİSKLER:")
        for r in sonuc['riskler']:
            print(f"    • {r}")
        print(f"\n  💡 ÖNERİLER:")
        for o in sonuc['oneriler']:
            print(f"    • {o}")
        print(f"\n  🔀 ALTERNATİFLER:")
        for a in sonuc['alternatifler']:
            print(f"    • {a}")
        print(f"\n  📁 Kayıt: {ANALIZ_DOSYASI}")
        return

    # ── Dış Temsil ──
    if args.rapor_musteri:
        musteri_raporu(args.rapor_musteri, args.konu)
        return

    if args.rapor:
        rapor_hazirla(args.rapor, args.icerik)
        return

    # ── Proje Yönetimi ──
    if args.gorev_ata:
        if not all([args.gorev, args.sorumlu]):
            print("✗ --gorev-ata için --gorev ve --sorumlu gerekli")
            sys.exit(1)
        gorev_ata(args.gorev, args.sorumlu, args.proje)
        return

    if args.ilerleme:
        if not args.proje:
            print("✗ --ilerleme için --proje gerekli")
            sys.exit(1)
        ilerleme_raporu(args.proje)
        return

    if args.proje_olustur:
        if not args.ad:
            print("✗ --proje-olustur için --ad gerekli")
            sys.exit(1)
        proje_olustur(args.ad, args.gorevler)
        return

    # ── İmza Yetkisi ──
    if args.yetki_kontrol:
        if not args.karar:
            print("✗ --yetki-kontrol için --karar gerekli")
            sys.exit(1)
        sonuc = yetki_kontrol(args.karar)
        print(f"\n{'='*60}")
        print(f"🔑 YETKİ KONTROLÜ")
        print(f"{'='*60}")
        print(f"  Karar:    {sonuc['karar']}")
        print(f"  Kategori: {sonuc['kategori'].upper()}")
        print(f"  Sonuç:    {sonuc['mesaj']}")
        return

    if args.imza_at:
        if not args.karar:
            print("✗ --imza-at için --karar gerekli")
            sys.exit(1)
        imza_at(args.karar)
        return

    # Hiçbir argüman verilmediyse
    parser.print_help()


if __name__ == "__main__":
    main()
