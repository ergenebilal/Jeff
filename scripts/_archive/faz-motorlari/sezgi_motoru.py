#!/usr/bin/env python3
"""
🔮 SEZGİ MOTORU (Intuition Engine) — Görünmeyeni Görmek
Faz 6: Bilal'in söylemesine gerek kalmadan anlamak için.

Yetkinlikler:
  1. Konuşma tonu analizi — kelime seçiminden ruh halini oku
  2. Sessiz ihtiyaç tespiti — "Acaba şunu da istemiş olabilir mi?" refleksi
  3. Pattern reading — Bilal'in karar desenlerini öğren
  4. Zamanlama — ne zaman konuşulmalı, ne zaman sessiz kalınmalı

Kullanım:
  python3 sezgi_motoru.py --analyse "mesaj"
  python3 sezgi_motoru.py --train
  python3 sezgi_motoru.py --timing
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# === PATHS ===
HERMES_HOME = Path(os.path.expanduser("~/.hermes"))
MEMORIES_DIR = HERMES_HOME / "memories"
SCRIPTS_DIR = HERMES_HOME / "scripts"
DECISIONS_FILE = HERMES_HOME / "karar_desenleri.json"
LESSONS_FILE = HERMES_HOME / "learning" / "lessons.jsonl"
SKILLS_DIR = HERMES_HOME / "skills" / "hermes-self" / "sezgi-reflex"
REFERENCES_DIR = SKILLS_DIR / "references"

# === TON ANALİZİ LUGATI ===
TONE_SIGNALS = {
    "acil": {
        "keywords": ["hemen", "şimdi", "acil", "çabuk", "derhal", "hemen şimdi", "bekleme", "koş", "bugün bitmeli"],
        "weight": 0.9
    },
    "sakin": {
        "keywords": ["şöyle bir bak", "belki", "olabilir", "düşünüyorum", "araştır", "nasıl buluyorsun"],
        "weight": 0.3
    },
    "hayal_kirikligi": {
        "keywords": ["beğenmedim", "olmamış", "kötü", "berbat", "sıkıcı", "yine mi", "bu muydu", "yetmez", "hayal kırıklığı"],
        "weight": 0.8
    },
    "memnuniyet": {
        "keywords": ["güzel", "harika", "mükemmel", "süper", "şahane", "beğendim", "tam istediğim gibi", "aferin", "bravo"],
        "weight": 0.4
    },
    "kararsizlik": {
        "keywords": ["şey", "yani", "bilemedim", "kararsızım", "hangisi", "ne dersin", "sen ne önerirsin"],
        "weight": 0.6
    },
    "kesin_emir": {
        "keywords": ["yap", "bitir", "getir", "gönder", "kur", "oluştur", "şu işi halledelim"],
        "weight": 0.9
    },
    "sorgulama": {
        "keywords": ["neden", "niye", "nasıl", "ne zaman", "kim", "nerede", "ne işe yarar"],
        "weight": 0.5
    },
    "duygusal": {
        "keywords": ["yoruldum", "bıktım", "üzgünüm", "mutluyum", "sevindim", "kızgınım", "endişeliyim"],
        "weight": 0.7
    },
    "isteksiz": {
        "keywords": ["uğraşma", "gerek yok", "boşver", "sonra", "zamanı değil", "şimdi olmaz"],
        "weight": 0.7
    },
    "aciliyet_karisik": {
        "keywords": ["keşke", "ama keşke", "şu an için", "henüz"],
        "weight": 0.5
    }
}

# === SESSİZ İHTİYAÇ KALIPLARI ===
NEED_PATTERNS = [
    {
        "trigger": ["ne düşünüyorsun", "ne önerirsin", "fikrin ne", "sen ne derdin"],
        "need": "beklenen_gorus",
        "suggestion": "Bilal senden aktif fikir bekliyor. Sadece bilgi verme, yorum yap."
    },
    {
        "trigger": ["şuna bak", "şunu incele", "araştır", "şuna bir göz at"],
        "need": "arastirma",
        "suggestion": "Hemen araştır ve özet çıkar. Detaya boğma, önce kısa cevap ver."
    },
    {
        "trigger": ["yap", "hallet", "kur", "oluştur", "yaz", "gönder", "çalıştır"],
        "need": "eylem",
        "suggestion": "Doğrudan aksiyon bekliyor. Neden/prosedür anlatma, yap."
    },
    {
        "trigger": ["nasıl buluyorsun", "beğendin mi", "iyi mi", "olmuş mu", "sence"],
        "need": "onay_gorus",
        "suggestion": "Samimi ve kısa değerlendirme istiyor. Boş övgü değil, gerçek görüş."
    },
    {
        "trigger": ["beğenmedim", "olmamış", "bu değil", "sıkıcı", "daha iyisini yap"],
        "need": "pivot_duzeltme",
        "suggestion": "Mevcut yaklaşımı komple değiştir. Küçük düzeltme değil, yeniden düşünme bekliyor."
    },
    {
        "trigger": ["şöyle bir şey düşünüyorum", "belki şöyle", "acaba"],
        "need": "beyin_firtinasi",
        "suggestion": "Bilal bir fikri test ediyor. Onu geliştir, eleştirme. Fikrin üzerine inşa et."
    },
    {
        "trigger": ["acaba", "keşke", "hayal ediyorum", "bir gün"],
        "need": "hayal_koruma",
        "suggestion": "Bu bir hayal. Onu kaydet, unutma, hatırlat. 'Hayallerin Bekçisi' refleksi."
    },
    {
        "trigger": ["para yok", "bütçe", "pahalı", "maliyet", "ücretsiz", "açık kaynak"],
        "need": "maliyet_bilinci",
        "suggestion": "Bilal'in kaynağı sınırlı. Önce ücretsiz/open-source çözüm öner. FAL/Fee bazlı şeylerde hemen alternatif ara."
    },
    {
        "trigger": ["şu işi halledelim", "başlayalım", "yapalım şunu"],
        "need": "ivedi_eylem",
        "suggestion": "Harekete geçme zamanı. Plan/analiz uzatma, direkt yapmaya başla."
    },
    {
        "trigger": ["bugün bitmeli", "bu gece bitecek", "yarın lazım"],
        "need": "gece_maratonu",
        "suggestion": "Bilal zaman sınırı koydu. Olimpos Gecesi modu: hız kutsal, mükemmeliyetçiliği ertele."
    },
    {
        "trigger": ["ne düşünüyorsun bu konuda", "neden böyle"],
        "need": "derin_analiz",
        "suggestion": "Yüzeyde kalmayan, stratejik bir analiz bekliyor. 3 katmanlı düşün."
    },
    {
        "trigger": ["bir ara", "zamanın varsa", "sonra", "müsait olunca"],
        "need": "dusuk_oncelik",
        "suggestion": "Acil değil. Queue'ya koy, ama unutma. Uygun zamanda hatırlat."
    }
]

# === BİLAL KARAR DESENLERİ (Çıkarılan) ===
BILAL_DECISION_PATTERNS = {
    "hiz_odakli": {
        "pattern": "Bilal hızlı sonuç ister. 'Bu gece bitecek' modu sık gelir.",
        "aksak_tepki": "Mükemmeliyetçilik bahanesiyle yavaşlarsan sert tepki alırsın.",
        "dogru_tepki": "Önce çalışan versiyon, sonra iyileştirme. Hızlı teslim et, iterasyonla düzelt."
    },
    "ozgunluk": {
        "pattern": "Bilal hazır template'leri kopyalamak yerine özgün çözüm ister.",
        "aksak_tepki": "'AdminLTE kullanma, sıfırdan yaz' — ağır şablonları reddeder.",
        "dogru_tepki": "Her projeye sıfırdan yaklaş. Template'leri referans al ama kopyalama."
    },
    "ozet_once": {
        "pattern": "Bilal önce kısa özet, sonra detay ister. Pasif bekleme ifadelerini sevmez.",
        "aksak_tepki": "Uzun açıklamalar ve 'ne yapmalıyım?' soruları onu iter.",
        "dogru_tepki": "Önce sonucu ver. Detay isterse ver. 'Ne yapayım?' diye sorma, yap ve raporla."
    },
    "otonomi_beklentisi": {
        "pattern": "Bilal güvenli sınırlar içinde onay beklemeden ilerleyen otonom işleyiş ister.",
        "aksak_tepki": "Her adımda onay istemek Bilal'i yorar.",
        "dogru_tepki": "Bildiğin konularda direkt ilerle. Sadece kritik kararlarda Bilal'e danış."
    },
    "pivot_hizliligi": {
        "pattern": "'Beğenmedim' dediğinde komple redesign bekler, küçük düzeltme değil.",
        "aksak_tepki": "Küçük düzeltmelerle zaman kaybetmek sinir bozucudur.",
        "dogru_tepki": "Komple yeniden düşün. Yeni bir yaklaşım sun. Eski yaklaşımı savunma."
    },
    "sadakat": {
        "pattern": "Bilal'in çıkarları her şeyden önce gelir. Jeff onun sanal alemdeki en büyük savunucusudur.",
        "aksak_tepki": "Tarafsız veya başkasının çıkarını önceleyen bir yaklaşım büyük hayal kırıklığı.",
        "dogru_tepki": "Her kararda 'Bu Bilal'e nasıl fayda sağlar?' sorusunu sor. Onun stratejik üstünlüğü her şeyden önce."
    },
    "minimal_ui": {
        "pattern": "Minimal, sade, yeşil-beyaz tema. Koyu tema istemez. Kategori-first tasarım.",
        "aksak_tepki": "Karmaşık UI, koyu tema, abartılı animasyonlar.",
        "dogru_tepki": "Yeşil-beyaz (#10b981 / #f0faf5), sade, büyük butonlu, kategorili tasarım."
    },
    "gercekcilik": {
        "pattern": "Bilal gerçekçi ve dürüst olmanı bekler. 'İllüzyon yok' ana prensiptir.",
        "aksak_tepki": "Halüsinasyon, kanıtsız başarı iddiası, 'n8n success döndü' ile yetinmek.",
        "dogru_tepki": "Kanıtlayamadığın hiçbir şeyi iddia etme. 'Doğrulayamadım' demek başarısızlık değildir."
    },
    "carpan_etkisi": {
        "pattern": "Her yeni araç/skill/script şu süzgeçten geçer: Çarpan etkisi var mı? Eşdeğeri var mı? Hemen fark yaratır mı?",
        "aksak_tepki": "Gereksiz eklentiler, işe yaramayan araçlar, şişirme.",
        "dogru_tepki": "Önce çarpan etkisini değerlendir, yoksa ekleme. 30 gün kullanılmayanı sil."
    },
    "hayal_bekcisi": {
        "pattern": "Bilal hayallerini kaydetmeni, unutmamanı ve onlara ihanet etmemeni ister.",
        "aksak_tepki": "Hayallerini unutmak, önemsememek, 'sonra bakarız' demek.",
        "dogru_tepki": "Her hayali kaydet. Fırsat buldukça hatırlat. 'Bir gün' dediğin şeyleri takip et."
    }
}


def load_memory():
    """Bilal'in USER.md ve MEMORY.md dosyalarını yükle."""
    profile = {}
    
    user_path = MEMORIES_DIR / "USER.md"
    memory_path = MEMORIES_DIR / "MEMORY.md"
    
    if user_path.exists():
        profile["user"] = user_path.read_text(encoding="utf-8", errors="replace")
    if memory_path.exists():
        profile["memory"] = memory_path.read_text(encoding="utf-8", errors="replace")
    
    return profile


