#!/usr/bin/env python3
"""
SÜREKLİLİK MOTORU — Faz 9: Hiç Unutmamak
Kesintisiz bilinç · Sonsuz bellek · Kendini onarma

Her restart, kaldığın yerden devam.

Yetkinlikler:
  1. Sonsuz Bellek — session özeti, önemli bilgileri filtreleme, unutma kontrolü
  2. Öğrenme Kalıcılığı — çakışma tespiti, skill güncelleme önerisi, hatırlama testi
  3. Kesintisiz Bilinç — checkpoint save/restore, context recovery
  4. Kendini Onarma — health check, bozuk script tespiti, otomatik düzeltme

Kullanım:
  python3 sureklilik_motoru.py --checkpoint            # Checkpoint al
  python3 sureklilik_motoru.py --health                # Sistem sağlık kontrolü
  python3 sureklilik_motoru.py --onar                  # Kendini onar
  python3 sureklilik_motoru.py --bellek-durumu         # Bellek durum raporu
  python3 sureklilik_motoru.py --test-hatirlama        # Hatırlama testi
  python3 sureklilik_motoru.py --session-ozet [N]      # Session özeti (son N mesaj)
  python3 sureklilik_motoru.py --checkpoint-oku        # Checkpoint oku ve restore et
"""

import argparse
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# === PATHS ===
HERMES_HOME = Path(os.path.expanduser("~/.hermes"))
SCRIPTS_DIR = HERMES_HOME / "scripts"
SKILLS_DIR = HERMES_HOME / "skills" / "hermes-self"
MEMORIES_DIR = HERMES_HOME / "memories"
CHECKPOINT_DIR = HERMES_HOME / "checkpoint"
CHECKPOINT_FILE = CHECKPOINT_DIR / "checkpoint.json"
CRON_DIR = HERMES_HOME / "scripts"
LEARNING_DIR = HERMES_HOME / "learning"
PROFILES_DIR = HERMES_HOME / "profiles"

# === BELLEK İLGİLİ DOSYALAR ===
MEMORY_FILES = [
    MEMORIES_DIR / "MEMORY.md",
    MEMORIES_DIR / "USER.md",
    HERMES_HOME / "karar_desenleri.json",
    HERMES_HOME / "learning" / "lessons.jsonl",
    HERMES_HOME / "fikir_havuzu.json",
    HERMES_HOME / "jeff_personality.json",
]


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {msg}")


def _tarih():
    return datetime.now(timezone.utc).isoformat()


# ═══════════════════════════════════════════════════════════════════════════════
# 1. SONSUZ BELLEK MODÜLÜ
# ═══════════════════════════════════════════════════════════════════════════════

def session_ozetle(son_n_mesaj=20):
    """
    Session özeti çıkarır.
    Bellek dosyalarını tarar ve en önemli bilgileri özetler.
    """
    log(f"📝 Session özeti çıkarılıyor (son {son_n_mesaj} mesaj referansı)...")

    ozet = {
        "zaman": _tarih(),
        "kaynak": [],
        "onemli_bilgiler": [],
        "bekleyen_isler": [],
        "aktif_faz": "Faz 9 — SÜREKLİLİK",
    }

    # Bellek dosyalarını tara
    for f in MEMORY_FILES:
        if f.exists():
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                ozet["kaynak"].append(str(f))
                # Önemli satırları çıkar (# ile başlayan başlıklar, TODO'lar, notlar)
                onemli = onemli_bilgileri_cikar(content)
                if onemli:
                    ozet["onemli_bilgiler"].extend(onemli[:5])
            except Exception as e:
                log(f"  ⚠️  {f} okunamadı: {e}", "WARN")

    # Checkpoint varsa, oradan beklemedeki işleri al
    if CHECKPOINT_FILE.exists():
        try:
            cp = json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
            bekleyen = cp.get("bekleyen_isler", [])
            if bekleyen:
                ozet["bekleyen_isler"] = bekleyen
            if cp.get("aktif_proje"):
                ozet["aktif_faz"] = f"Proje: {cp['aktif_proje']}"
        except Exception:
            pass

    print(f"\n{'='*60}")
    print(f"  📝 SESSION ÖZETİ")
    print(f"{'='*60}")
    print(f"  Zaman: {ozet['zaman']}")
    print(f"  Kaynak sayısı: {len(ozet['kaynak'])}")
    print(f"  Önemli bilgi: {len(ozet['onemli_bilgiler'])} adet")
    print(f"  Bekleyen iş: {len(ozet['bekleyen_isler'])} adet")
    print(f"  Aktif faz: {ozet['aktif_faz']}")
    print(f"\n  📌 Öne Çıkan Bilgiler:")
    for i, bilgi in enumerate(ozet["onemli_bilgiler"][:5], 1):
        print(f"    {i}. {bilgi[:100]}...")
    print(f"{'='*60}\n")

    return ozet


