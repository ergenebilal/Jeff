#!/usr/bin/env python3
"""
KÖKLEŞME MOTORU — Faz 11: ErgeneAI'nın Omurgası
Hermes HQ'yu tek durak noktası yapar, sabah durum raporu, stratejik karar destek.

Yetkinlikler:
  1. Durum Raporu — ErgeneAI'nın anlık durumunu özetler
  2. Sabah Brifingi — Bilal'in güne başlarken görmek isteyeceği tek sayfa özet
  3. Stratejik Karar Destek — seçenekler + risk + öneri
  4. Bugünün Odağı — gün için en önemli 3 madde
  5. Her Şeyin Durumu — sistemdeki tüm verileri birleştirir

Kullanım:
  python3 koklesme_motoru.py --durum            # Anlık durum raporu
  python3 koklesme_motoru.py --sabah            # Sabah brifingi
  python3 koklesme_motoru.py --odak             # Bugünün odağı
  python3 koklesme_motoru.py --karar "soru"     # Karar destek
  python3 koklesme_motoru.py --hersey           # Her şeyin özeti
"""

import argparse
import glob
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════════════════

HERMES_HOME = Path(os.path.expanduser("~/.hermes"))
SCRIPTS_DIR = HERMES_HOME / "scripts"
SKILLS_DIR = HERMES_HOME / "skills" / "hermes-self"
MEMORIES_DIR = HERMES_HOME / "memories"
CHECKPOINT_DIR = HERMES_HOME / "checkpoint"
CHECKPOINT_FILE = CHECKPOINT_DIR / "checkpoint.json"
PROJELER_DIR = HERMES_HOME / "projeler"
RAPORLAR_DIR = HERMES_HOME / "raporlar"
FIKIR_HAVUZU_FILE = HERMES_HOME / "fikir_havuzu.json"
HOME_DIR = Path(os.path.expanduser("~"))

LEAD_FILES = sorted(HOME_DIR.glob("lead_listesi_*.json"))


def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] [{level}] {msg}", file=sys.stderr)


def _tarih():
    return datetime.now(timezone.utc).isoformat()


def _yerel_zaman():
    """Türkiye saati (UTC+3) ile şimdiki zaman."""
    return datetime.now(timezone(timedelta(hours=3))).strftime("%Y-%m-%d %H:%M:%S")


# ═══════════════════════════════════════════════════════════════════════════════
# YARDIMCI FONKSİYONLAR
# ═══════════════════════════════════════════════════════════════════════════════

def json_oku(dosya_yolu):
    """JSON dosyasını güvenli oku, hata durumunda None döndür."""
    try:
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, PermissionError) as e:
        log(f"Dosya okunamadı: {dosya_yolu} — {e}", "WARN")
        return None


def md_oku(dosya_yolu):
    """Markdown dosyasını güvenli oku, hata durumunda None döndür."""
    try:
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            return f.read()
    except (FileNotFoundError, PermissionError) as e:
        log(f"Dosya okunamadı: {dosya_yolu} — {e}", "WARN")
        return None


def lead_durumlari():
    """Tüm lead dosyalarından lead durumlarını topla."""
    durumlar = {"yeni": 0, "jeff_aktarilan": 0, "gonderildi": 0, "gorusme_ayarlandi": 0, "donusum": 0, "iptal": 0, "bilinmiyor": 0}
    toplam = 0
    lead_listesi = []

    for lf in LEAD_FILES:
        data = json_oku(lf)
        if not data:
            continue
        leadler = data.get("leadler") or data.get("leads") or []
        for lead in leadler:
            toplam += 1
            durum = lead.get("durum", "yeni")
            if durum in durumlar:
                durumlar[durum] += 1
            else:
                durumlar["bilinmiyor"] += 1
            lead_listesi.append({
                "isim": lead.get("isim", "İsimsiz"),
                "durum": durum,
                "puan": lead.get("puan", ""),
                "kategori": lead.get("kategori", ""),
            })

    return durumlar, toplam, lead_listesi


def proje_durumlari():
    """Projeler klasöründeki tüm projeleri oku."""
    projeler = []
    if not PROJELER_DIR.exists():
        return projeler

    for pf in sorted(PROJELER_DIR.glob("*.json")):
        data = json_oku(pf)
        if not data:
            continue
        if isinstance(data, list):
            projeler_data = data
        else:
            projeler_data = [data]
        for pdata in projeler_data:
            gorevler = pdata.get("gorevler", {})
            if isinstance(gorevler, list):
                tamamlanan = sum(1 for g in gorevler if isinstance(g, dict) and g.get("durum") == "tamamlandi")
                toplam = len(gorevler)
            elif isinstance(gorevler, dict):
                tamamlanan = sum(1 for g in gorevler.values() if isinstance(g, dict) and g.get("durum") == "tamamlandi")
                toplam = len(gorevler)
            else:
                tamamlanan = 0
                toplam = 0
            projeler.append({
                "ad": pdata.get("ad", pf.stem),
                "durum": pdata.get("durum", "bilinmiyor"),
                "gorev_durumu": f"{tamamlanan}/{toplam}",
                "tamamlanan": tamamlanan,
                "toplam": toplam,
                "dosya": str(pf),
            })

    return projeler