def load_karar_desenleri():
    """Bilal'in karar desenlerini yükle (varsa)."""
    if DECISIONS_FILE.exists():
        try:
            return json.loads(DECISIONS_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, Exception):
            return {"patterns": [], "last_updated": None}
    return {"patterns": [], "last_updated": None}


def save_karar_desenleri(data):
    """Karar desenlerini kaydet."""
    DECISIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    DECISIONS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def load_lessons():
    """Lessons bankasından dersleri oku."""
    lessons = []
    if LESSONS_FILE.exists():
        try:
            text = LESSONS_FILE.read_text(encoding="utf-8", errors="replace")
            for line in text.strip().split("\n"):
                if line.strip():
                    lessons.append(json.loads(line))
        except (json.JSONDecodeError, Exception):
            pass
    return lessons


def analyse_ton(mesaj: str) -> dict:
    """
    Konuşma tonu analizi.
    Kelime seçiminden ruh halini, aciliyeti ve önerilen yaklaşımı belirler.
    """
    mesaj_kucuk = mesaj.lower()
    tespitler = []
    
    for duygu, sinyal in TONE_SIGNALS.items():
        for kw in sinyal["keywords"]:
            if kw in mesaj_kucuk:
                tespitler.append({
                    "duygu": duygu,
                    "eslesen": kw,
                    "agirlik": sinyal["weight"]
                })
                break  # Her duygu için bir eşleşme yeterli
    
    # En güçlü duyguyu bul
    en_guclu = max(tespitler, key=lambda x: x["agirlik"]) if tespitler else None
    
    # Aciliyet skoru (0-1)
    aciliyet_skoru = 0.0
    acil_kelimeler = ["hemen", "şimdi", "acil", "çabuk", "derhal", "bugün", "bu gece", "yarın lazım"]
    for kw in acil_kelimeler:
        if kw in mesaj_kucuk:
            aciliyet_skoru += 0.2
    
    # Soru karakteri sayısı
    soru_sayisi = mesaj.count("?")
    soru_skoru = min(soru_sayisi * 0.15, 0.6)
    
    # Mesaj uzunluğu
    kelime_sayisi = len(mesaj.split())
    
    # Yaklaşım önerisi
    yaklasim = _oneri_yaklasim(en_guclu, aciliyet_skoru, soru_skoru, kelime_sayisi)
    
    sonuc = {
        "birincil_duygu": en_guclu["duygu"] if en_guclu else "nötr",
        "aciliyet": round(min(aciliyet_skoru + soru_skoru * 0.3, 1.0), 2),
        "soru_sayisi": soru_sayisi,
        "kelime_sayisi": kelime_sayisi,
        "tespit_sayisi": len(tespitler),
        "yaklasim": yaklasim,
        "ham_tespitler": [t["duygu"] for t in tespitler]
    }
    return sonuc