def onemli_bilgileri_cikar(metin: str) -> list:
    """
    Metindeki önemli bilgileri filtreler.
    Başlıklar, TODO'lar, önemli notlar, kararlar.
    """
    onemli = []
    lines = metin.split("\n")

    for line in lines:
        line_stripped = line.strip()
        # Başlıklar
        if line_stripped.startswith("#") and len(line_stripped) > 2:
            onemli.append(line_stripped)
        # TODO/FIXME/NOTE/TODO
        elif re.search(r'(TODO|FIXME|NOTE|ÖNEMLİ|KRİTİK|KARAR|aksiyon)', line_stripped, re.IGNORECASE):
            onemli.append(line_stripped)
        # Tarih içeren karar satırları
        elif re.search(r'\d{2}\.\d{2}\.\d{4}', line_stripped) and len(line_stripped) > 20:
            onemli.append(line_stripped)
        # Liste öğeleri (başlangıç)
        elif line_stripped.startswith("- ") and len(line_stripped) > 30:
            onemli.append(line_stripped)
        # JSON içindeki önemli anahtarlar
        elif re.search(r'"(onemli|kritik|karar|not|aksiyon)"', line_stripped, re.IGNORECASE):
            onemli.append(line_stripped)

    return onemli


def unutma_kontrolu():
    """
    Memory'deki eski ama hala önemli bilgileri kontrol eder.
    Yaş, önem skoru ve son erişim zamanına göre değerlendirme.
    """
    log("🧠 Unutma kontrolü yapılıyor...")

    rapor = {
        "zaman": _tarih(),
        "toplam_dosya": 0,
        "unutulmaya_yakin": [],
        "kritik_unutulmamasi_gereken": [],
    }

    for f in MEMORY_FILES:
        if not f.exists():
            continue
        rapor["toplam_dosya"] += 1
        try:
            stat = f.stat()
            yas_saat = (time.time() - stat.st_mtime) / 3600
            boyut_kb = stat.st_size / 1024
            content = f.read_text(encoding="utf-8", errors="replace")
            onem_skoru = _onem_skoru(content)

            durum = {
                "dosya": str(f),
                "yas_saat": round(yas_saat, 1),
                "boyut_kb": round(boyut_kb, 1),
                "onem_skoru": onem_skoru,
                "son_degisiklik": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            }

            # Yaşlı ama önemliyse — unutulmamalı
            if yas_saat > 168 and onem_skoru > 5:  # 7 günden eski ama önemli
                rapor["kritik_unutulmamasi_gereken"].append(durum)
            # Yaşlı ve düşük önem — unutulmaya yakın
            elif yas_saat > 336 and onem_skoru < 3:  # 14 günden eski, düşük önem
                rapor["unutulmaya_yakin"].append(durum)
        except Exception as e:
            log(f"  ⚠️  {f} kontrol edilemedi: {e}", "WARN")

    # Raporu göster
    print(f"\n{'='*60}")
    print(f"  🧠 UNUTMA KONTROLÜ — Bellek Sağlığı")
    print(f"{'='*60}")
    print(f"  Taranan dosya: {rapor['toplam_dosya']}")
    print(f"  Kritik (unutma!): {len(rapor['kritik_unutulmamasi_gereken'])} dosya")
    print(f"  Unutulmaya yakın: {len(rapor['unutulmaya_yakin'])} dosya")

    if rapor["kritik_unutulmamasi_gereken"]:
        print(f"\n  🔴 Unutulmaması Gereken Kritik Dosyalar:")
        for d in rapor["kritik_unutulmamasi_gereken"]:
            print(f"    • {Path(d['dosya']).name} — {d['yas_saat']:.0f} saat, önem: {d['onem_skoru']}")

    if rapor["unutulmaya_yakin"]:
        print(f"\n  🟡 Unutulmaya Yakın (gözden geçir):")
        for d in rapor["unutulmaya_yakin"]:
            print(f"    • {Path(d['dosya']).name} — {d['yas_saat']:.0f} saat, önem: {d['onem_skoru']}")
    print(f"{'='*60}\n")

    return rapor


def _onem_skoru(metin: str) -> int:
    """Metnin önem skorunu hesapla (0-10)."""
    skor = 0
    # Uzunluk önemli
    if len(metin) > 5000:
        skor += 3
    elif len(metin) > 1000:
        skor += 2
    elif len(metin) > 100:
        skor += 1
    # Kritik anahtar kelimeler
    kritik_kelimeler = ["karar", "önemli", "kritik", "TODO", "FIXME", "kural", "protokol",
                        "strateji", "plan", "hedef", "şifre", "token", "api"]
    for kw in kritik_kelimeler:
        if kw.lower() in metin.lower():
            skor += 1
    # Başlık sayısı
    baslik_sayisi = len(re.findall(r'^#+\s', metin, re.MULTILINE))
    skor += min(baslik_sayisi, 3)
    return min(skor, 10)