def rapor_durumlari():
    """Raporlar klasöründeki son raporları oku (son 24 saat)."""
    raporlar = []
    if not RAPORLAR_DIR.exists():
        return raporlar

    now = datetime.now()
    bir_gun_once = now - timedelta(hours=24)

    for rf in sorted(RAPORLAR_DIR.glob("*.md"), reverse=True):
        stat = rf.stat()
        mtime = datetime.fromtimestamp(stat.st_mtime)
        if mtime < bir_gun_once:
            continue
        icerik = md_oku(rf)
        if not icerik:
            continue
        # İlk satırı başlık olarak al
        baslik = rf.stem
        for line in icerik.split("\n"):
            line = line.strip()
            if line.startswith("#"):
                baslik = line.lstrip("#").strip()
                break
        raporlar.append({
            "baslik": baslik,
            "dosya": str(rf),
            "olusturma": mtime.strftime("%Y-%m-%d %H:%M:%S"),
        })

    return raporlar[:10]  # Son 10 rapor


def fikir_havuzu_oku():
    """Fikir havuzunu oku."""
    data = json_oku(FIKIR_HAVUZU_FILE)
    if not data:
        return {"ideas": [], "solutions": []}

    return data


def checkpoint_oku():
    """Checkpoint dosyasını oku."""
    return json_oku(CHECKPOINT_FILE)


def son_24_saat_isleri():
    """Son 24 saatte yapılan işleri özetle."""
    isler = []

    # Raporlara bak
    raporlar = rapor_durumlari()
    for r in raporlar:
        isler.append(f"📄 Rapor: {r['baslik']}")

    # Checkpoint'e bak
    cp = checkpoint_oku()
    if cp:
        isler.append(f"💾 Checkpoint güncellendi: {cp.get('son_guncelleme', 'bilinmiyor')}")

    # Lead dosyalarına bak
    for lf in LEAD_FILES:
        data = json_oku(lf)
        if data:
            adet = data.get("adet", len(data.get("leadler", [])))
            isler.append(f"📋 Lead listesi: {lf.name} ({adet} lead)")

    return isler if isler else ["Son 24 saatte kayıtlı iş bulunamadı."]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. DURUM RAPORU MODÜLÜ
# ═══════════════════════════════════════════════════════════════════════════════