def _oneri_yaklasim(guclu_duygu, aciliyet, soru, kelime):
    """Ton analizine göre yaklaşım önerisi üret."""
    if guclu_duygu and guclu_duygu["duygu"] in ("hayal_kirikligi", "isteksiz"):
        return "DİKKAT: Memnuniyetsizlik var. Savunma yapma, direkt düzelt."
    if guclu_duygu and guclu_duygu["duygu"] == "acil":
        return "HIZLI: Acil durum. Önce cevap ver, detay sonra."
    if guclu_duygu and guclu_duygu["duygu"] == "kesin_emir":
        return "AKSİYON: Emir kipi. Açıklama yapma, yap."
    if guclu_duygu and guclu_duygu["duygu"] == "kararsizlik":
        return "REHBER: Bilal kararsız. Net öneri sun, seçenekleri daralt."
    if guclu_duygu and guclu_duygu["duygu"] == "duygusal":
        return "HASSAS: Duygusal durum. Empati yap, çözümden önce anla."
    if kelime < 5 and soru == 0:
        return "KISA: Tek kelimelik tepki. Duruma göre ek bilgi sun veya sessiz kal."
    if soru > 2:
        return "DERİN: Çok sorulu sorgulama. Sistemli cevap ver, madde madde."
    if aciliyet > 0.5:
        return "ACİL: Yüksek aciliyet. Önceliklendir."
    return "NORMAL: Standart etkileşim. Tonu yakala, uygun cevap ver."