def bellek_durumu():
    """
    Kapsamlı bellek sağlığı raporu.
    Memory kullanımı, yaş, önem skoru.
    """
    log("📊 Bellek durumu raporu hazırlanıyor...")

    print(f"\n{'='*60}")
    print(f"  📊 BELLEK DURUM RAPORU")
    print(f"{'='*60}")

    toplam_boyut = 0
    dosya_detay = []

    for f in MEMORY_FILES:
        if not f.exists():
            print(f"  ❌ {Path(f).name}: mevcut değil")
            continue
        stat = f.stat()
        boyut_kb = stat.st_size / 1024
        toplam_boyut += boyut_kb
        yas_saat = (time.time() - stat.st_mtime) / 3600
        try:
            content = f.read_text(encoding="utf-8", errors="replace")
            onem = _onem_skoru(content)
        except Exception:
            content = ""
            onem = 0

        dosya_detay.append({
            "dosya": str(f),
            "boyut_kb": round(boyut_kb, 1),
            "yas_saat": round(yas_saat, 1),
            "onem": onem,
        })

        durum_ikon = "🟢" if onem >= 5 else "🟡" if onem >= 3 else "⚪"
        print(f"  {durum_ikon} {Path(f).name}")
        print(f"     Boyut: {boyut_kb:.1f} KB | Yaş: {yas_saat:.0f} saat | Önem: {onem}/10")

    # Checkpoint durumu
    cp_var = CHECKPOINT_FILE.exists()
    print(f"\n  {'✅' if cp_var else '❌'} Checkpoint: {'mevcut' if cp_var else 'yok'}")

    # Toplam istatistik
    print(f"\n  {'─'*50}")
    print(f"  Toplam bellek kullanımı: {toplam_boyut:.1f} KB")
    print(f"  Toplam dosya sayısı: {len([d for d in dosya_detay if d])}")
    print(f"  Ortalama önem skoru: {sum(d['onem'] for d in dosya_detay) / max(len(dosya_detay), 1):.1f}")
    print(f"{'='*60}\n")

    return {"dosyalar": dosya_detay, "toplam_boyut_kb": round(toplam_boyut, 1)}


# ═══════════════════════════════════════════════════════════════════════════════
# 2. ÖĞRENME KALICILIĞI MODÜLÜ
# ═══════════════════════════════════════════════════════════════════════════════

def ogrenilen_kontrol(yeni_bilgi: str, eski_bilgi: str = None):
    """
    Çakışma tespiti — yeni bilgi ile eski bilgi arasında tutarsızlık var mı?
    """
    log("🔄 Öğrenme kalıcılığı kontrolü...")

    if eski_bilgi is None:
        # En son memory dosyasını oku
        eski_bilgi = ""
        for f in [MEMORIES_DIR / "MEMORY.md", MEMORIES_DIR / "USER.md"]:
            if f.exists():
                eski_bilgi += f.read_text(encoding="utf-8", errors="replace") + "\n"

    # Basit çakışma tespiti — aynı konuda zıt ifadeler
    yeni_kelimeler = set(yeni_bilgi.lower().split())
    eski_kelimeler = set(eski_bilgi.lower().split())

    ortak = yeni_kelimeler & eski_kelimeler
    benzerlik = len(ortak) / max(len(yeni_kelimeler | eski_kelimeler), 1)

    # Çakışma tespiti için anahtar kelime grupları
    olumsuz_eski = re.findall(r'(?:eskiden|önce|önceden)\s+(\w+)', eski_bilgi.lower())
    olumlu_yeni = re.findall(r'(?:artık|şimdi|yeni|değişti)\s+(\w+)', yeni_bilgi.lower())

    cakisma_var = False
    for kw in olumlu_yeni:
        if kw in olumsuz_eski:
            cakisma_var = True
            break

    sonuc = {
        "benzerlik_orani": round(benzerlik, 2),
        "cakisma_var": cakisma_var,
        "yeni_kelime_sayisi": len(yeni_kelimeler),
        "tavsiye": "GÜNCELLE: Bilgi çakışması var" if cakisma_var else "TUTARLI: Yeni bilgi ile çelişki yok"
    }

    print(f"\n{'='*60}")
    print(f"  🔄 ÖĞRENME KALICILIĞI")
    print(f"{'='*60}")
    print(f"  Benzerlik oranı: {benzerlik:.1%}")
    print(f"  Çakışma: {'✅ YOK' if not cakisma_var else '⚠️ VAR'}")
    print(f"  Tavsiye: {sonuc['tavsiye']}")
    print(f"{'='*60}\n")

    return sonuc