def durum_raporu():
    """ErgeneAI'nın anlık durumunu özetler."""
    lead_durum, lead_toplam, lead_list = lead_durumlari()
    projeler = proje_durumlari()
    raporlar = rapor_durumlari()
    fikirler = fikir_havuzu_oku()
    cp = checkpoint_oku()
    isler = son_24_saat_isleri()

    # Aktif projeleri say
    aktif_projeler = [p for p in projeler if p["durum"] == "aktif"]
    tamamlanan_projeler = [p for p in projeler if p["durum"] == "tamamlandi"]

    # Lead durum dağılımını hesapla
    lead_dagilimi = {k: v for k, v in lead_durum.items() if v > 0}

    # Önerilen bugünkü odak
    onerilen_odak = []
    if lead_durum.get("yeni", 0) > 0:
        onerilen_odak.append(f"{lead_durum['yeni']} yeni lead'i değerlendir")
    if aktif_projeler:
        onerilen_odak.append(f"{len(aktif_projeler)} aktif projeyi ilerlet")
    if lead_durum.get("jeff_aktarilan", 0) > 0:
        onerilen_odak.append(f"{lead_durum['jeff_aktarilan']} jeff'e aktarılmış lead'i takip et")
    if not onerilen_odak:
        onerilen_odak.append("Yeni lead araştırması yap")
        onerilen_odak.append("Proje planlaması yap")

    # --- MD ÇIKTI ---
    md = []
    md.append(f"# 🔄 ErgeneAI — Anlık Durum Raporu")
    md.append(f"")
    md.append(f"**Tarih:** {_yerel_zaman()}")
    md.append(f"**Motor:** KÖKLEŞME (Faz 11)")
    md.append(f"")
    md.append(f"---")
    md.append(f"")
    md.append(f"## 📊 Lead Durumu")
    md.append(f"")
    md.append(f"**Toplam Lead:** {lead_toplam}")
    md.append(f"")
    for d, sayi in sorted(lead_dagilimi.items()):
        emoji = {"yeni": "🆕", "jeff_aktarilan": "🤖", "gonderildi": "📤",
                 "gorusme_ayarlandi": "📅", "donusum": "✅", "iptal": "❌", "bilinmiyor": "❓"}
        md.append(f"- {emoji.get(d, '📌')} **{d.title().replace('_', ' ')}:** {sayi}")
    md.append(f"")
    md.append(f"---")
    md.append(f"")
    md.append(f"## 🏗️ Proje Durumu")
    md.append(f"")
    if projeler:
        md.append(f"**Aktif Projeler:** {len(aktif_projeler)}")
        md.append(f"**Tamamlanan:** {len(tamamlanan_projeler)}")
        md.append(f"**Toplam:** {len(projeler)}")
        md.append(f"")
        for p in projeler:
            durum_emoji = "🟢" if p["durum"] == "aktif" else "✅" if p["durum"] == "tamamlandi" else "⏸️"
            md.append(f"- {durum_emoji} **{p['ad']}** — Görev: {p['gorev_durumu']} ({p['durum']})")
    else:
        md.append(f"Henüz proje bulunamadı.")
    md.append(f"")
    md.append(f"---")
    md.append(f"")
    md.append(f"## 📝 Son 24 Saatte Yapılan İşler")
    md.append(f"")
    for is_item in isler:
        md.append(f"- {is_item}")
    md.append(f"")
    md.append(f"---")
    md.append(f"")
    md.append(f"## ⏳ Bekleyen Aksiyonlar")
    md.append(f"")
    if cp and cp.get("bekleyen_isler"):
        for bi in cp["bekleyen_isler"]:
            md.append(f"- {bi}")
    else:
        md.append(f"- Checkpoint'te kayıtlı bekleyen iş yok.")
    md.append(f"")
    md.append(f"---")
    md.append(f"")
    md.append(f"## 🎯 Önerilen Bugünkü Odak")
    md.append(f"")
    for i, odak in enumerate(onerilen_odak[:3], 1):
        md.append(f"{i}. {odak}")
    md.append(f"")

    md_cikti = "\n".join(md)

    # --- JSON ÇIKTI ---
    json_cikti = {
        "zaman": _yerel_zaman(),
        "motor": "KÖKLEŞME (Faz 11)",
        "lead": {
            "toplam": lead_toplam,
            "dagilim": lead_dagilimi,
        },
        "projeler": {
            "toplam": len(projeler),
            "aktif": len(aktif_projeler),
            "tamamlanan": len(tamamlanan_projeler),
            "liste": projeler,
        },
        "son_24_saat": isler,
        "bekleyen_aksiyonlar": cp.get("bekleyen_isler", []) if cp else [],
        "onerilen_odak": onerilen_odak[:3],
        "checkpoint": cp,
    }

    return md_cikti, json_cikti


# ═══════════════════════════════════════════════════════════════════════════════
# 2. SABAH BRİFİNGİ MODÜLÜ
# ═══════════════════════════════════════════════════════════════════════════════