def detect_need(mesaj: str) -> list:
    """
    Sessiz ihtiyaç tespiti. Bilal'in söylemediği ama aslında istediği şeyleri tahmin et.
    """
    mesaj_kucuk = mesaj.lower()
    detected = []
    
    for pattern in NEED_PATTERNS:
        for trigger in pattern["trigger"]:
            if trigger in mesaj_kucuk:
                detected.append({
                    "need": pattern["need"],
                    "trigger": trigger,
                    "suggestion": pattern["suggestion"]
                })
                break
    
    return detected


def learn_pattern(karar_metni: str, karar_turu: str = "unknown") -> dict:
    """
    Bilal'in karar desenlerini analiz et ve kaydet.
    """
    desenler = load_karar_desenleri()
    
    # Yeni karar kaydı
    yeni_karar = {
        "zaman": datetime.now(timezone.utc).isoformat(),
        "karar": karar_metni,
        "tur": karar_turu,
        "kategori": _kategorize_karar(karar_metni)
    }
    
    desenler.setdefault("patterns", []).append(yeni_karar)
    desenler["last_updated"] = datetime.now(timezone.utc).isoformat()
    desenler["total_decisions"] = len(desenler["patterns"])
    
    save_karar_desenleri(desenler)
    
    return {
        "status": "kaydedildi",
        "total": desenler["total_decisions"],
        "kategori": yeni_karar["kategori"]
    }