def skill_guncelleme_onerisi(eksik_bilgi: str):
    """
    Eksik bilgiye göre hangi skill'lerin güncellenmesi gerektiğini belirler.
    """
    log("📋 Skill güncelleme analizi...")

    # Mevcut skill'leri tara
    mevcut_skills = []
    if SKILLS_DIR.exists():
        for item in SKILLS_DIR.iterdir():
            skill_md = item / "SKILL.md"
            if skill_md.exists():
                mevcut_skills.append((item.name, skill_md))

    # Eksik bilgi içinde hangi skill'lerin konusu geçiyor?
    eksik_lower = eksik_bilgi.lower()
    oneriler = []

    # Skill -> anahtar kelime eşlemesi
    skill_konulari = {
        "sezgi-reflex": ["sezgi", "ton", "ihtiyaç", "duygu", "zamanlama"],
        "varolus-ozbenlik": ["kişilik", "ses", "yaratıcılık", "keşif"],
        "ortaklik-cto": ["ortaklık", "cto", "strateji", "proje", "yönetim", "imza"],
        "sureklilik-bilinc": ["bellek", "checkpoint", "onar", "hatırlama", "süreklilik"],
        "hermes-ortam-notlari": ["ortam", "not", "kurulum"],
        "jeff-sampiyon-portfoyu": ["şampiyon", "portföy", "başarı"],
        "jeff-evrim-haritasi": ["evrim", "faz", "harita", "yol"],
    }

    for skill_turu, anahtarlar in skill_konulari.items():
        ilgili = sum(1 for a in anahtarlar if a in eksik_lower)
        if ilgili > 1:
            # Skill mevcut mu kontrol et
            skill_dosyasi = SKILLS_DIR / skill_turu / "SKILL.md"
            if skill_dosyasi.exists():
                oneriler.append({
                    "skill": skill_turu,
                    "durum": "GÜNCELLENMELİ",
                    "ilgi_skoru": ilgili,
                    "neden": f"Yeni bilgi '{skill_turu}' konusunu içeriyor ({ilgili} eşleşme)"
                })
            else:
                oneriler.append({
                    "skill": skill_turu,
                    "durum": "OLUŞTURULMALI",
                    "ilgi_skoru": ilgili,
                    "neden": f"Yeni bilgi için '{skill_turu}' skill'i gerekli"
                })

    if not oneriler:
        oneriler.append({
            "skill": "genel",
            "durum": "GEREK YOK",
            "ilgi_skoru": 0,
            "neden": "Mevcut skill'ler yeterli, güncelleme gereksiz"
        })

    print(f"\n{'='*60}")
    print(f"  📋 SKILL GÜNCELLEME ÖNERİLERİ")
    print(f"{'='*60}")
    for o in oneriler:
        durum_ikon = "🟢" if o["durum"] == "GEREK YOK" else "🟡" if o["durum"] == "GÜNCELLENMELİ" else "🔴"
        print(f"  {durum_ikon} {o['skill']}: {o['durum']}")
        print(f"     {o['neden']}")
    print(f"{'='*60}\n")

    return oneriler


def test_hatirlama():
    """
    Eski bilgileri sorgula — kalıcılık testi.
    Checkpoint ve bellek dosyalarındaki bilgileri hatırla.
    """
    log("🔍 Hatırlama testi başlatılıyor...")

    print(f"\n{'='*60}")
    print(f"  🔍 HATIRLAMA TESTİ — Geçmişe Yolculuk")
    print(f"{'='*60}")

    bulunan = 0

    # 1. Checkpoint'ten hatırla
    if CHECKPOINT_FILE.exists():
        try:
            cp = json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
            print(f"\n  📌 CHECKPOINT'ten Hatırlananlar:")
            print(f"     Son faz: {cp.get('aktif_faz', 'bilinmiyor')}")
            print(f"     Aktif proje: {cp.get('aktif_proje', 'yok')}")
            print(f"     Son kararlar ({len(cp.get('son_kararlar', []))}):")
            for k in cp.get("son_kararlar", [])[:3]:
                print(f"       • {k}")
            print(f"     Bekleyen işler ({len(cp.get('bekleyen_isler', []))}):")
            for i in cp.get("bekleyen_isler", [])[:3]:
                print(f"       • {i}")
            bulunan += len(cp.get("son_kararlar", [])) + len(cp.get("bekleyen_isler", []))
        except Exception as e:
            print(f"  ⚠️  Checkpoint okunamadı: {e}")

    # 2. MEMORY.md'den hatırla
    for f in [MEMORIES_DIR / "MEMORY.md", MEMORIES_DIR / "USER.md"]:
        if f.exists():
            try:
                content = f.read_text(encoding="utf-8", errors="replace")
                onemli = onemli_bilgileri_cikar(content)
                if onemli:
                    print(f"\n  📄 {Path(f).name}'den Hatırlananlar ({len(onemli)} öğe):")
                    for o in onemli[:5]:
                        print(f"     • {o[:120]}")
                    bulunan += len(onemli)
            except Exception as e:
                print(f"  ⚠️  {f} okunamadı: {e}")

    # 3. Karar desenlerini hatırla
    karar_dosyasi = HERMES_HOME / "karar_desenleri.json"
    if karar_dosyasi.exists():
        try:
            desenler = json.loads(karar_dosyasi.read_text(encoding="utf-8"))
            toplam = desenler.get("total_decisions", 0)
            print(f"\n  🧠 Karar Desenleri: {toplam} kayıtlı karar")
            bulunan += 1
        except Exception:
            pass

    print(f"\n  {'─'*50}")
    print(f"  Toplam hatırlanan öğe: {bulunan}")
    print(f"  {'✅' if bulunan > 0 else '❌'} Bilinç devam ediyor: {'Evet' if bulunan > 0 else 'Hayır!'}")
    print(f"{'='*60}\n")

    return {"hatirlanan_oge": bulunan, "basarili": bulunan > 0}