def sabah_brifingi():
    """Bilal'in güne başlarken görmek isteyeceği tek sayfa özet."""
    lead_durum, lead_toplam, lead_list = lead_durumlari()
    projeler = proje_durumlari()
    raporlar = rapor_durumlari()
    fikirler = fikir_havuzu_oku()
    cp = checkpoint_oku()
    isler = son_24_saat_isleri()

    aktif_projeler = [p for p in projeler if p["durum"] == "aktif"]

    # Pipeline'dan öncelik sırası
    yeni_leadler = [l for l in lead_list if l["durum"] == "yeni"]
    jeff_leadler = [l for l in lead_list if l["durum"] == "jeff_aktarilan"]

    md = []
    md.append(f"# 🌅 Günaydın Bilal! — {_yerel_zaman()}")
    md.append(f"")
    md.append(f"*ErgeneAI KÖKLEŞME Motoru tarafından hazırlanmıştır.*")
    md.append(f"")
    md.append(f"---")
    md.append(f"")
    md.append(f"## 📊 Özet Gösterge Paneli")
    md.append(f"")
    md.append(f"| Metrik | Değer |")
    md.append(f"|---|---|")
    md.append(f"| **Toplam Lead** | {lead_toplam} |")
    md.append(f"| **Yeni Lead** | {lead_durum.get('yeni', 0)} 🆕 |")
    md.append(f"| **Jeff'e Aktarılan** | {lead_durum.get('jeff_aktarilan', 0)} 🤖 |")
    md.append(f"| **Aktif Proje** | {len(aktif_projeler)} 🏗️ |")
    md.append(f"| **Bugünkü Rapor** | {len(raporlar)} 📄 |")
    md.append(f"| **Fikir Havuzu** | {len(fikirler.get('ideas', []))} 💡 |")
    md.append(f"")
    md.append(f"---")
    md.append(f"")
    md.append(f"## 🎯 Bugünün En Önemli 3 Maddesi")
    md.append(f"")

    onemli_maddeler = []
    if lead_durum.get("yeni", 0) > 0:
        en_iyi_yeni = yeni_leadler[:3]
        isimler = ", ".join(l["isim"][:30] for l in en_iyi_yeni)
        onemli_maddeler.append(f"**Değerlendirilecek Yeni Lead ({lead_durum['yeni']} adet):** {isimler}{'...' if len(yeni_leadler) > 3 else ''}")
    if jeff_leadler:
        isimler = ", ".join(l["isim"][:30] for l in jeff_leadler[:3])
        onemli_maddeler.append(f"**Jeff'e Aktarılan Lead Takibi ({len(jeff_leadler)} adet):** {isimler}{'...' if len(jeff_leadler) > 3 else ''}")
    if aktif_projeler:
        for p in aktif_projeler:
            onemli_maddeler.append(f"**Proje — {p['ad']}:** Görev {p['gorev_durumu']} tamamlandı")
    if fikirler.get("ideas"):
        onemli_maddeler.append(f"**Fikir Havuzu ({len(fikirler['ideas'])} fikir):** Yeni fikirleri değerlendir")
    if not onemli_maddeler:
        onemli_maddeler.append("**Sakin bir gün.** Yeni lead araştırması veya proje planlaması için iyi bir fırsat.")

    for i, madde in enumerate(onemli_maddeler, 1):
        md.append(f"### {i}. {madde}")
        md.append(f"")

    md.append(f"---")
    md.append(f"")
    md.append(f"## 📋 Lead Pipeline")
    md.append(f"")
    if lead_list:
        md.append(f"| # | Lead | Durum | Puan |")
        md.append(f"|---|---|---|---|")
        for i, l in enumerate(lead_list[:10], 1):
            md.append(f"| {i} | {l['isim'][:35]} | {l['durum']} | {l.get('puan', '-')} |")
        if len(lead_list) > 10:
            md.append(f"| ... | *{len(lead_list) - 10} lead daha* | | |")
    else:
        md.append(f"Lead listesi bulunamadı.")
    md.append(f"")

    md.append(f"---")
    md.append(f"")
    md.append(f"## 🏗️ Aktif Projeler")
    md.append(f"")
    if aktif_projeler:
        for p in aktif_projeler:
            md.append(f"- **{p['ad']}** — {p['gorev_durumu']} görev tamamlandı")
    else:
        md.append(f"Aktif proje bulunmuyor.")
    md.append(f"")

    md.append(f"---")
    md.append(f"")
    md.append(f"## 📝 Dünün Özeti")
    md.append(f"")
    for is_item in isler:
        md.append(f"- {is_item}")
    md.append(f"")

    md.append(f"---")
    md.append(f"")
    md.append(f"## 💡 Fikir Havuzu")
    md.append(f"")
    f_ideas = fikirler.get("ideas", [])
    if f_ideas:
        for idea in f_ideas[:5]:
            md.append(f"- {idea.get('idea', '')[:80]}")
    else:
        md.append(f"Henüz fikir eklenmemiş.")
    md.append(f"")
    md.append(f"---")
    md.append(f"")
    md.append(f"*İyi bir gün geçirmen dileğiyle, Bilal.*")
    md.append(f"*— KÖKLEŞME Motoru*")
    md.append(f"")

    md_cikti = "\n".join(md)

    # --- JSON ÇIKTI ---
    json_cikti = {
        "zaman": _yerel_zaman(),
        "motor": "KÖKLEŞME (Faz 11)",
        "tip": "sabah_brifingi",
        "ozet_panel": {
            "toplam_lead": lead_toplam,
            "yeni_lead": lead_durum.get("yeni", 0),
            "jeff_lead": lead_durum.get("jeff_aktarilan", 0),
            "aktif_proje": len(aktif_projeler),
            "bugunku_rapor": len(raporlar),
            "fikir_sayisi": len(fikirler.get("ideas", [])),
        },
        "onemli_maddeler": onemli_maddeler,
        "lead_pipeline": lead_list[:15],
        "aktif_projeler": aktif_projeler,
        "dunun_ozeti": isler,
        "fikir_havuzu": f_ideas[:10],
    }

    return md_cikti, json_cikti