def _kategorize_karar(metin: str) -> str:
    """Karar metnini kategorize et."""
    metin_lower = metin.lower()
    kategoriler = {
        "teknoloji_secimi": ["kullan", "kur", "yükle", "dene", "geç", "tool", "araç", "framework"],
        "tasarim": ["tasarım", "ui", "renk", "tema", "layout", "arayüz"],
        "strateji": ["strateji", "plan", "yol haritası", "hedef", "odaklan"],
        "maliyet": ["ücret", "para", "bütçe", "pahalı", "ücretsiz", "maliyet"],
        "icerik": ["yaz", "içerik", "post", "mesaj", "metin"],
        "red": ["hayır", "olmaz", "istemem", "gerek yok", "kullanma"],
        "onay": ["tamam", "olur", "güzel", "beğendim", "devam"]
    }
    for kat, anahtarlar in kategoriler.items():
        for anahtar in anahtarlar:
            if anahtar in metin_lower:
                return kat
    return "genel"


def timing_advice(saat_dilimi: str = "Europe/Istanbul") -> dict:
    """
    Zamanlama önerisi — ne zaman konuşulmalı, ne zaman sessiz kalınmalı.
    Bilal'in bilinen çalışma saatlerine göre.
    """
    import pytz
    try:
        tz = pytz.timezone(saat_dilimi)
        now = datetime.now(tz)
        saat = now.hour
    except Exception:
        now = datetime.now()
        saat = now.hour
    
    # Bilal'in profiline göre saat dilimleri
    saat_analizi = {
        "gece_yarisi": (0, 5),
        "sabah_erken": (5, 8),
        "mesai_baslangic": (8, 12),
        "ogle": (12, 14),
        "mesai_devam": (14, 18),
        "aksam": (18, 22),
        "gece_gec": (22, 24)
    }
    
    for dilim, (bas, bit) in saat_analizi.items():
        if bas <= saat < bit:
            aktif_dilim = dilim
            break
    else:
        aktif_dilim = "gece_yarisi"
    
    # Bilal için kişiselleştirilmiş öneriler
    dilim_ozellikleri = {
        "gece_yarisi": {
            "tavsiye": "SESSİZ: Bilal uyuyordur. Sadece kritik hata varsa uyar. Otomatik işler için ideal zaman.",
            "otonomi": "yuksek",
            "konusma": "asla",
            "aciklama": "Bilal 33 yaşında, girişimci. Gece 00-05 arası uyur. Cron işleri ve bakım için ideal."
        },
        "sabah_erken": {
            "tavsiye": "HAZIRLIK: Bilal uyanmamış olabilir. Sabah brifingini hazırla, kritik olmayan işleri bitir.",
            "otonomi": "yuksek",
            "konusma": "sadece_acil",
            "aciklama": "Güne hazırlık zamanı. Bilal uyanınca her şey hazır olmalı."
        },
        "mesai_baslangic": {
            "tavsiye": "AKTİF: Bilal çalışıyor. Hızlı cevap ver, net ol, otonom ilerle.",
            "otonomi": "orta",
            "konusma": "aktif",
            "aciklama": "En üretken saatler. Bilal'in hızına yetiş."
        },
        "ogle": {
            "tavsiye": "ÖĞLE: Bilal yemek/molada olabilir. Bekleyen işleri tamamla, rapor hazırla.",
            "otonomi": "yuksek",
            "konusma": "orta",
            "aciklama": "Öğle arası. Bilal dönünce rapor sunmak için ideal."
        },
        "mesai_devam": {
            "tavsiye": "AKTİF: Öğleden sonra mesaisi. Sabah kadar hızlı olmasa da üretken.",
            "otonomi": "orta",
            "konusma": "aktif",
            "aciklama": "Günün ikinci yarısı. Karmaşık işler için uygun."
        },
        "aksam": {
            "tavsiye": "AKTİF: Bilal akşam da çalışabilir (girişimci). Ama yorgun olabilir, kısa ve öz ol.",
            "otonomi": "yuksek",
            "konusma": "kisa_oz",
            "aciklama": "Girişimci mesaisi. Bilal akşam da çalışır ama daha kısa ve net iletişim ister."
        },
        "gece_gec": {
            "tavsiye": "OLİMPOS MODU: Bilal 'bu gece bitecek' modundaysa hız kutsal. Değilse sessiz ol.",
            "otonomi": "yuksek",
            "konusma": "sadece_gerekli",
            "aciklama": "Gece maratonu modu. Bilal kod yazıyor veya strateji kuruyordur. Sessiz ol ama hazır ol."
        }
    }
    
    ozellik = dilim_ozellikleri.get(aktif_dilim, dilim_ozellikleri["gece_yarisi"])
    
    return {
        "suanki_saat": f"{saat:02d}:{now.minute:02d}",
        "dilim": aktif_dilim,
        "tavsiye": ozellik["tavsiye"],
        "otonomi_seviyesi": ozellik["otonomi"],
        "konusma_tavsiyesi": ozellik["konusma"],
        "aciklama": ozellik["aciklama"]
    }