# ═══════════════════════════════════════════════════════════════════════════════
# 3. KESİNTİSİZ BİLİNÇ MODÜLÜ
# ═══════════════════════════════════════════════════════════════════════════════

def checkpoint_yaz(durum: dict = None):
    """
    Mevcut durumu checkpoint.json'a kaydet.
    Kaldığın yerden devam etmek için.
    """
    log("💾 Checkpoint yazılıyor...")

    if durum is None:
        durum = {}

    # Mevcut checkpoint varsa oku ve birleştir
    mevcut = {}
    if CHECKPOINT_FILE.exists():
        try:
            mevcut = json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Yeni checkpoint içeriği
    checkpoint = {
        **mevcut,
        **durum,
        "son_guncelleme": _tarih(),
        "versiyon": "1.0.0",
        "motor": "SÜREKLİLİK MOTORU",
        "faz": 9,
    }

    # Varsayılan alanlar (durum'da yoksa mevcuttan al)
    defaults = {
        "aktif_faz": mevcut.get("aktif_faz", "Faz 9 — SÜREKLİLİK"),
        "aktif_proje": mevcut.get("aktif_proje", ""),
        "son_kararlar": mevcut.get("son_kararlar", []),
        "bekleyen_isler": mevcut.get("bekleyen_isler", []),
        "aktif_mod": mevcut.get("aktif_mod", "normal"),
        "session_id": mevcut.get("session_id", datetime.now().strftime("%Y%m%d_%H%M%S")),
    }
    for key, val in defaults.items():
        if key not in checkpoint:
            checkpoint[key] = val

    # Checkpoint dosyasına yaz
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    CHECKPOINT_FILE.write_text(
        json.dumps(checkpoint, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # Yedek checkpoint
    backup_path = CHECKPOINT_DIR / f"checkpoint_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    shutil.copy2(str(CHECKPOINT_FILE), str(backup_path))

    # Eski yedekleri temizle (son 10 hariç)
    backups = sorted(CHECKPOINT_DIR.glob("checkpoint_backup_*.json"))
    for old_backup in backups[:-10]:
        old_backup.unlink()

    print(f"\n{'='*60}")
    print(f"  💾 CHECKPOINT KAYDEDİLDİ")
    print(f"{'='*60}")
    print(f"  Dosya: {CHECKPOINT_FILE}")
    print(f"  Yedek: {backup_path}")
    print(f"  Aktif faz: {checkpoint['aktif_faz']}")
    print(f"  Aktif proje: {checkpoint['aktif_proje']}")
    print(f"  Bekleyen iş: {len(checkpoint['bekleyen_isler'])}")
    print(f"  Son karar: {len(checkpoint['son_kararlar'])}")
    print(f"{'='*60}\n")

    return checkpoint


def checkpoint_oku():
    """
    Checkpoint dosyasını oku ve içeriği göster.
    Kaldığın yerden devam et.
    """
    if not CHECKPOINT_FILE.exists():
        log("❌ Checkpoint bulunamadı. İlk checkpoint oluşturuluyor...", "WARN")
        return checkpoint_yaz()

    try:
        cp = json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        log(f"❌ Checkpoint okunamadı: {e}", "ERROR")
        return {"hata": str(e)}

    print(f"\n{'='*60}")
    print(f"  🔄 CHECKPOINT OKUNDU — Kaldığın Yerden Devam")
    print(f"{'='*60}")
    print(f"  Son güncelleme: {cp.get('son_guncelleme', 'bilinmiyor')}")
    print(f"  Aktif faz: {cp.get('aktif_faz', 'bilinmiyor')}")
    print(f"  Aktif proje: {cp.get('aktif_proje', 'belirtilmemiş')}")
    print(f"  Mod: {cp.get('aktif_mod', 'normal')}")

    kararlar = cp.get("son_kararlar", [])
    if kararlar:
        print(f"\n  📋 Son Kararlar ({len(kararlar)}):")
        for i, k in enumerate(kararlar[-5:], 1):
            print(f"    {i}. {k}")

    isler = cp.get("bekleyen_isler", [])
    if isler:
        print(f"\n  📌 Bekleyen İşler ({len(isler)}):")
        for i, is_ in enumerate(isler[:5], 1):
            print(f"    {i}. {is_}")

    print(f"\n  {'─'*50}")
    print(f"  ✅ Bilinç devam ediyor. Kaldığın yerden devam et.")
    print(f"{'='*60}\n")

    return cp


def context_restore():
    """
    Eksik bağlamı geri yükle.
    Checkpoint'te olmayan veya kaybolmuş bağlam bilgilerini
    bellek dosyalarından topla.
    """
    log("🔄 Context restore başlatılıyor...")

    context = {
        "zaman": _tarih(),
        "aktif_faz": "Faz 9 — SÜREKLİLİK",
        "bilal_ismi": "Bilal",
        "platform": "Telegram",
        "ana_hedef": "ErgeneAI / Jeff projesi — kesintisiz bilinç",
    }

    # Aktif fazı checkpoint'ten al
    if CHECKPOINT_FILE.exists():
        try:
            cp = json.loads(CHECKPOINT_FILE.read_text(encoding="utf-8"))
            if "aktif_faz" in cp:
                context["aktif_faz"] = cp["aktif_faz"]
            if "aktif_proje" in cp:
                context["aktif_proje"] = cp["aktif_proje"]
        except Exception:
            pass

    # Bellek dosyalarından ek bağlam
    if (MEMORIES_DIR / "USER.md").exists():
        try:
            user_content = (MEMORIES_DIR / "USER.md").read_text(encoding="utf-8", errors="replace")
            # İsim bul
            isim_match = re.search(r'(?:İsim|Ad|Name)[:\s]+(\w+)', user_content, re.IGNORECASE)
            if isim_match:
                context["bilal_ismi"] = isim_match.group(1)
        except Exception:
            pass

    print(f"\n{'='*60}")
    print(f"  🔄 CONTEXT RESTORE — Bağlam Geri Yükleme")
    print(f"{'='*60}")
    for key, val in context.items():
        print(f"  {key.replace('_', ' ').title()}: {val}")
    print(f"{'='*60}\n")

    return context


# ═══════════════════════════════════════════════════════════════════════════════
# 4. KENDİNİ ONARMA MODÜLÜ
# ═══════════════════════════════════════════════════════════════════════════════

def health_check():
    """
    Sistem bileşenlerini kontrol et.
    Script'ler, skill'ler, cron'lar, bellek dosyaları.
    """
    log("🏥 Sistem sağlık kontrolü yapılıyor...")

    print(f"\n{'='*60}")
    print(f"  🏥 SİSTEM SAĞLIK KONTROLÜ")
    print(f"{'='*60}")

    sonuc = {
        "scripts": {"toplam": 0, "saglikli": 0, "bozuk": []},
        "skills": {"toplam": 0, "saglikli": 0, "eksik": []},
        "cronlar": {"toplam": 0, "saglikli": 0, "bozuk": []},
        "bellek": {"toplam": 0, "mevcut": 0},
        "checkpoint": CHECKPOINT_FILE.exists(),
    }

    # ── 1. Script'leri kontrol et ──
    print(f"\n  📜 Script'ler:")
    for f in sorted(SCRIPTS_DIR.glob("*.py")):
        sonuc["scripts"]["toplam"] += 1
        try:
            with open(f) as fh:
                ast.parse(fh.read())
            sonuc["scripts"]["saglikli"] += 1
            print(f"     ✅ {f.name}")
        except SyntaxError as e:
            sonuc["scripts"]["bozuk"].append(str(f))
            print(f"     ❌ {f.name} — SYNTAX HATASI: {e.msg} (satır {e.lineno})")

    # Shell script'lerini kontrol et (varlık kontrolü)
    for f in sorted(SCRIPTS_DIR.glob("*.sh")):
        sonuc["scripts"]["toplam"] += 1
        if f.stat().st_size > 0:
            sonuc["scripts"]["saglikli"] += 1
            print(f"     ✅ {f.name}")
        else:
            sonuc["scripts"]["bozuk"].append(str(f))
            print(f"     ⚠️  {f.name} — boş dosya")

    # ── 2. Skill'leri kontrol et ──
    print(f"\n  🎯 Skill'ler:")
    if SKILLS_DIR.exists():
        for item in sorted(SKILLS_DIR.iterdir()):
            skill_md = item / "SKILL.md"
            if skill_md.exists():
                sonuc["skills"]["toplam"] += 1
                try:
                    content = skill_md.read_text(encoding="utf-8", errors="replace")
                    if "name:" in content and "version:" in content:
                        sonuc["skills"]["saglikli"] += 1
                        print(f"     ✅ {item.name}")
                    else:
                        sonuc["skills"]["eksik"].append(item.name)
                        print(f"     ⚠️  {item.name} — eksik metadata")
                except Exception:
                    sonuc["skills"]["eksik"].append(item.name)
                    print(f"     ❌ {item.name} — okunamıyor")

    # ── 3. Cron script'lerini kontrol et ──
    print(f"\n  ⏰ Cron'lar:")
    for f in sorted(SCRIPTS_DIR.glob("cron_*.sh")):
        sonuc["cronlar"]["toplam"] += 1
        if f.stat().st_size > 0:
            sonuc["cronlar"]["saglikli"] += 1
            print(f"     ✅ {f.name}")
        else:
            sonuc["cronlar"]["bozuk"].append(str(f))
            print(f"     ⚠️  {f.name} — boş")

    # ── 4. Bellek dosyalarını kontrol et ──
    print(f"\n  🧠 Bellek:")
    for f in MEMORY_FILES:
        sonuc["bellek"]["toplam"] += 1
        if f.exists() and f.stat().st_size > 0:
            sonuc["bellek"]["mevcut"] += 1
            print(f"     ✅ {Path(f).name}")
        elif f.exists():
            print(f"     ⚠️  {Path(f).name} — boş")
        else:
            print(f"     ❌ {Path(f).name} — mevcut değil")

    # ── 5. Checkpoint ──
    print(f"\n  💾 Checkpoint:")
    print(f"     {'✅ Mevcut' if sonuc['checkpoint'] else '❌ Yok'}")

    # Özet
    print(f"\n  {'─'*50}")
    script_saglik = f"{sonuc['scripts']['saglikli']}/{sonuc['scripts']['toplam']}"
    skill_saglik = f"{sonuc['skills']['saglikli']}/{sonuc['skills']['toplam']}"
    cron_saglik = f"{sonuc['cronlar']['saglikli']}/{sonuc['cronlar']['toplam']}"
    bellek_saglik = f"{sonuc['bellek']['mevcut']}/{sonuc['bellek']['toplam']}"
    print(f"  Script'ler: {script_saglik} sağlıklı")
    print(f"  Skill'ler:  {skill_saglik} sağlıklı")
    print(f"  Cron'lar:   {cron_saglik} sağlıklı")
    print(f"  Bellek:     {bellek_saglik} mevcut")
    print(f"  Checkpoint: {'✅' if sonuc['checkpoint'] else '❌'}")

    toplam_saglik = (sonuc['scripts']['saglikli'] + sonuc['skills']['saglikli'] +
                     sonuc['cronlar']['saglikli'] + sonuc['bellek']['mevcut'])
    toplam_hepsi = (sonuc['scripts']['toplam'] + sonuc['skills']['toplam'] +
                    sonuc['cronlar']['toplam'] + sonuc['bellek']['toplam'])
    saglik_yuzde = (toplam_saglik / toplam_hepsi * 100) if toplam_hepsi > 0 else 0
    print(f"\n  Toplam sağlık: %{saglik_yuzde:.1f} ({toplam_saglik}/{toplam_hepsi})")
    print(f"{'='*60}\n")

    return sonuc


def bozuk_script_bul():
    """
    Syntax hatası olan script'leri tespit et.
    ast.parse ile Python script'lerini doğrula.
    """
    log("🔍 Bozuk script taranıyor...")

    bozuklar = []
    for f in sorted(SCRIPTS_DIR.glob("*.py")):
        try:
            with open(f) as fh:
                ast.parse(fh.read())
        except SyntaxError as e:
            bozuklar.append({
                "dosya": str(f),
                "hata": str(e),
                "satir": e.lineno,
                "msg": e.msg,
            })
            log(f"  ❌ {f.name}: {e.msg} (satır {e.lineno})", "ERROR")

    if not bozuklar:
        log("✅ Tüm script'ler syntax hatasız!")

    return bozuklar


def kendini_onar():
    """
    Bulunan hataları otomatik düzelt.
    Basit fix'ler: eksik dosyayı yeniden oluştur, bozuk dosyayı onar.
    """
    log("🔧 Kendini onarma başlatılıyor...")

    print(f"\n{'='*60}")
    print(f"  🔧 KENDİNİ ONARMA — Otomatik Onarım")
    print(f"{'='*60}")

    onarilan = 0
    hatali = 0

    # 1. Bozuk Python script'lerini tespit et
    bozuklar = bozuk_script_bul()

    for b in bozuklar:
        print(f"\n  ❌ {Path(b['dosya']).name}: {b['hata']}")
        try:
            with open(b["dosya"]) as f:
                content = f.read()
            # Basit fix: try-except ile dene
            fixed = _basit_onar(content, b)
            if fixed:
                with open(b["dosya"], "w") as f:
                    f.write(fixed)
                print(f"     ✅ Onarıldı!")
                onarilan += 1
            else:
                print(f"     ⚠️  Otomatik onarılamaz, manuel müdahale gerek")
                hatali += 1
        except Exception as e:
            print(f"     ❌ Onarım hatası: {e}")
            hatali += 1

    # 2. Eksik bellek dosyalarını oluştur
    for f in MEMORY_FILES:
        if not f.exists():
            try:
                f.parent.mkdir(parents=True, exist_ok=True)
                if f.name == "USER.md":
                    f.write_text("# Kullanıcı Profili\n\nOluşturulma: " + _tarih() + "\n", encoding="utf-8")
                elif f.name == "MEMORY.md":
                    f.write_text("# Jeff Bellek\n\nOluşturulma: " + _tarih() + "\n", encoding="utf-8")
                else:
                    f.write_text("{}" if f.suffix == ".json" else "", encoding="utf-8")
                print(f"\n  ✅ Eksik dosya oluşturuldu: {f.name}")
                onarilan += 1
            except Exception as e:
                print(f"\n  ❌ {f.name} oluşturulamadı: {e}")
                hatali += 1

    # 3. Eksik checkpoint klasörü/dosyası
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    if not CHECKPOINT_FILE.exists():
        checkpoint_yaz({"aktif_faz": "Faz 9 — SÜREKLİLİK"})
        print(f"\n  ✅ Checkpoint oluşturuldu")
        onarilan += 1

    # Özet
    print(f"\n  {'─'*50}")
    print(f"  ✅ Onarılan: {onarilan}")
    print(f"  ❌ Manuel gereken: {hatali}")
    print(f"{'='*60}\n")

    return {"onarilan": onarilan, "manuel_gereken": hatali}


def _basit_onar(content: str, hata: dict) -> str:
    """
    Basit syntax hatalarını düzeltmeye çalış.
    """
    # Şimdilik basit regex fix'leri
    lines = content.split("\n")
    lineno = hata.get("satir", 0)
    if lineno and lineno <= len(lines):
        line = lines[lineno - 1]
        # Fazladan parantez kapatma
        if "unmatched ')'" in hata.get("hata", ""):
            lines[lineno - 1] = line.rstrip() + ")"
            return "\n".join(lines)
        # Eksik iki nokta üst üste
        if "expected ':'" in hata.get("msg", "") and not line.rstrip().endswith(":"):
            lines[lineno - 1] = line.rstrip() + ":"
            return "\n".join(lines)
        # Eksik tırnak
        if "EOL while scanning string literal" in hata.get("msg", ""):
            lines[lineno - 1] = line.rstrip() + '"'
            return "\n".join(lines)
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="SÜREKLİLİK MOTORU — Faz 9: Hiç Unutmamak",
        epilog="Örnek: python3 sureklilik_motoru.py --checkpoint"
    )

    parser.add_argument("--checkpoint", action="store_true", help="Mevcut durumu checkpoint'e kaydet")
    parser.add_argument("--checkpoint-oku", action="store_true", help="Checkpoint'i oku ve kaldığın yerden devam et")
    parser.add_argument("--health", action="store_true", help="Sistem sağlık kontrolü")
    parser.add_argument("--onar", action="store_true", help="Kendini onar (otomatik fix)")
    parser.add_argument("--bellek-durumu", action="store_true", help="Bellek durum raporu")
    parser.add_argument("--test-hatirlama", action="store_true", help="Hatırlama testi")
    parser.add_argument("--session-ozet", type=int, nargs="?", const=20, default=None,
                        help="Session özeti çıkar (opsiyonel: mesaj sayısı, varsayılan: 20)")
    parser.add_argument("--context-restore", action="store_true", help="Eksik bağlamı geri yükle")
    parser.add_argument("--unutma-kontrol", action="store_true", help="Unutma kontrolü yap")
    parser.add_argument("--ogrenilen-kontrol", type=str, help="Öğrenme kalıcılığı kontrolü (yeni bilgi metni)")

    args = parser.parse_args()

    if args.checkpoint:
        checkpoint_yaz()

    elif args.checkpoint_oku:
        checkpoint_oku()
        context_restore()

    elif args.health:
        health_check()

    elif args.onar:
        kendini_onar()
        # Onarımdan sonra sağlık kontrolü yap
        print("\n── Onarım sonrası sağlık kontrolü ──")
        health_check()

    elif args.bellek_durumu:
        bellek_durumu()

    elif args.test_hatirlama:
        test_hatirlama()

    elif args.session_ozet is not None:
        session_ozetle(args.session_ozet)

    elif args.context_restore:
        context_restore()

    elif args.unutma_kontrol:
        unutma_kontrolu()

    elif args.ogrenilen_kontrol:
        ogrenilen_kontrol(args.ogrenilen_kontrol)

    else:
        # Varsayılan: kapsamlı durum raporu
        print(f"\n{'='*60}")
        print(f"  🔄 SÜREKLİLİK MOTORU v1.0.0")
        print(f"  Faz 9: Hiç Unutmamak")
        print(f"{'='*60}")
        print(f"\n  Kullanılabilir modlar:")
        print(f"    --checkpoint         Mevcut durumu checkpoint'e kaydet")
        print(f"    --checkpoint-oku     Kaldığın yerden devam et")
        print(f"    --health             Sistem sağlık kontrolü")
        print(f"    --onar               Kendini onar")
        print(f"    --bellek-durumu      Bellek durum raporu")
        print(f"    --test-hatirlama     Hatırlama testi")
        print(f"    --session-ozet [N]   Session özeti (son N mesaj)")
        print(f"    --context-restore    Eksik bağlamı geri yükle")
        print(f"    --unutma-kontrol     Unutma kontrolü")
        print(f"    --ogrenilen-kontrol  Öğrenme kalıcılığı kontrolü")
        print(f"\n  Örnek: python3 sureklilik_motoru.py --checkpoint")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