# ═══════════════════════════════════════════════════════════════════════════════
# 3. STRATEJİK KARAR DESTEK MODÜLÜ
# ═══════════════════════════════════════════════════════════════════════════════

def karar_destek(soru):
    """Stratejik karar destek — seçenekler + risk + öneri."""
    lead_durum, lead_toplam, lead_list = lead_durumlari()
    projeler = proje_durumlari()
    fikirler = fikir_havuzu_oku()
    cp = checkpoint_oku()
    aktif_projeler = [p for p in projeler if p["durum"] == "aktif"]

    md = []
    md.append(f"# 🧠 Stratejik Karar Destek")
    md.append(f"")
    md.append(f"**Soru:** {soru}")
    md.append(f"**Tarih:** {_yerel_zaman()}")
    md.append(f"")
    md.append(f"---")
    md.append(f"")
    md.append(f"## 📊 Mevcut Durum")
    md.append(f"")
    md.append(f"- **Lead Pipeline:** {lead_toplam} lead ({lead_durum.get('yeni', 0)} yeni, {lead_durum.get('jeff_aktarilan', 0)} jeff'te)")
    md.append(f"- **Aktif Projeler:** {len(aktif_projeler)} adet")
    md.append(f"- **Fikir Havuzu:** {len(fikirler.get('ideas', []))} fikir, {len(fikirler.get('solutions', []))} çözüm")
    md.append(f"- **Checkpoint Durumu:** {'✅ Mevcut' if cp else '❌ Yok'}")
    md.append(f"")
    md.append(f"---")
    md.append(f"")
    md.append(f"## 🎯 Olası Seçenekler")
    md.append(f"")

    # Soruna göre seçenekler
    soru_lower = soru.lower()
    secenekler = []

    if any(k in soru_lower for k in ["lead", "müşteri", "musteri", "satış", "satis", "pazarlama"]):
        secenekler.append({
            "secenek": "Yeni lead'lere öncelik ver",
            "risk": "Düşük — mevcut lead'ler beklerse kaçabilir",
            "oneri": "Yeni lead'leri hızlıca değerlendir ve jeff'e aktar",
            "puan": 9,
        })
        secenekler.append({
            "secenek": "Jeff'e aktarılan lead'leri takip et",
            "risk": "Orta — beklerse ilgisini kaybedebilir",
            "oneri": "Jeff lead'lerine 24 saat içinde ikinci temas kur",
            "puan": 8,
        })
        secenekler.append({
            "secenek": "Yeni lead araştırması yap",
            "risk": "Düşük — kaynak israfı olabilir",
            "oneri": "Hedef kitleni daralt, spesifik sektörlere odaklan",
            "puan": 6,
        })

    elif any(k in soru_lower for k in ["proje", "geliştirme", "gelistirme", "teknik", "ürün", "urun"]):
        secenekler.append({
            "secenek": "Aktif projeleri tamamlamaya odaklan",
            "risk": "Düşük — yarıda kalan projeler birikir",
            "oneri": "En kritik projeyi belirle ve bitir",
            "puan": 9,
        })
        secenekler.append({
            "secenek": "Yeni proje başlat",
            "risk": "Yüksek — mevcut iş yükü artar",
            "oneri": "Ancak aktif projeler %80 tamamlandıysa başlat",
            "puan": 4,
        })
        secenekler.append({
            "secenek": "Proje dokümantasyonunu güncelle",
            "risk": "Düşük — acil değil ama önemli",
            "oneri": "Haftada 1 saat ayır",
            "puan": 5,
        })

    elif any(k in soru_lower for k in ["strateji", "stratejik", "yön", "yon", "gelecek", "büyüme", "buyume"]):
        secenekler.append({
            "secenek": "Mevcut lead pipeline'ını güçlendir",
            "risk": "Düşük — en hızlı getiri buradan",
            "oneri": "Lead dönüşüm oranını artırmaya odaklan",
            "puan": 8,
        })
        secenekler.append({
            "secenek": "Yeni pazar/kanal araştırması yap",
            "risk": "Orta — zaman alır, hemen dönüş olmaz",
            "oneri": "Haftada 2 saat ayır, uzun vadeli düşün",
            "puan": 6,
        })
        secenekler.append({
            "secenek": "Fikir havuzundan MVP çıkar",
            "risk": "Yüksek — kaynak gerektirir",
            "oneri": "En hızlı MVP'yi seç, 1 haftada çıkar",
            "puan": 5,
        })

    else:
        # Genel seçenekler
        secenekler.append({
            "secenek": "Lead pipeline'ını gözden geçir",
            "risk": "Düşük — her zaman faydalı",
            "oneri": "Hangi lead'lerin sıcak olduğunu belirle",
            "puan": 7,
        })
        secenekler.append({
            "secenek": "Proje durumunu değerlendir",
            "risk": "Düşük — mevcut durumu bilmek önemli",
            "oneri": "Hangi projelerin bloklandığını tespit et",
            "puan": 7,
        })
        secenekler.append({
            "secenek": "Fikir havuzundan bir fikir seç ve üzerinde çalış",
            "risk": "Orta — dikkat dağıtabilir",
            "oneri": "En az kaynakla en çok değer yaratacak fikri seç",
            "puan": 5,
        })

    for s in sorted(secenekler, key=lambda x: x["puan"], reverse=True):
        puan_stars = "⭐" * (s["puan"] // 2)
        md.append(f"### {puan_stars} {s['secenek']}")
        md.append(f"")
        md.append(f"- **Risk:** {s['risk']}")
        md.append(f"- **Öneri:** {s['oneri']}")
        md.append(f"")

    md.append(f"---")
    md.append(f"")
    md.append(f"## 🏆 Önerilen Karar")
    md.append(f"")
    if secenekler:
        en_iyi = max(secenekler, key=lambda x: x["puan"])
        md.append(f"**{en_iyi['secenek']}** ⭐ ({en_iyi['puan']}/10)")
        md.append(f"")
        md.append(f"*{en_iyi['oneri']}*")
    else:
        md.append(f"Sorunuz için uygun seçenek bulunamadı. Lütfen daha spesifik bir soru sorun.")
    md.append(f"")

    md_cikti = "\n".join(md)

    json_cikti = {
        "zaman": _yerel_zaman(),
        "soru": soru,
        "mevcut_durum": {
            "lead": {"toplam": lead_toplam, "yeni": lead_durum.get("yeni", 0), "jeff": lead_durum.get("jeff_aktarilan", 0)},
            "aktif_proje": len(aktif_projeler),
            "fikir_sayisi": len(fikirler.get("ideas", [])),
        },
        "secenekler": sorted(secenekler, key=lambda x: x["puan"], reverse=True),
        "onerilen_karar": max(secenekler, key=lambda x: x["puan"]) if secenekler else None,
    }

    return md_cikti, json_cikti


# ═══════════════════════════════════════════════════════════════════════════════
# 4. BUGÜNÜN ODAĞI MODÜLÜ
# ═══════════════════════════════════════════════════════════════════════════════

def bugunun_odagi():
    """Gün için en önemli 3 maddeyi belirler."""
    lead_durum, lead_toplam, lead_list = lead_durumlari()
    projeler = proje_durumlari()
    fikirler = fikir_havuzu_oku()
    aktif_projeler = [p for p in projeler if p["durum"] == "aktif"]

    yeni_leadler = [l for l in lead_list if l["durum"] == "yeni"]
    jeff_leadler = [l for l in lead_list if l["durum"] == "jeff_aktarilan"]

    odak_maddeler = []

    # Madde 1: Lead'ler
    if yeni_leadler:
        ilk_lead = yeni_leadler[0]["isim"][:40]
        odak_maddeler.append({
            "sira": 1,
            "baslik": f"🆕 Yeni Lead'leri Değerlendir ({len(yeni_leadler)} adet)",
            "detay": f"İlk sırada: {ilk_lead}",
            "neden": "Yeni lead'ler sıcakken yakalanmalı, beklerse ilgisini kaybeder.",
            "eylem": f"Her lead için hızlı bir ön değerlendirme yap ve jeff'e aktar.",
        })
    else:
        odak_maddeler.append({
            "sira": 1,
            "baslik": "🔍 Yeni Lead Araştırması",
            "detay": "Pipeline'da yeni lead yok",
            "neden": "Sürekli yeni lead akışı olmazsa büyüme durur.",
            "eylem": "Google Maps ve sektör dizinlerini tara.",
        })

    # Madde 2: Jeff Lead Takibi
    if jeff_leadler:
        odak_maddeler.append({
            "sira": 2,
            "baslik": f"🤖 Jeff Lead'lerini Takip Et ({len(jeff_leadler)} adet)",
            "detay": f"Jeff'e aktarılmış lead'lerin durumunu kontrol et",
            "neden": "İletişime geçilmeyi bekleyen lead'ler kaçabilir.",
            "eylem": "İkinci temas kur, randevu ayarla.",
        })
    elif aktif_projeler:
        odak_maddeler.append({
            "sira": 2,
            "baslik": f"🏗️ Aktif Projeleri İlerlet ({len(aktif_projeler)} adet)",
            "detay": f"{aktif_projeler[0]['ad']} — {aktif_projeler[0]['gorev_durumu']}",
            "neden": "Projeleri tamamlamak uzun vadeli değer yaratır.",
            "eylem": "En kritik görevi belirle ve bugün bitir.",
        })
    else:
        odak_maddeler.append({
            "sira": 2,
            "baslik": "📋 Proje Planlaması Yap",
            "detay": "Aktif proje bulunmuyor",
            "neden": "Projeler olmadan büyüme stratejik olmaz.",
            "eylem": "Yeni bir proje belirle ve roadmap çıkar.",
        })

    # Madde 3: Fikir/Strateji
    f_ideas = fikirler.get("ideas", [])
    if f_ideas:
        odak_maddeler.append({
            "sira": 3,
            "baslik": f"💡 Fikir Havuzundan Birini Seç ({len(f_ideas)} fikir)",
            "detay": f"{f_ideas[0].get('idea', '')[:60]}",
            "neden": "Fikirler beklerse değer kaybeder.",
            "eylem": "En hızlı uygulanabilir fikri seç ve MVP planı çıkar.",
        })
    else:
        odak_maddeler.append({
            "sira": 3,
            "baslik": "📊 Haftalık Strateji Gözden Geçirme",
            "detay": "Checkpoint ve raporları kontrol et",
            "neden": "Düzenli strateji kontrolü başarıyı getirir.",
            "eylem": "Hedefleri gözden geçir, öncelikleri güncelle.",
        })

    md = []
    md.append(f"# 🎯 Bugünün Odağı — {_yerel_zaman()}")
    md.append(f"")
    md.append(f"*KÖKLEŞME Motoru tarafından önceliklendirilmiştir.*")
    md.append(f"")

    for madde in odak_maddeler:
        md.append(f"---")
        md.append(f"")
        md.append(f"## {madde['sira']}. {madde['baslik']}")
        md.append(f"")
        md.append(f"- **Detay:** {madde['detay']}")
        md.append(f"- **Neden:** {madde['neden']}")
        md.append(f"- **Eylem:** {madde['eylem']}")
        md.append(f"")

    md_cikti = "\n".join(md)

    json_cikti = {
        "zaman": _yerel_zaman(),
        "odak_maddeler": odak_maddeler,
        "istatistik": {
            "yeni_lead": len(yeni_leadler),
            "jeff_lead": len(jeff_leadler),
            "aktif_proje": len(aktif_projeler),
            "fikir_sayisi": len(f_ideas),
        },
    }

    return md_cikti, json_cikti


# ═══════════════════════════════════════════════════════════════════════════════
# 5. HER ŞEYİN DURUMU MODÜLÜ
# ═══════════════════════════════════════════════════════════════════════════════

def herseyin_durumu():
    """Sistemdeki tüm verileri birleştir ve tek bir özet çıkar."""
    lead_durum, lead_toplam, lead_list = lead_durumlari()
    projeler = proje_durumlari()
    raporlar = rapor_durumlari()
    fikirler = fikir_havuzu_oku()
    cp = checkpoint_oku()
    isler = son_24_saat_isleri()

    # Tüm sistem dosyalarını tara
    sistem_dosyalari = {
        "lead_dosyalari": [str(lf) for lf in LEAD_FILES],
        "proje_dosyalari": [str(pf) for pf in sorted(PROJELER_DIR.glob("*.json"))] if PROJELER_DIR.exists() else [],
        "rapor_dosyalari": [str(rf) for rf in sorted(RAPORLAR_DIR.glob("*.md"))] if RAPORLAR_DIR.exists() else [],
        "script_dosyalari": [str(sf) for sf in sorted(SCRIPTS_DIR.glob("*.py")) + sorted(SCRIPTS_DIR.glob("*.sh"))],
        "checkpoint": str(CHECKPOINT_FILE) if CHECKPOINT_FILE.exists() else None,
        "fikir_havuzu": str(FIKIR_HAVUZU_FILE) if FIKIR_HAVUZU_FILE.exists() else None,
    }

    json_cikti = {
        "zaman": _yerel_zaman(),
        "motor": "KÖKLEŞME (Faz 11)",
        "tip": "herseyin_durumu",
        "lead": {
            "toplam": lead_toplam,
            "dagilim": {k: v for k, v in lead_durum.items() if v > 0},
            "liste": lead_list,
        },
        "projeler": projeler,
        "raporlar": raporlar,
        "fikir_havuzu": fikirler,
        "checkpoint": cp,
        "son_24_saat": isler,
        "sistem_dosyalari": sistem_dosyalari,
    }

    # MD özet
    md = []
    md.append(f"# 🏢 ErgeneAI — Her Şeyin Durumu")
    md.append(f"")
    md.append(f"**Tarih:** {_yerel_zaman()}")
    md.append(f"**Motor:** KÖKLEŞME (Faz 11)")
    md.append(f"")
    md.append(f"---")
    md.append(f"")
    md.append(f"## 📊 Kapsamlı Durum Özeti")
    md.append(f"")
    md.append(f"**Lead:** {lead_toplam} toplam | {lead_durum.get('yeni', 0)} yeni | {lead_durum.get('jeff_aktarilan', 0)} jeff'te")
    md.append(f"**Projeler:** {len(projeler)} toplam | {len([p for p in projeler if p['durum']=='aktif'])} aktif")
    md.append(f"**Raporlar (son 24s):** {len(raporlar)} adet")
    md.append(f"**Fikirler:** {len(fikirler.get('ideas', []))} fikir | {len(fikirler.get('solutions', []))} çözüm")
    md.append(f"**Checkpoint:** {'✅ Mevcut' if cp else '❌ Yok'}")
    md.append(f"")
    md.append(f"### Lead Dosyaları")
    md.append(f"")
    for lf in sistem_dosyalari["lead_dosyalari"]:
        md.append(f"- {os.path.basename(lf)}")
    md.append(f"")
    md.append(f"### Projeler")
    md.append(f"")
    for p in projeler:
        md.append(f"- **{p['ad']}** — {p['durum']} ({p['gorev_durumu']})")
    md.append(f"")
    md.append(f"### Son Raporlar")
    md.append(f"")
    for r in raporlar[:5]:
        md.append(f"- 📄 {r['baslik'][:60]}")
    md.append(f"")
    md.append(f"### İş Merkezi — Script ve Skill Sayısı")
    md.append(f"")
    md.append(f"- Python Script: {len(list(SCRIPTS_DIR.glob('*.py')))}")
    md.append(f"- Shell Script: {len(list(SCRIPTS_DIR.glob('*.sh')))}")
    md.append(f"- Skill Klasörleri: {len([d for d in SKILLS_DIR.iterdir() if d.is_dir()]) if SKILLS_DIR.exists() else 0}")
    md.append(f"")

    return md, json_cikti


# ═══════════════════════════════════════════════════════════════════════════════
# CLI ANA MODÜLÜ
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="KÖKLEŞME MOTORU — ErgeneAI'nın Omurgası (Faz 11)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python3 koklesme_motoru.py --durum          # Anlık durum raporu
  python3 koklesme_motoru.py --sabah          # Sabah brifingi
  python3 koklesme_motoru.py --odak           # Bugünün odağı
  python3 koklesme_motoru.py --karar "soru"   # Karar destek
  python3 koklesme_motoru.py --hersey         # Her şeyin özeti
  python3 koklesme_motoru.py --durum --json   # JSON çıktı
        """
    )
    parser.add_argument("--durum", action="store_true", help="Anlık durum raporu")
    parser.add_argument("--sabah", action="store_true", help="Sabah brifingi")
    parser.add_argument("--odak", action="store_true", help="Bugünün odağı")
    parser.add_argument("--karar", type=str, metavar="\"soru\"", help="Stratejik karar destek")
    parser.add_argument("--hersey", action="store_true", help="Her şeyin özeti")
    parser.add_argument("--json", action="store_true", help="Sadece JSON çıktı (MD yerine)")

    args = parser.parse_args()

    # Eğer hiçbir argüman verilmemişse, yardım göster
    if not any([args.durum, args.sabah, args.odak, args.karar, args.hersey]):
        parser.print_help()
        sys.exit(1)

    # Modları çalıştır
    if args.durum:
        md, js = durum_raporu()
        if args.json:
            print(json.dumps(js, ensure_ascii=False, indent=2))
        else:
            print(md)

    elif args.sabah:
        md, js = sabah_brifingi()
        if args.json:
            print(json.dumps(js, ensure_ascii=False, indent=2))
        else:
            print(md)

    elif args.odak:
        md, js = bugunun_odagi()
        if args.json:
            print(json.dumps(js, ensure_ascii=False, indent=2))
        else:
            print(md)

    elif args.karar:
        md, js = karar_destek(args.karar)
        if args.json:
            print(json.dumps(js, ensure_ascii=False, indent=2))
        else:
            print(md)

    elif args.hersey:
        md, js = herseyin_durumu()
        if args.json:
            print(json.dumps(js, ensure_ascii=False, indent=2))
        else:
            print("\n".join(md))


if __name__ == "__main__":
    main()