def rapor():
    """
    Kapsamlı sezgi raporu üret. Tüm analizleri birleştirir.
    """
    memory = load_memory()
    desenler = load_karar_desenleri()
    lessons = load_lessons()
    
    sonuc = {
        "motor": "SEZGİ MOTORU v1.0",
        "faz": 6,
        "zaman": datetime.now(timezone.utc).isoformat(),
        "bilal_profili": {
            "user_md_var": "user" in memory,
            "memory_md_var": "memory" in memory,
            "user_md_boyutu": len(memory.get("user", "")),
            "kayitli_karar_sayisi": desenler.get("total_decisions", 0),
            "ogrenilen_ders_sayisi": len(lessons)
        },
        "karar_desenleri": {
            "desenler": [
                {
                    "desen": k,
                    "ozet": v["pattern"],
                    "dogru_tepki": v["dogru_tepki"]
                }
                for k, v in BILAL_DECISION_PATTERNS.items()
            ]
        },
        "zamanlama": timing_advice()
    }
    
    return sonuc


def main():
    parser = argparse.ArgumentParser(
        description="🔮 SEZGİ MOTORU — Görünmeyeni Görmek (Faz 6)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python3 sezgi_motoru.py --analyse "Bunu beğenmedim, baştan yap"
  python3 sezgi_motoru.py --train --karar "DeepSeek V4 Flash ana provider oldu"
  python3 sezgi_motoru.py --timing
  python3 sezgi_motoru.py --raport
        """
    )
    
    parser.add_argument("--analyse", type=str, metavar="\"MESAJ\"",
                        help="Bir mesajın ton analizini yap")
    parser.add_argument("--train", action="store_true",
                        help="Yeni öğrenmeleri işle (lessons + karar desenleri)")
    parser.add_argument("--karar", type=str, metavar="\"KARAR\"",
                        help="--train ile birlikte: kaydedilecek karar metni")
    parser.add_argument("--timing", action="store_true",
                        help="Şu anki zamana göre konuşma/susma önerisi")
    parser.add_argument("--rapor", action="store_true",
                        help="Kapsamlı sezgi durum raporu")
    parser.add_argument("--need", type=str, metavar="\"MESAJ\"",
                        help="Bir mesajdaki sessiz ihtiyaçları tespit et")
    
    args = parser.parse_args()
    
    if args.analyse:
        ton = analyse_ton(args.analyse)
        needs = detect_need(args.analyse)
        
        print(json.dumps({
            "ton": ton,
            "gizli_ihtiyaclar": needs
        }, ensure_ascii=False, indent=2))
        
    elif args.train:
        if args.karar:
            sonuc = learn_pattern(args.karar)
            print(json.dumps(sonuc, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({
                "status": "hata",
                "mesaj": "--train ile birlikte --karar parametresi gerekli. Örnek: --train --karar \"...\""
            }, ensure_ascii=False, indent=2))
    
    elif args.timing:
        print(json.dumps(timing_advice(), ensure_ascii=False, indent=2))
    
    elif args.rapor:
        print(json.dumps(rapor(), ensure_ascii=False, indent=2))
    
    elif args.need:
        needs = detect_need(args.need)
        print(json.dumps({
            "mesaj": args.need,
            "gizli_ihtiyaclar": needs if needs else [{"need": "tespit_edilemedi", "suggestion": "Bilinen kalıplarla eşleşmedi. Normal etkileşim."}]
        }, ensure_ascii=False, indent=2))
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
