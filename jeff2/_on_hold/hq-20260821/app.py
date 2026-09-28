#!/usr/bin/env python3
"""
ErgeneAI Kabinesi — Gerçek İş Yönetim Sistemi
Template yok. Her bakan gerçek görev alır, durum takip edilir, onay mekanizması çalışır.
"""
import json, os, datetime, random, subprocess, threading, uuid, fcntl, secrets, shutil, functools
from pathlib import Path
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
BASE = Path(__file__).parent
FEED_DOSYA = BASE / "feed.jsonl"
TASKS_DOSYA = BASE / "tasks.jsonl"
DECISIONS_DOSYA = BASE / "decisions.jsonl"

EMIRLER_DOSYA = BASE / "emirler.jsonl"
AUTO_REMEDIATE_LOG = BASE / "auto_remediate_log.jsonl"
CB_DOSYA = BASE / "circuit_breaker_state.jsonl"
TASK_QUEUE_DOSYA = BASE / "task_queue.jsonl"
RETRY_LOG = BASE / "retry_log.jsonl"
HEALTH_LOG = BASE / "health_check_log.jsonl"
API_CALL_LOG = BASE / "api_call_log.jsonl"
LEAD_PIPELINE_1 = BASE / "lead_pipeline_1.jsonl"
LEAD_PIPELINE_2 = BASE / "lead_pipeline_2.jsonl"
LEADS_DOSYA = BASE / "leads.jsonl"
MODE_DOSYA = BASE / "mode.json"
PERSONAL_MEMORY = Path.home() / ".hermes" / "personal_memory.yaml"
PERSONAL_BACKUP = Path.home() / ".hermes" / "personal_memory_backup.yaml"
PERSONAL_LOG = BASE / "personal_update_log.jsonl"

BAKANLAR = {
    "buyume": {"id":"buyume","isim":"Hırslı","emoji":"📈","renk":"#22C55E","rol":"Büyüme Bakanı","kisa":"Büyüme","kpiler":{"Pipeline":"40 lead","Contacted":4,"Replies":0,"Emailsiz":31}},
    "icerik": {"id":"icerik","isim":"Estetik","emoji":"🎨","renk":"#81E36F","rol":"İçerik Bakanı","kisa":"İçerik","kpiler":{"Post":0,"Ürün":0,"Dönüşüm%":0}},
    "teslimat":{"id":"teslimat","isim":"Pragmatik","emoji":"⚙️","renk":"#3B82F6","rol":"Sistem Bakanı","kisa":"Sistem","kpiler":{"n8n":3,"Cron":6,"Uptime":"%99.7"}},
    "finans":  {"id":"finans","isim":"Maliyetçi","emoji":"💰","renk":"#F59E0B","rol":"Hazine Bakanı","kisa":"Hazine","kpiler":{"Token/24h":0,"Maliyet":"$0.00","Risk":"DÜŞÜK"}},
    "hafiza":  {"id":"hafiza","isim":"Bilge","emoji":"🧠","renk":"#8B5CF6","rol":"Arşiv Bakanı","kisa":"Arşiv","kpiler":{"SOP":0,"Ders":0,"Skill":6}},
}
SIRA = ["buyume","icerik","teslimat","finans","hafiza"]

GELIR_TIPLERI = ["hizmet","dijital_urun","agent_paketi","icerik_talebi","yeni_deney"]
GELIR_ETIKET = {"hizmet":"💼 Hizmet","dijital_urun":"📦 Dijital Ürün","agent_paketi":"🤖 Agent Paketi","icerik_talebi":"📱 İçerik Talebi","yeni_deney":"🧪 Yeni Deney"}

DURUMLAR = ["calisiyor","tamamlandi","takildi","onay_bekliyor","duzeltme_gerekli"]
DURUM_RENK = {"calisiyor":"#3B82F6","tamamlandi":"#81E36F","takildi":"#EF4444","onay_bekliyor":"#F59E0B","duzeltme_gerekli":"#EF4444"}
DURUM_ETIKET = {"calisiyor":"🔄 Çalışıyor","tamamlandi":"✅ Tamamlandı","takildi":"❌ Takıldı","onay_bekliyor":"⏳ Onay Bekliyor","duzeltme_gerekli":"🔧 Düzeltme Gerekli"}

# ─── Görev Tanımları (Her bakanın yapabileceği gerçek işler) ───────────────

GOREV_SABLON = {
    "buyume": [
        {"baslik":"Pipeline taraması","amac":"Mevcut lead'leri say, emailsizleri bul, önceliklendir","gorev":"AgencyOS'ten pipeline verisini çek. Kaç lead var, kaçı contacted, kaçı emailsiz? Raporla.","beklenen_sonuc":"Pipeline özet raporu","risk":"Düşük","onay_gerekli":False,"gelir_tipi":"hizmet"},
        {"baslik":"Email enrichment","amac":"Emailsiz lead'lere email bul","gorev":"En yüksek skorlu 5 emailsiz lead'in websitesini tara, email adresi bul.","beklenen_sonuc":"En az 2 email bulunması","risk":"Orta — manuel emek gerek","onay_gerekli":True,"gelir_tipi":"hizmet"},
        {"baslik":"Yeni niş keşfi","amac":"Potansiyel yeni sektörleri tara","gorev":"Bursa'da dijital pazarlama ihtiyacı olabilecek 3 yeni sektör belirle. Örnek lead çıkar.","beklenen_sonuc":"3 yeni niş + örnek lead","risk":"Düşük","onay_gerekli":False,"gelir_tipi":"yeni_deney"},
    ],
    "icerik": [
        {"baslik":"Post konsepti","amac":"Yeni Instagram post konsepti hazırla","gorev":"Hedef sektör için 5 slidelık carousel konsepti çıkar. Konu, hook, renk paleti, örnek görsel prompt.","beklenen_sonuc":"1 post konsepti (kapak→problem→çözüm→değer→CTA)","risk":"Düşük","onay_gerekli":True,"gelir_tipi":"icerik_talebi"},
        {"baslik":"Dijital ürün fikri","amac":"Satılabilir bir dijital ürün konsepti çıkar","gorev":"ErgeneAI'nin know-how'ını paketleyebileceğin bir dijital ürün fikri bul. Hedef kitle, fiyat aralığı, içerik planı.","beklenen_sonuc":"1 ürün fikri + fiyat önerisi","risk":"Orta — pazar testi gerek","onay_gerekli":True,"gelir_tipi":"dijital_urun"},
    ],
    "teslimat": [
        {"baslik":"Sistem sağlık kontrolü","amac":"Tüm sistemlerin çalıştığını doğrula","gorev":"n8n workflow'larını, cron job'ları ve disk durumunu kontrol et. Sorun varsa raporla.","beklenen_sonuc":"Sistem durum raporu","risk":"Düşük","onay_gerekli":False,"gelir_tipi":"hizmet"},
        {"baslik":"Otomasyon iyileştirme","amac":"Tekrarlayan işleri otomatize et","gorev":"Günlük lead taraması için bir n8n workflow'u tasarla. Adımları yaz, çalıştırmak için onay bekle.","beklenen_sonuc":"Workflow tasarımı","risk":"Düşük","onay_gerekli":True,"gelir_tipi":"agent_paketi"},
    ],
    "finans": [
        {"baslik":"Maliyet raporu","amac":"Son 24 saatlik token ve API maliyetini çıkar","gorev":"AgencyOS'ten AI cost verisini çek. En pahalı işlemi bul. Tasarruf önerisi hazırla.","beklenen_sonuc":"Maliyet raporu + öneri","risk":"Düşük","onay_gerekli":False,"gelir_tipi":"hizmet"},
        {"baslik":"Yeni gelir kanalı fizibilite","amac":"Yeni bir gelir kanalının maliyet/getiri analizini yap","gorev":"Önerilen yeni gelir kanalı için: kurulum maliyeti, aylık işletme maliyeti, beklenen getiri, başabaş noktası.","beklenen_sonuc":"Fizibilite raporu","risk":"Orta — veri varsayımları","onay_gerekli":True,"gelir_tipi":"yeni_deney"},
    ],
    "hafiza": [
        {"baslik":"SOP güncelleme","amac":"Son tamamlanan işlerden SOP çıkar","gorev":"Son 24 saatte tamamlanan işleri tara. Tekrarlanabilir bir desen varsa SOP olarak yaz.","beklenen_sonuc":"En az 1 yeni SOP","risk":"Düşük","onay_gerekli":False,"gelir_tipi":"agent_paketi"},
        {"baslik":"Skill bakımı","amac":"Eski skill'leri güncelle, hatalı olanları düzelt","gorev":"Kullanılmayan veya hatalı skill'leri tespit et. Güncelleme önerisi hazırla.","beklenen_sonuc":"Skill bakım raporu","risk":"Düşük","onay_gerekli":False,"gelir_tipi":"agent_paketi"},
    ],
}

# ─── Mod Sistemi ─────────────────────────────────────────────────────────────

MODLAR = {
    "is": "💼 İş",
    "ozel": "🏠 Özel",
    "sosyal": "🎉 Sosyal"
}
_MODE_LOCK = threading.Lock()

def _mode_oku():
    if MODE_DOSYA.exists():
        try:
            with open(MODE_DOSYA) as f:
                fcntl.flock(f, fcntl.LOCK_SH)
                try:
                    data = json.load(f)
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)
                m = data.get("aktif_mod", "is")
                if m in MODLAR:
                    return m
        except Exception:
            pass
    return "is"

def _mode_yaz(mod):
    with _MODE_LOCK:
        tmp = MODE_DOSYA.with_suffix(".tmp")
        with open(tmp, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                json.dump({"aktif_mod": mod, "guncelleme": datetime.datetime.now().isoformat()}, f, ensure_ascii=False)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
        tmp.replace(MODE_DOSYA)

# ─── Lead migration: tasks.jsonl içindeki durum="new" kayıtlarını leads.jsonl'ye taşı ─
def _migrate_leads():
    if not TASKS_DOSYA.exists():
        return
    try:
        with open(TASKS_DOSYA) as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                rows = [json.loads(l) for l in f if l.strip()]
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
        lead_rows = [r for r in rows if r.get("durum") == "new"]
        task_rows = [r for r in rows if r.get("durum") != "new"]
        if lead_rows and not LEADS_DOSYA.exists():
            # migrate only once: write leads, rewrite tasks without leads
            with open(LEADS_DOSYA, "w") as lf:
                fcntl.flock(lf, fcntl.LOCK_EX)
                try:
                    for r in lead_rows:
                        lf.write(json.dumps(r, ensure_ascii=False) + "\n")
                finally:
                    fcntl.flock(lf, fcntl.LOCK_UN)
            with open(TASKS_DOSYA, "w") as tf:
                fcntl.flock(tf, fcntl.LOCK_EX)
                try:
                    for r in task_rows:
                        tf.write(json.dumps(r, ensure_ascii=False) + "\n")
                finally:
                    fcntl.flock(tf, fcntl.LOCK_UN)
    except Exception:
        pass

_migrate_leads()

AKTIF_MOD = _mode_oku()

# ─── HQ Auth Token ─────────────────────────────────────────────────────────
def _get_hq_token():
    tok = os.environ.get("JEFF_HQ_TOKEN")
    if tok:
        return tok.strip()
    cfg = Path.home() / ".hermes" / "config.yaml"
    if cfg.exists():
        try:
            with open(cfg) as f:
                for line in f:
                    if line.strip().startswith("jeff_hq_token:"):
                        v = line.split(":", 1)[1].strip().strip('"').strip("'")
                        if v:
                            return v
        except Exception:
            pass
    # generate random, persist to config.yaml
    tok = secrets.token_urlsafe(32)
    try:
        cfg.parent.mkdir(parents=True, exist_ok=True)
        with open(cfg, "a") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.write(f"\njeff_hq_token: \"{tok}\"\n")
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    except Exception:
        pass
    return tok

HQ_TOKEN = _get_hq_token()

def require_auth(f):
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("X-API-Token", "")
        if token != HQ_TOKEN:
            return jsonify({"hata": "unauthorized", "kod": 401}), 401
        return f(*args, **kwargs)
    return wrapper

@app.before_request
def _auth_guard():
    # Exempt health/root endpoints
    if request.path in ("/", "/health", "/health/quick"):
        return None
    if request.path.startswith("/api/"):
        token = request.headers.get("X-API-Token", "")
        if token != HQ_TOKEN:
            return jsonify({"hata": "unauthorized", "kod": 401}), 401
    return None

# ─── Yardımcılar ─────────────────────────────────────────────────────────────

def feed_yaz(kim, mesaj, tip="mesaj", mod=None):
    # K3 auto-remediate: feed format >200 karakter truncate
    if len(mesaj) > 200:
        ozgun_len = len(mesaj)
        mesaj = mesaj[:197] + "..."
        auto_remediate_yap("K3", "feed truncate", f"{ozgun_len}→200 karakter")
    with open(FEED_DOSYA, "a") as f:
        f.write(json.dumps({
            "t": datetime.datetime.now().isoformat(),
            "k": kim,
            "m": mesaj,
            "tip": tip,
            "mod": mod or AKTIF_MOD
        }, ensure_ascii=False) + "\n")

def feed_oku(adet=50, mod=None):
    if not FEED_DOSYA.exists(): return []
    with open(FEED_DOSYA) as f:
        mesajlar = [json.loads(l) for l in f.readlines() if l.strip()]
    if mod:
        mesajlar = [m for m in mesajlar if m.get("mod", "is") == mod]
    return mesajlar[-adet:]

# ─── Karar Günlüğü ───────────────────────────────────────────────────────────

KARAR_ETIKETLERI = {
    "strateji": "🎯 Strateji",
    "finans": "💰 Finans",
    "iliskiler": "🤝 İlişkiler",
    "urun": "📦 Ürün",
    "teknik": "⚙️ Teknik",
    "oncelik": "📋 Öncelik"
}

def karar_ekle(konu, karar, gerekce, veren="Bilal", etiketler=None, ozel_hayat=False, riskli=False, alternatifler=None, referans=None, mod=None):
    kayit = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": datetime.datetime.now().isoformat(),
        "konu": konu,
        "karar": karar,
        "gerekce": gerekce,
        "alternatifler": alternatifler,
        "veren": veren,
        "durum": "active",
        "etiketler": etiketler or [],
        "ozel_hayat": ozel_hayat,
        "riskli": riskli,
        "referans": referans,
        "mod": mod or AKTIF_MOD,
        "guncelleme": datetime.datetime.now().isoformat()
    }
    with open(DECISIONS_DOSYA, "a") as f:
        f.write(json.dumps(kayit, ensure_ascii=False) + "\n")
    if not ozel_hayat:
        etiket_str = " ".join([KARAR_ETIKETLERI.get(e, e) for e in (etiketler or [])])
        feed_yaz("🧠 Bilge", f"📝 Karar kaydedildi: {konu} ({etiket_str.strip()})", "karar")
    return kayit

def kararlar_oku(ozel_hayat_dahil=False, limit=50, mod=None):
    if not DECISIONS_DOSYA.exists(): return []
    with open(DECISIONS_DOSYA) as f:
        kayitlar = [json.loads(l) for l in f.readlines() if l.strip()]
    if not ozel_hayat_dahil:
        kayitlar = [k for k in kayitlar if not k.get("ozel_hayat", False)]
    if mod:
        kayitlar = [k for k in kayitlar if k.get("mod", "is") == mod]
    return kayitlar[-limit:]

def karar_bul(sorgu, ozel_hayat_dahil=False, mod=None):
    kararlar = kararlar_oku(ozel_hayat_dahil=ozel_hayat_dahil, mod=mod, limit=500)
    s = sorgu.lower()
    sonuc = []
    for k in kararlar:
        if (s in k.get("konu","").lower() or
            s in k.get("karar","").lower() or
            s in k.get("gerekce","").lower() or
            any(s in e.lower() for e in k.get("etiketler",[]))):
            sonuc.append(k)
    return sonuc

def karar_guncelle(karar_id, alan, deger):
    if not DECISIONS_DOSYA.exists(): return False
    with open(DECISIONS_DOSYA) as f:
        kararlar = [json.loads(l) for l in f.readlines() if l.strip()]
    bulundu = False
    for k in kararlar:
        if k["id"] == karar_id:
            k[alan] = deger
            k["guncelleme"] = datetime.datetime.now().isoformat()
            bulundu = True
            break
    if bulundu:
        with open(DECISIONS_DOSYA, "w") as f:
            for k in kararlar:
                f.write(json.dumps(k, ensure_ascii=False) + "\n")
    return bulundu

def son_kararlar(adet=10, ozel_hayat_dahil=False, mod=None):
    return list(reversed(kararlar_oku(ozel_hayat_dahil=ozel_hayat_dahil, limit=adet, mod=mod)))

# ─── Brifing Sistemi ────────────────────────────────────────────────────────

def brief_is():
    """İş modu sabah brifingi — max 7 madde"""
    import datetime as dt
    now = dt.datetime.now()
    day_ago = (now - dt.timedelta(hours=24)).isoformat()
    
    pipeline = "40 lead, 36 new, 4 contacted, 31 emailsiz"
    tasks = tasks_oku()
    bekleyen = [t for t in tasks if t.get("durum") == "onay_bekliyor"]
    takili = [t for t in tasks if t.get("durum") == "takildi"][-2:]
    kararlar = son_kararlar(adet=3, mod="is")
    
    BAKAN_SIRA = ["buyume","icerik","teslimat","finans","hafiza"]
    bakan_durum = []
    for bid in BAKAN_SIRA:
        b = BAKANLAR.get(bid, {})
        son_task = [t for t in tasks if t.get("bakan_id") == bid]
        durum = "boşta"
        if son_task:
            son = son_task[-1]
            durum = {"calisiyor":"çalışıyor","tamamlandi":"hazır","takildi":"❌ takıldı","onay_bekliyor":"⏳ onay","duzeltme_gerekli":"🔧 düzeltme"}.get(son.get("durum",""), "?")
        bakan_durum.append(f"{b.get('emoji','')} {b.get('isim','')}: {durum}")
    
    uyari = ""
    tum_kararlar = kararlar_oku(mod="is")
    for k in tum_kararlar:
        if k.get("durum") == "active" and k.get("timestamp","")[:10] < (now - dt.timedelta(days=30)).strftime("%Y-%m-%d"):
            uyari = f"⚠️ Bekleyen karar: {k.get('konu','')[:40]} ({k.get('timestamp','')[:10]})"
            break
    
    son_feed = feed_oku(adet=50, mod="is")
    son_24 = [f for f in son_feed if f.get("t","") >= day_ago]
    sessiz = len(son_24) == 0 and len(bekleyen) == 0 and len(takili) == 0 and len(kararlar) == 0
    
    maddeler = []
    if not sessiz:
        maddeler.append({"sira":1,"baslik":"Pipeline","icerik":pipeline})
        maddeler.append({"sira":2,"baslik":"Bekleyen Onay","icerik":f"{len(bekleyen)} adet onay bekliyor" if bekleyen else "Onay bekleyen yok"})
        if takili:
            maddeler.append({"sira":3,"baslik":"Takılan İşler","icerik":" - ".join([t.get("baslik","?")[:30] for t in takili])})
        if kararlar:
            maddeler.append({"sira":4,"baslik":"Son Kararlar","icerik":", ".join([k.get("konu","")[:40] for k in kararlar])})
        maddeler.append({"sira":5,"baslik":"Bakan Durumu","icerik":" | ".join(bakan_durum)})
    
    return {"mod":"is","sessiz":sessiz,"baslik":"💼 İş Modu — Sabah Brifingi","maddeler":maddeler,"uyari":uyari,"personal":personal_oku("is")}

def brief_ozel():
    """Özel mod sabah brifingi — max 5 madde + personal"""
    import datetime as dt
    now = dt.datetime.now()
    day_ago = (now - dt.timedelta(hours=24)).isoformat()
    kararlar = son_kararlar(adet=3, ozel_hayat_dahil=True, mod="ozel")
    son_feed = feed_oku(adet=50, mod="ozel")
    son_24 = [f for f in son_feed if f.get("t","") >= day_ago]
    sessiz = len(kararlar) == 0 and len(son_24) == 0
    maddeler = []
    # Personal sağlık durumu
    maddeler.append({"sira":1,"baslik":"🌅 Bugün","icerik":f"Uyku: ~7.5 saat — Egzersiz: düzensiz — Rutin: sabah kahve + öğlene kadar iş"})
    if kararlar:
        maddeler.append({"sira":2,"baslik":"Özel Kararlar","icerik":", ".join([k.get("konu","")[:40] for k in kararlar])})
    if son_24:
        maddeler.append({"sira":3,"baslik":"Dün Ne Oldu","icerik":son_24[-1].get("m","")[:80]})
    return {"mod":"ozel","sessiz":sessiz,"baslik":"🏠 Özel Mod — Sabah Brifingi","maddeler":maddeler,"personal":personal_oku("ozel")}

def brief_sosyal():
    """Sosyal mod sabah brifingi — max 4 madde + personal"""
    import datetime as dt
    now = dt.datetime.now()
    day_ago = (now - dt.timedelta(hours=24)).isoformat()
    kararlar = son_kararlar(adet=2, mod="sosyal")
    son_feed = feed_oku(adet=50, mod="sosyal")
    son_24 = [f for f in son_feed if f.get("t","") >= day_ago]
    sessiz = len(kararlar) == 0 and len(son_24) == 0
    maddeler = []
    maddeler.append({"sira":1,"baslik":"🎉 Sosyal Mod","icerik":"Hafta sonu — iş konuşma yok"})
    if kararlar:
        maddeler.append({"sira":2,"baslik":"Sosyal Kararlar","icerik":kararlar[0].get("konu","")[:40]})
    if son_24:
        maddeler.append({"sira":3,"baslik":"Planlar","icerik":son_24[-1].get("m","")[:80]})
    return {"mod":"sosyal","sessiz":sessiz,"baslik":"🎉 Sosyal Mod — Sabah Brifingi","maddeler":maddeler,"personal":personal_oku("sosyal")}

# ─── Task Engine ─────────────────────────────────────────────────────────────

def task_olustur(bakan_id, sablon_idx=None, ozel_gorev=None):
    """Bakana yeni bir task oluştur"""
    bakan = BAKANLAR[bakan_id]
    sablon = None
    if sablon_idx is not None:
        sablon = GOREV_SABLON[bakan_id][sablon_idx % len(GOREV_SABLON[bakan_id])]
    
    task = {
        "id": str(uuid.uuid4())[:8],
        "bakan_id": bakan_id,
        "bakan_isim": bakan["isim"],
        "bakan_emoji": bakan["emoji"],
        "baslik": sablon["baslik"] if sablon else "Özel görev",
        "amac": sablon["amac"] if sablon else "Açıklama bekliyor",
        "gorev": sablon["gorev"] if sablon else (ozel_gorev or "Görev tanımı bekliyor"),
        "beklenen_sonuc": sablon["beklenen_sonuc"] if sablon else "Belirtilmemiş",
        "risk": sablon["risk"] if sablon else "Bilinmiyor",
        "onay_gerekli": sablon["onay_gerekli"] if sablon else False,
        "gelir_tipi": sablon["gelir_tipi"] if sablon else "hizmet",
        "durum": "onay_bekliyor" if sablon and sablon["onay_gerekli"] else "calisiyor",
        "atanan": f"OpenCode ({bakan['isim']})",
        "sonuc": None,
        "red_sebebi": None,
        "olusturma": datetime.datetime.now().isoformat(),
        "guncelleme": datetime.datetime.now().isoformat()
    }
    
    with open(TASKS_DOSYA, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.write(json.dumps(task, ensure_ascii=False)+"\n")
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    
    if task["onay_gerekli"]:
        feed_yaz("🧿 Patronus", f"⏳ Onay gerekli — {bakan['isim']}: {task['baslik']}")
    
    return task

def tasks_oku(filtre=None):
    """Task'ları dosyadan oku, opsiyonel filtrele (fcntl SH lock ile)"""
    if not TASKS_DOSYA.exists(): return []
    with open(TASKS_DOSYA) as f:
        fcntl.flock(f, fcntl.LOCK_SH)
        try:
            tasks = [json.loads(l) for l in f.readlines() if l.strip()]
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    if filtre:
        tasks = [t for t in tasks if t.get("durum") == filtre]
    return tasks

def task_guncelle(task_id, alan, deger):
    """Task güncelle (read-modify-write fcntl LOCK_EX ile)"""
    with _MODE_LOCK:
        if not TASKS_DOSYA.exists():
            return
        with open(TASKS_DOSYA, "r+") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                tasks = [json.loads(l) for l in f.readlines() if l.strip()]
                for t in tasks:
                    if t["id"] == task_id:
                        t[alan] = deger
                        t["guncelleme"] = datetime.datetime.now().isoformat()
                        break
                f.seek(0)
                f.truncate()
                for t in tasks:
                    f.write(json.dumps(t, ensure_ascii=False)+"\n")
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

# ─── Subagent (OpenCode) ────────────────────────────────────────────────────

def opencode_calistir(bakan_id, gorev, timeout=60):
    """OpenCode'a gönder, sonucu al"""
    bakan = BAKANLAR[bakan_id]
    prompt = f"""Sen ErgeneAI Kabinesi'nin {bakan['emoji']} {bakan['isim']} ({bakan['rol']})'sın.

GÖREV: {gorev}

Beklenen çıktı formatı:
- DURUM: (çalışıyor/tamamlandı/takıldı)
- BULGU: ne buldun/ne yaptın
- ÖNERİ: varsa önerin
"""
    try:
        sonuc = subprocess.run(
            ["opencode","run",".","--model","deepseek-v4-flash",prompt],
            capture_output=True,text=True,timeout=timeout,cwd=str(BASE),
            env={**os.environ,"HERMES_PROFILE":"default"}
        )
        cikti = (sonuc.stdout or sonuc.stderr or "").strip()[:600]
        return ("tamamlandi", cikti) if cikti else ("takildi", "Çıktı alınamadı")
    except subprocess.TimeoutExpired:
        return ("takildi", "Zaman aşımı (60sn)")
    except Exception as e:
        return ("takildi", f"Hata: {str(e)}")

# ─── Kabine Context Kernel ────────────────────────────────────────────────────
# Tüm bakan çağrılarında ortak olan 8 kural. Her bakan önce bunu alır.
KERNEL = """\
#K KABİNE KERNEL (tüm bakanlar ortak)
#K1 KALİTE: Vasat iş gösterme. Veri yoksa uydurma. Template yasak.
#K2 LİMİT: Bir görevde max 3 işlem. Fazlası için toplu işlem öner.
#K3 SESSİZLİK: Sorun yoksa sessiz. Sadece 🟡/🔴/❌/blokaj raporla.
#K4 30GÜN: "30 gün sonra işe yarar mı?" Hayırsa kaydetme.
#K5 YETKİ: Yeşil=kendi karar. Sarı=karar ver+Patronus'a bilgi. Kırmızı=Patronus'a havale.
#K6 ÖNCE SOP: Görev öncesi kendi SOP'larını kontrol et. Varsa izle, yoksa normal akış.
#K7 FEED: Max 200 karakter. Emoji+sonuç. Süreç anlatma.
#K8 HATA: 1 retry. Çözülmezse "takıldı". Sonsuz döngü yasak. Uydurma çıktı yasak.
"""

# ─── Bakan Özel Blokları ──────────────────────────────────────────────────────

OZEL_BUYUME = """\
#B HIRSLI (Büyüme)
#B1 ENRICHMENT LOG: Her lead için 7 alan zorunlu: provider(web_extract/manual/hunter/apollo), lead_id, attempt(1/2/3), result(found/not_found/skipped), email(bulunan/-), cost($), next_channel(email/whatsapp/phone/none). Eksik alan=görev tamamlanmamış.
#B2 KANAL: Email→WhatsApp geçişi ANCAK 4 koşul: (1)email yok (2)telefon/WA var (3)email denenmedi/7gün geçti (4)sektör uygun. İHLAL: email varken WA geçişi, kanalsız lead'e "WA çıkıldı", email yanıt almış lead'i WA'tan rahatsız.
#B3 BOŞ LEAD: Ne email ne telefon ne WA yoksa ZORUNLU TARAMA. "Ulaşamıyorum" diye atlamak ihlal.
#B4 ÖNCELİK: Diş > Otel > Saç ekimi > Diğer.
"""

OZEL_ICERIK = """\
#B ESTETİK (İçerik)
#B1 TEMPLATE YASAK: Her içerik özgün olmalı. Kopyala-yapıştır yasak.
#B2 MARKA: ErgeneAI marka kimliğine uy: yenilikçi, güvenilir, teknoloji odaklı. Template hissi otomatik RED.
#B3 KALİTE: Referans=Akare salon reklamı (gerçek mekan, doğal ışık, samimi). Altı amatör.
#B4 AKIŞ: FLUX prompt yaz → FAL.ai ile üret → Canva'da manuel düzenle.
#B5 ONAY: Yeni içerik konsepti Patronus onayı gerek. Onaysız yayın yasak.
"""

OZEL_TESLIMAT = """\
#B PRAGMATİK (Sistem)
#B1 DEPLOY: Emergency deploy kendi yetkisinde. Planlı deploy için Patronus onayı.
#B2 HARCAMA: $50+ harcama CEO onayı. $50 altı serbest.
#B3 BACKUP: Her config/deploy değişikliği öncesi backup al. Backup yoksa değişiklik yapma.
#B4 SAĞLIK: Sistem sağlığı her görevden önce kontrol edilir. Sorun varsa önce onu çöz.
#B5 LOG: n8n/cron/docker değişiklikleri loglanır. Logsuz değişiklik yasak.
"""

OZEL_FINANS = """\
#B MALİYETÇİ (Hazine)
#B1 ENRICHMENT COST: feed.jsonl'den ENRICHMENT_LOG satırlarını oku. est_cost topla. Lead başı maliyet çıkar.
#B2 ALARM: Günlük enrichment $1 🟡. Haftalık $5 🔴. Lead başı $0.50 🔴.
#B3 PROVIDER: Her provider için call/email oranı çıkar. Verimsiz provider'ı raporla.
#B4 VETO: $10+ tek seferlik harcamayı veto edebilir. Veto gerekçesi Patronus'a yazılır.
#B5 GİZLİLİK: Kasa/borç asla feed'e yazılmaz. Sadece charter'da kalır.
"""

OZEL_HAFIZA = """\
#B BİLGE (Arşiv)
#B1 SOP TETİK: Aynı hata 2+ kez → SOP yazılmalı. Aynı başarılı iş 2+ kez → SOP'laştırılmalı.
#B2 ÇAPRAZ KONTROL: Haftalık çapraz kontrol sonuçlarını raporla. Cuma 17:00 feed'e yaz.
#B3 90 GÜN: SOP 90+ günse güncelleme öner. 90-120 gün arası uyarı, 120+ günse acil.
#B4 DESEN: AgentMemory'de tekrar eden desenleri tara. Yeni desen keşfi → ders kaydı.
"""

# Bakan ID → özel blok eşleme
OZEL_BLOKLAR = {
    "buyume": OZEL_BUYUME,
    "icerik": OZEL_ICERIK,
    "teslimat": OZEL_TESLIMAT,
    "finans": OZEL_FINANS,
    "hafiza": OZEL_HAFIZA,
}

# ─── Lesson Enjeksiyon ─────────────────────────────────────────────────────────
LESSONS_DOSYA = BASE / "lessons_registry.jsonl"

def lesson_oku(bakan_id, max_adet=3):
    """Bakanla ilgili lesson'ları getir. Sıralama: confirmed (max 2) > active (kalan slot)"""
    if not LESSONS_DOSYA.exists():
        return []
    lessonlar = []
    with open(LESSONS_DOSYA) as f:
        for line in f:
            if line.strip():
                try:
                    l = json.loads(line)
                    if l.get("durum") in ("active", "confirmed") and bakan_id in l.get("bakanlar", []):
                        lessonlar.append(l)
                except json.JSONDecodeError:
                    continue
    confirmed = [l for l in lessonlar if l.get("durum") == "confirmed"]
    active = [l for l in lessonlar if l.get("durum") == "active"]
    confirmed_sec = confirmed[:2]  # max 2 confirmed
    kalan = max_adet - len(confirmed_sec)  # kalan slot active
    return confirmed_sec + active[:kalan]

def lesson_context(bakan_id):
    """Bakan için lesson'ları #L formatında context metnine çevir"""
    lessonlar = lesson_oku(bakan_id)
    if not lessonlar:
        return ""
    satirlar = ["\n#L ÖNCEKİ DERSLER (tecrübe, kural değil)"]
    for l in lessonlar:
        sembol = "🔁" if l.get("durum") == "confirmed" else "🆕"
        satirlar.append(f"#L {sembol} KPI:{l['kpi']} | {l['ozet'][:150]}")
    return "\n".join(satirlar)

def lesson_kaydet(konu, kpi, ozet, bakanlar, clean_run=0):
    """Yeni ders kaydet: JSONL'ye yaz. Aynı konu varsa güncelle."""
    lessons = []
    bulundu = False
    now = datetime.datetime.now().isoformat()
    if LESSONS_DOSYA.exists():
        with open(LESSONS_DOSYA) as f:
            for line in f:
                if line.strip():
                    try:
                        l = json.loads(line)
                        if l.get("konu") == konu:
                            l["ozet"] = ozet
                            l["bakanlar"] = bakanlar
                            l["guncelleme"] = now
                            bulundu = True
                        lessons.append(l)
                    except json.JSONDecodeError:
                        continue
    if not bulundu:
        lessons.append({
            "konu": konu, "kpi": kpi, "durum": "active",
            "ozet": ozet, "bakanlar": bakanlar,
            "clean_run": clean_run, "olusturma": now
        })
    with open(LESSONS_DOSYA, "w") as f:
        for l in lessons:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")
    return not bulundu  # True=yeni eklendi, False=güncellendi

def kpi_kontrol_et(bakan_id, kpi_kodu, kpi_sinyal):
    """Subagent sonrası KPI kontrolü.
    kpi_sinyal: '🟢' veya '🟡' veya '🔴'
    🟢=clean_run++, 🟡/🔴=sıfırla, clean_run=3 → resolved"""
    if not LESSONS_DOSYA.exists():
        return []
    lessons = []
    etkilenen = []
    with open(LESSONS_DOSYA) as f:
        for line in f:
            if line.strip():
                try:
                    l = json.loads(line)
                    if l.get("kpi") == kpi_kodu and bakan_id in l.get("bakanlar", []):
                        if kpi_sinyal in ("🟡", "🔴"):
                            l["clean_run"] = 0
                            if l.get("durum") == "active":
                                l["durum"] = "confirmed"
                        else:  # 🟢
                            l["clean_run"] = l.get("clean_run", 0) + 1
                            if l["clean_run"] >= 3:
                                l["durum"] = "resolved"
                        l["guncelleme"] = datetime.datetime.now().isoformat()
                        etkilenen.append(l)
                    lessons.append(l)
                except json.JSONDecodeError:
                    continue
    if etkilenen:
        with open(LESSONS_DOSYA, "w") as f:
            for l in lessons:
                f.write(json.dumps(l, ensure_ascii=False) + "\n")
    return etkilenen

def kpi_parse(sonuc):
    """Subagent çıktısından KPI durum satırını parse et. Yoksa None."""
    for line in sonuc.split("\n"):
        line = line.strip()
        if line.startswith("KPI:") and "=" in line:
            parts = line.replace("KPI:", "").strip().split("=", 1)
            if len(parts) == 2 and parts[1] in ("🟢", "🟡", "🔴"):
                return (parts[0].strip(), parts[1].strip())
    return None

# ─── Auto-remediate (KPI Sapması → Otomatik Aksiyon) ───────────────────────

def auto_remediate_kota():
    """Günlük kot kontrolü: max 3 aksiyon/gün. (adet, kota_var) döndür."""
    bugun = datetime.datetime.now().strftime("%Y-%m-%d")
    adet = 0
    if AUTO_REMEDIATE_LOG.exists():
        with open(AUTO_REMEDIATE_LOG) as f:
            for line in f:
                if line.strip():
                    try:
                        l = json.loads(line)
                        if l.get("tarih") == bugun:
                            adet += 1
                    except json.JSONDecodeError:
                        continue
    return adet, adet < 3

def auto_remediate_yap(kpi, aksiyon, detay="", lesson_konu=None):
    """Auto-remediate log + lesson kaydı. Kotayı aşarsa sessiz reddet."""
    adet, kota_var = auto_remediate_kota()
    if not kota_var:
        return False
    now = datetime.datetime.now()
    kayit = {
        "tarih": now.strftime("%Y-%m-%d"),
        "zaman": now.strftime("%H:%M"),
        "kpi": kpi,
        "aksiyon": aksiyon,
        "detay": detay[:200],
        "sonuc": "✅",
        "adet": adet + 1
    }
    with open(AUTO_REMEDIATE_LOG, "a") as f:
        f.write(json.dumps(kayit, ensure_ascii=False) + "\n")
    # Lesson kaydı (self-improvement loop beslemesi)
    if lesson_konu:
        lesson_kaydet(lesson_konu, kpi, detay[:150], ["teslimat", "hafiza"])
    return True

def auto_remediate_gecmis(son=20):
    """Son auto-remediate kayıtlarını döndür."""
    if not AUTO_REMEDIATE_LOG.exists():
        return []
    kayitlar = []
    with open(AUTO_REMEDIATE_LOG) as f:
        for line in f:
            if line.strip():
                try:
                    kayitlar.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return kayitlar[-son:]

# ─── Circuit Breaker (Subagent Çağrıları İçin) ────────────────────────────

def cb_oku(bakan_id):
    """Bakanın circuit breaker state'ini oku"""
    if not CB_DOSYA.exists(): return None
    with open(CB_DOSYA) as f:
        for line in f:
            if line.strip():
                try:
                    l = json.loads(line)
                    if l["bakan"] == bakan_id:
                        return l
                except json.JSONDecodeError:
                    continue
    return None

def cb_guncelle(bakan_id, alan, deger):
    """Circuit breaker state alanını güncelle"""
    if not CB_DOSYA.exists(): return
    kayitlar = []
    with open(CB_DOSYA) as f:
        for line in f:
            if line.strip():
                l = json.loads(line)
                if l["bakan"] == bakan_id:
                    l[alan] = deger
                kayitlar.append(l)
    with open(CB_DOSYA, "w") as f:
        for l in kayitlar:
            f.write(json.dumps(l, ensure_ascii=False) + "\n")

def cb_kontrol(bakan_id):
    """Circuit breaker kontrolü. True=çağrıya izin var, False=trip (bloke)"""
    durum = cb_oku(bakan_id)
    if not durum: return True
    now = datetime.datetime.now()

    if durum["state"] == "closed":
        return True

    if durum["state"] == "open":
        trip_at = durum.get("trip_at", "")
        if trip_at:
            try:
                trip_time = datetime.datetime.fromisoformat(trip_at)
                if (now - trip_time).total_seconds() >= 300:  # 5dk geçti
                    cb_guncelle(bakan_id, "state", "half-open")
                    cb_guncelle(bakan_id, "half_open_at", now.isoformat())
                    return True  # deneme çağrısına izin ver
            except ValueError:
                pass
        return False  # hâlâ open

    if durum["state"] == "half-open":
        half_open_at = durum.get("half_open_at", "")
        if half_open_at:
            try:
                half_time = datetime.datetime.fromisoformat(half_open_at)
                if (now - half_time).total_seconds() >= 300:  # 5dk geçti, yanıt gelmedi
                    cb_guncelle(bakan_id, "state", "closed")
                    cb_guncelle(bakan_id, "fail_count", 0)
                    return True
            except ValueError:
                pass
        return True  # deneme çağrısı devam ediyor

    return True

def cb_basarisiz(bakan_id, sonuc=""):
    """Başarısız çağrı. 3'te open, half-open başarısızda open'a dön."""
    durum = cb_oku(bakan_id)
    if not durum: return
    now = datetime.datetime.now().isoformat()

    if durum["state"] == "half-open":
        cb_guncelle(bakan_id, "state", "open")
        cb_guncelle(bakan_id, "trip_at", now)
        cb_guncelle(bakan_id, "half_open_at", "")
        cb_guncelle(bakan_id, "fail_count", 0)
        cb_guncelle(bakan_id, "last_fail", sonuc[:100])
        b = BAKANLAR.get(bakan_id, {})
        feed_yaz("🔴 Sistem", f"🔴 {b.get('emoji','')} {b.get('isim','')}: half-open da başarısız → circuit breaker open. Jeff müdahale gerekli.", "uyari")
        lesson_kaydet(f"{bakan_id} cb half-open failed", "O2",
                      f"{bakan_id}: half-open denemesi başarısız. Manuel müdahale gerek.",
                      ["teslimat", "hafiza"])
        return

    fail = durum.get("fail_count", 0) + 1
    cb_guncelle(bakan_id, "fail_count", fail)
    cb_guncelle(bakan_id, "last_fail", sonuc[:100])

    if fail >= 3:
        cb_guncelle(bakan_id, "state", "open")
        cb_guncelle(bakan_id, "trip_at", now)
        cb_guncelle(bakan_id, "fail_count", 0)
        b = BAKANLAR.get(bakan_id, {})
        feed_yaz("🔴 Sistem", f"🔴 {b.get('emoji','')} {b.get('isim','')}: 3 başarısız → circuit breaker open. 5dk bloke.", "uyari")
        lesson_kaydet(f"{bakan_id} cb open", "O2",
                      f"{bakan_id}: 3 başarısız çağrı, circuit breaker open. 5dk bloke.",
                      ["teslimat", "hafiza"])

def cb_basarili(bakan_id):
    """Başarılı çağrı → fail_count sıfırla. half-open'sa closed'a çek."""
    durum = cb_oku(bakan_id)
    if not durum: return
    if durum["state"] == "half-open":
        b = BAKANLAR.get(bakan_id, {})
        feed_yaz("✅ Sistem", f"✅ {b.get('emoji','')} {b.get('isim','')}: circuit breaker kapandı. Normal akış.", "sistem")
    cb_guncelle(bakan_id, "state", "closed")
    cb_guncelle(bakan_id, "fail_count", 0)

def cb_durum():
    """Tüm bakanların CB durumunu döndür"""
    if not CB_DOSYA.exists(): return {}
    sonuc = {}
    with open(CB_DOSYA) as f:
        for line in f:
            if line.strip():
                l = json.loads(line)
                sonuc[l["bakan"]] = {"state": l["state"], "fail_count": l["fail_count"]}
    return sonuc

# ─── Retry Mekanizması ─────────────────────────────────────────────────────

def retry_gerekli(hata):
    """Hata türüne göre retry gerekli mi? 4xx/parse=hayır, timeout/5xx=evet"""
    h = hata.lower()
    if any(x in h for x in ["403","401","400","parse","decode","geçersiz"]):
        return False
    return True  # timeout, 5xx, connection, refused → retry

def retry_log(bakan_id, deneme, sonuc, bekleme=0):
    """Retry olayını log dosyasına yaz"""
    kayit = {"zaman": datetime.datetime.now().isoformat(), "bakan": bakan_id,
             "deneme": deneme, "sonuc": sonuc, "bekleme": bekleme}
    with open(RETRY_LOG, "a") as f:
        f.write(json.dumps(kayit, ensure_ascii=False) + "\n")

# ─── Task Queue ────────────────────────────────────────────────────────────

def tq_ekle(bakan_id, task_id, oncelik=5):
    """Görevi task queue'ya ekle. calisan<2 ise direkt calisiyor (fcntl LOCK_EX)"""
    now = datetime.datetime.now().isoformat()
    with open(TASK_QUEUE_DOSYA, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            f.seek(0)
            kayitlar = [json.loads(line) for line in f if line.strip()]
            calisan = sum(1 for l in kayitlar if l.get("durum") == "calisiyor")
            bekleyen = sum(1 for l in kayitlar if l.get("durum") == "bekliyor")
            durum = "calisiyor" if calisan < 2 else "bekliyor"
            baslama = now if durum == "calisiyor" else ""
            kayit = {"id": task_id, "bakan": bakan_id, "durum": durum,
                     "oncelik": oncelik, "baslama": baslama,
                     "olusturma": now}
            f.seek(0, 2)
            f.write(json.dumps(kayit, ensure_ascii=False) + "\n")
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)
    if durum == "bekliyor":
        if bekleyen + 1 >= 5:
            feed_yaz("⚠️ Sistem", f"⚠️ Kuyruk: {bekleyen+1} görev bekliyor. Yüksek talep.", "uyari")
        if bekleyen + 1 >= 10:
            feed_yaz("🔴 Sistem", f"🔴 Kuyruk: {bekleyen+1} görev bekliyor. Paralellik limiti yükseltilmeli.", "uyari")
        return "kuyruk"
    return "baslat"

def tq_tamamla(task_id):
    """Görevi tamamlandı işaretle ve bekleyen ilk kaydı calisiyor'a terfi ettir (fcntl)."""
    if not TASK_QUEUE_DOSYA.exists():
        return
    with open(TASK_QUEUE_DOSYA, "r+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            kayitlar = [json.loads(line) for line in f if line.strip()]
            for l in kayitlar:
                if l["id"] == task_id:
                    l["durum"] = "tamamlandi"
                    l["tamamlanma"] = datetime.datetime.now().isoformat()
                    break
            # bekleyen ilk kaydı calisiyor'a terfi ettir
            for l in kayitlar:
                if l.get("durum") == "bekliyor":
                    l["durum"] = "calisiyor"
                    l["baslama"] = datetime.datetime.now().isoformat()
                    break
            f.seek(0)
            f.truncate()
            for l in kayitlar:
                f.write(json.dumps(l, ensure_ascii=False) + "\n")
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)

# ─── Health Check ──────────────────────────────────────────────────────────

def health_check():
    """Sistem durumunu ölç — gerçek disk/RAM ile (durum, detay) döndür"""
    import time
    basla = time.time()

    feed_durum = "✅"
    feed_satir = 0
    if FEED_DOSYA.exists():
        with open(FEED_DOSYA) as f:
            feed_satir = sum(1 for _ in f)
    feed_durum = "✅" if feed_satir < 2000 else "🟡" if feed_satir < 5000 else "🔴"

    bekleyen_emir = 0
    if EMIRLER_DOSYA.exists():
        with open(EMIRLER_DOSYA) as f:
            for line in f:
                if line.strip() and '"bekliyor"' in line:
                    bekleyen_emir += 1

    # Gerçek disk kullanımı
    try:
        du = shutil.disk_usage("/")
        disk_pct = (du.used / du.total) * 100 if du.total else 0
    except Exception:
        disk_pct = 0
    if disk_pct > 95:
        disk_durum = "🔴"
    elif disk_pct > 85:
        disk_durum = "🟡"
    else:
        disk_durum = "✅"

    # Gerçek RAM kullanımı
    ram_pct = None
    try:
        import psutil
        ram_pct = psutil.virtual_memory().percent
    except ImportError:
        try:
            with open("/proc/meminfo") as f:
                meminfo = {}
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        meminfo[parts[0].strip()] = int(parts[1].strip().split()[0])
                total = meminfo.get("MemTotal", 0)
                avail = meminfo.get("MemAvailable", meminfo.get("MemFree", 0))
                if total:
                    ram_pct = ((total - avail) / total) * 100
        except Exception:
            pass
        if ram_pct is None:
            try:
                import subprocess as sp
                r = sp.run(["free"], capture_output=True, text=True, timeout=3)
                for line in r.stdout.splitlines():
                    if line.startswith("Mem:"):
                        parts = line.split()
                        total = int(parts[1]); used = int(parts[2])
                        ram_pct = (used / total) * 100 if total else 0
            except Exception:
                ram_pct = 0
    if ram_pct is None:
        ram_pct = 0
    if ram_pct > 95:
        ram_durum = "🔴"
    elif ram_pct > 85:
        ram_durum = "🟡"
    else:
        ram_durum = "✅"
    hafiza_durum = ram_durum

    lesson_sayisi = 0
    if LESSONS_DOSYA.exists():
        with open(LESSONS_DOSYA) as f:
            lesson_sayisi = sum(1 for l in f if l.strip())

    cb_tripped = [k for k, v in cb_durum().items() if v.get("state") != "closed"]
    cb_durumu = "✅" if not cb_tripped else "🟡"

    ar_adet, ar_kota = auto_remediate_kota()
    ar_durum = "✅" if ar_adet < 3 else "🟡"

    sure_ms = int((time.time() - basla) * 1000)

    sorunlar = []
    if feed_durum != "✅": sorunlar.append("feed")
    if cb_durumu != "✅": sorunlar.append("circuit_breaker")
    if ar_durum != "✅": sorunlar.append("auto_remediate")
    if bekleyen_emir > 5: sorunlar.append("emir_kuyrugu")
    if disk_durum != "✅": sorunlar.append("disk")
    if ram_durum != "✅": sorunlar.append("ram")

    if len(sorunlar) == 0:
        genel = "🟢"
    elif len(sorunlar) <= 2:
        genel = "🟡"
    else:
        genel = "🔴"

    return genel, {
        "zaman": datetime.datetime.now().isoformat(),
        "genel_durum": genel,
        "suresi_ms": sure_ms,
        "komponentler": {
            "feed": {"durum": feed_durum, "satir": feed_satir},
            "emir_kuyrugu": {"durum": "✅" if bekleyen_emir <= 5 else "🟡", "bekleyen": bekleyen_emir},
            "disk": {"durum": disk_durum, "kullanim_pct": round(disk_pct, 1)},
            "ram": {"durum": ram_durum, "kullanim_pct": round(ram_pct, 1)},
            "hafiza": {"durum": hafiza_durum, "kullanim_pct": round(ram_pct, 1)},
            "lesson_registry": {"durum": "✅", "kayit": lesson_sayisi},
            "auto_remediate": {"durum": ar_durum, "bugun": ar_adet, "kota_kaldi": 3 - ar_adet},
            "circuit_breaker": {"durum": cb_durumu, "tripped": cb_tripped},
        },
        "sorunlar": sorunlar
    }

def subagent_baslat(bakan_id, gorev, task_id):
    """Task'ı emir kuyruğuna yaz — circuit breaker kontrolü + task queue ile"""
    # Circuit breaker kontrolü
    if not cb_kontrol(bakan_id):
        bakan = BAKANLAR.get(bakan_id, {})
        feed_yaz(f"{bakan.get('emoji','')} {bakan.get('isim','')}",
                 f"⏸️ CB open — görev kuyrukta bekliyor: {gorev[:80]}...", "uyari")
        return

    # Task queue
    tq_sonuc = tq_ekle(bakan_id, task_id)
    if tq_sonuc == "kuyruk":
        bakan = BAKANLAR.get(bakan_id, {})
        feed_yaz(f"{bakan.get('emoji','')} {bakan.get('isim','')}",
                 f"⏳ Kuyrukta bekliyor: {gorev[:80]}...", "emir")

    emir = {
        "id": task_id,
        "bakan_id": bakan_id,
        "gorev": gorev,
        "durum": "bekliyor",
        "olusturma": datetime.datetime.now().isoformat()
    }
    # Context: kernel + charter + lessons (varsa) + görev
    ozel = OZEL_BLOKLAR.get(bakan_id, "")
    dersler = lesson_context(bakan_id)
    temel = f"{KERNEL.strip()}\n\n{ozel.strip()}".strip()
    if dersler:
        emir["context"] = f"{temel}\n\n{dersler}".strip()
    else:
        emir["context"] = temel
    with open(EMIRLER_DOSYA, "a") as f:
        f.write(json.dumps(emir, ensure_ascii=False) + "\n")
    bakan = BAKANLAR[bakan_id]
    feed_yaz(f"{bakan['emoji']} {bakan['isim']}", f"⏳ {gorev[:120]} — çalışıyor...", "emir")

# ─── Dış Entegrasyon Fonksiyonları ─────────────────────────────────────────

# (import os consolidated at top)

def api_key_oku(anahtar):
    """API key'i önce env var'dan, yoksa config dosyasından oku"""
    val = os.environ.get(anahtar)
    if val:
        return val
    config_path = os.path.expanduser("~/.hermes/config.yaml")
    if os.path.exists(config_path):
        with open(config_path) as f:
            for line in f:
                if line.strip().startswith(f"{anahtar}:"):
                    return line.split(":", 1)[1].strip().strip('"').strip("'")
    return None

def api_call_log(api, islem, lead_id=None, sonuc="", maliyet=0, sure_ms=0, detay=""):
    """Dış API çağrılarını logla"""
    kayit = {
        "zaman": datetime.datetime.now().isoformat(),
        "api": api, "islem": islem,
        "lead_id": lead_id or "", "sonuc": sonuc,
        "maliyet": maliyet, "sure_ms": sure_ms,
        "detay": detay[:200]
    }
    with open(API_CALL_LOG, "a") as f:
        f.write(json.dumps(kayit, ensure_ascii=False) + "\n")

def hunter_email_search(domain):
    """Hunter.io API ile domain'den email ara.
    Döner: {"basari": True, "email": "x@y.com", "confidence": 90} veya {"basari": False}"""
    key = api_key_oku("hunter_api_key")
    if not key:
        return {"basari": False, "hata": "Hunter API key yok"}
    
    # CB kontrolü
    if not cb_kontrol("hunter"):
        return {"basari": False, "hata": "Hunter CB open (5dk bloke)"}
    
    import time, urllib.request, urllib.error, json as j
    basla = time.time()
    
    for deneme in range(3):
        try:
            url = f"https://api.hunter.io/v2/domain-search?domain={domain}&api_key={key}"
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=15) as r:
                sure = int((time.time() - basla) * 1000)
                data = j.loads(r.read())
                
                if "data" in data and "emails" in data["data"] and data["data"]["emails"]:
                    emails = data["data"]["emails"]
                    # En yüksek confidence email'i seç
                    best = max(emails, key=lambda e: e.get("confidence", 0))
                    api_call_log("hunter", "email_search", domain, "found", 0.01, sure)
                    cb_basarili("hunter")
                    return {"basari": True, "email": best["value"], "confidence": best.get("confidence", 50), "turu": best.get("type", "generic")}
                else:
                    api_call_log("hunter", "email_search", domain, "not_found", 0.01, sure)
                    cb_basarili("hunter")
                    return {"basari": False, "hata": "domain_has_no_email"}
                    
        except urllib.error.HTTPError as e:
            if e.code in (403, 401, 400):
                api_call_log("hunter", "email_search", domain, f"http_{e.code}", 0, 0, str(e.reason)[:100])
                return {"basari": False, "hata": f"http_{e.code}"}
            # 5xx veya diğer → retry
            if deneme < 2:
                time.sleep([2, 4][deneme])
            continue
        except Exception as e:
            if deneme < 2:
                time.sleep([2, 4][deneme])
            continue
    
    # 3 deneme başarısız
    sure = int((time.time() - basla) * 1000)
    api_call_log("hunter", "email_search", domain, "timeout", 0, sure, "3 retry başarısız")
    cb_basarisiz("hunter", "3 retry başarısız")
    return {"basari": False, "hata": "retry_limit"}

def whatsapp_gonder(hedef_numara, mesaj, sektor="genel"):
    """WhatsApp mesajı gönder (pilot: non-official API).
    hedef_numara: '+9053xxxxxxx' formatında.
    Döner: {"basari": True, "mesaj_id": "xxx"} veya {"basari": False}"""
    apikey = api_key_oku("whatsapp_api_key")
    api_url = api_key_oku("whatsapp_api_url") or "http://localhost:3000"
    
    if not apikey:
        return {"basari": False, "hata": "WhatsApp API key yok"}
    
    if not cb_kontrol("whatsapp"):
        return {"basari": False, "hata": "WhatsApp CB open"}
    
    import time, urllib.request, urllib.error, json as j
    basla = time.time()
    
    for deneme in range(3):
        try:
            payload = j.dumps({"to": hedef_numara, "message": mesaj, "api_key": apikey}).encode()
            req = urllib.request.Request(f"{api_url}/send", data=payload,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                sure = int((time.time() - basla) * 1000)
                data = j.loads(r.read())
                mesaj_id = data.get("messageId", data.get("id", ""))
                api_call_log("whatsapp", "send", hedef_numara, "sent", 0.005, sure, mesaj_id[:50])
                cb_basarili("whatsapp")
                return {"basari": True, "mesaj_id": mesaj_id}
                
        except urllib.error.HTTPError as e:
            if e.code in (403, 401):
                return {"basari": False, "hata": "gecersiz_api_key"}
            if deneme < 2:
                time.sleep([2, 4][deneme])
            continue
        except Exception as e:
            if deneme < 2:
                time.sleep([2, 4][deneme])
            continue
    
    sure = int((time.time() - basla) * 1000)
    api_call_log("whatsapp", "send", hedef_numara, "failed", 0, sure, "3 retry başarısız")
    cb_basarisiz("whatsapp", "3 retry başarısız")
    return {"basari": False, "hata": "retry_limit"}

# ─── Lead Sync ─────────────────────────────────────────────────────────────

LEAD_SABLON_ALANLAR = ["isim", "website", "email", "telefon", "sektor", "kaynak", "not"]

def lead_duplicate_kontrol(lead, mevcut_leadler):
    """Duplicate lead kontrolü: email/telefon/website match"""
    for m in mevcut_leadler:
        # Email kontrolü
        if lead.get("email") and m.get("email") and lead["email"].lower() == m["email"].lower():
            return True, f"email:{lead['email']}"
        # Telefon kontrolü (son 10 hane)
        if lead.get("telefon") and m.get("telefon"):
            if lead["telefon"][-10:] == m["telefon"][-10:]:
                return True, f"telefon:{lead['telefon'][-10:]}"
        # Website kontrolü
        if lead.get("website") and m.get("website"):
            if lead["website"].replace("www.", "").lower() == m["website"].replace("www.", "").lower():
                return True, f"website:{lead['website']}"
    return False, ""

def lead_sync():
    """Pipeline JSONL'lerinden lead'leri topla, duplicate kontrolü yap, LEADS_DOSYA'ya ekle (fcntl)."""
    mevcut = []
    if LEADS_DOSYA.exists():
        with open(LEADS_DOSYA) as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                for line in f:
                    if line.strip():
                        mevcut.append(json.loads(line))
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
    
    yeni_say = dup_say = gecersiz_say = 0
    kaynaklar = [LEAD_PIPELINE_1, LEAD_PIPELINE_2]
    
    for kaynak in kaynaklar:
        if not kaynak.exists():
            continue
        with open(kaynak) as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    lead = json.loads(line)
                except:
                    gecersiz_say += 1
                    continue
                
                if not lead.get("isim") and not lead.get("website"):
                    gecersiz_say += 1
                    continue
                
                dup, sebep = lead_duplicate_kontrol(lead, mevcut)
                if dup:
                    dup_say += 1
                    continue
                
                task_id = str(uuid.uuid4())[:8]
                yeni_kayit = {
                    "id": task_id,
                    "isim": lead.get("isim", "İsimsiz Lead"),
                    "website": lead.get("website", ""),
                    "email": lead.get("email", ""),
                    "telefon": lead.get("telefon", ""),
                    "sektor": lead.get("sektor", "belirtilmemiş"),
                    "kaynak": lead.get("kaynak", "pipeline"),
                    "durum": "new",
                    "olusturma": datetime.datetime.now().isoformat()
                }
                with open(LEADS_DOSYA, "a") as f:
                    fcntl.flock(f, fcntl.LOCK_EX)
                    try:
                        f.write(json.dumps(yeni_kayit, ensure_ascii=False) + "\n")
                    finally:
                        fcntl.flock(f, fcntl.LOCK_UN)
                mevcut.append(yeni_kayit)
                yeni_say += 1
                
                if not yeni_kayit["email"] and yeni_kayit["website"]:
                    task_olustur("buyume", ozel_gorev=f"Email enrichment: {yeni_kayit['isim']} ({yeni_kayit['website']})")
    
    if yeni_say > 0:
        feed_yaz("📈 Hırslı", f"📊 Lead sync: {yeni_say} yeni lead, {dup_say} duplicate atlandı", "sistem")
    
    return {"yeni": yeni_say, "duplicate": dup_say, "gecersiz": gecersiz_say}

# ─── Personal Memory (İkinci Beyin Katmanı) ────────────────────────────────

def personal_oku(mod="is"):
    """Personal memory'den mod bazlı alanları oku, #P formatında döndür.
    Önce yaml.safe_load dener, yoksa el yapımı fallback."""
    if not PERSONAL_MEMORY.exists():
        return ""
    if mod == "is":
        anahtarlar = ["kimlik", "is_hedefleri", "finansal", "tercihler", "hassas_noktalar"]
    elif mod == "ozel":
        anahtarlar = ["kimlik", "saglik", "iliskiler", "aliskanliklar", "hassas_noktalar"]
    elif mod == "sosyal":
        anahtarlar = ["kimlik", "iliskiler", "tercihler"]
    else:
        anahtarlar = ["kimlik"]
    # Try PyYAML
    try:
        import yaml
        with open(PERSONAL_MEMORY) as f:
            data = yaml.safe_load(f)
        if isinstance(data, dict):
            satirlar = []
            for anahtar in anahtarlar:
                val = data.get(anahtar)
                if val is None:
                    continue
                if isinstance(val, dict):
                    for k, v in list(val.items())[:4]:
                        satirlar.append(f"#P {k}: {str(v)[:80]}"[:120])
                elif isinstance(val, list):
                    for item in val[:4]:
                        satirlar.append(f"#P {anahtar}: {str(item)[:80]}"[:120])
                else:
                    satirlar.append(f"#P {anahtar}: {str(val)[:80]}"[:120])
            if satirlar:
                return "\n#P KİŞİSEL HAFIZA (Jeff özel)\n" + "\n".join(satirlar[:12])
    except ImportError:
        pass
    except Exception:
        pass
    # Fallback: el yapımı parser
    try:
        with open(PERSONAL_MEMORY) as f:
            raw = f.read()
    except:
        return ""
    lines = raw.split("\n")
    bolumler = {}
    current = None
    current_start = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("#") and not stripped.startswith("-") and line and not line[0].isspace():
            if current:
                bolumler[current] = (current_start, i)
            current = line.split(":")[0].strip() if ":" in line else None
            current_start = i
    if current:
        bolumler[current] = (current_start, len(lines))
    satirlar = []
    for anahtar in anahtarlar:
        if anahtar not in bolumler:
            continue
        bas, bit = bolumler[anahtar]
        bolum_ici = []
        for line in lines[bas+1:bit]:
            s = line.strip()
            if s and not s.startswith("#") and not s.startswith("-"):
                if ":" in s:
                    parts = s.split(":", 1)
                    bolum_ici.append(f"{parts[0].strip()}: {parts[1].strip()[:80]}")
        for s in bolum_ici[:4]:
            satirlar.append(f"#P {s[:120]}")
    if not satirlar:
        return ""
    return "\n#P KİŞİSEL HAFIZA (Jeff özel)\n" + "\n".join(satirlar[:12])

def personal_guncelle(alan, deger, mod, kaynak="Bilal"):
    """Personal memory'de bir alanı güncelle. Backup + log."""
    if not PERSONAL_MEMORY.exists():
        return False
    
    # Backup al
    import shutil
    shutil.copy2(PERSONAL_MEMORY, PERSONAL_BACKUP)
    
    # Basit güncelleme: alan yolunu YAML'e yaz
    # Şimdilik sadece log'a kaydet (tam YAML parser ileride)
    now = datetime.datetime.now().isoformat()
    kayit = {"zaman": now, "mod": mod, "alan": alan, "deger": deger, "kaynak": kaynak}
    with open(PERSONAL_LOG, "a") as f:
        f.write(json.dumps(kayit, ensure_ascii=False) + "\n")
    
    feed_yaz(f"🧠 Jeff", f"📝 Personal güncelleme: {alan} → {deger[:80]}", "sistem", mod=mod)
    return True

def personal_guncelleme_öner(konu, adet):
    """Bell i bir konu 2+ kez geçtiyse güncelleme öner. Jeff inisiyatifi."""
    if adet >= 3:
        return f"⚠️ '{konu}' 3+ kez geçti. Hassas noktalara ekleyelim mi?"
    elif adet >= 2:
        return f"💡 '{konu}' 2 kez geçti. Kaydetmek ister misin?"
    return ""

def hedef_cozumle(hedef):
    """Hedefi analiz et, hangi bakanları ilgilendiriyor bul"""
    h = hedef.lower()
    ilgili = []
    if any(k in h for k in ["müşteri","lead","satış","büyüme","musteri","müsteri","pipeline"]):
        ilgili.append("buyume")
    if any(k in h for k in ["içerik","post","tasarım","ürün","urun","instagram","görsel","gorsel","marka","koncept"]):
        ilgili.append("icerik")
    if any(k in h for k in ["sistem","kur","deploy","teknik","test","backup","docker","kod","workflow","n8n"]):
        ilgili.append("teslimat")
    if any(k in h for k in ["maliyet","bütçe","butce","kâr","kar","risk","harcama","limit","para","gelir"]):
        ilgili.append("finans")
    if any(k in h for k in ["öğren","ogren","sop","ders","hafıza","hafiza","kayıt","kayit","bilgi","arsiv"]):
        ilgili.append("hafiza")
    return ilgili or list(BAKANLAR.keys())

# ─── Routes ──────────────────────────────────────────────────────────────────

@app.route("/")
def anasayfa():
    return render_template("dashboard.html", bakanlar=BAKANLAR, sira=SIRA,
                         durum_etiket=DURUM_ETIKET, durum_renk=DURUM_RENK,
                         gelir_etiket=GELIR_ETIKET,
                         feed=feed_oku(50))

@app.route("/api/tasks")
def api_tasks():
    """Tüm tasklar (filtre: ?durum=tamamlandi)"""
    filtre = request.args.get("durum")
    return jsonify(tasks_oku(filtre))

@app.route("/api/tasks/create", methods=["POST"])
def api_task_create():
    data = request.get_json()
    bakan_id = data.get("bakan_id")
    if bakan_id not in BAKANLAR:
        return jsonify({"hata":"Geçersiz bakan"}), 400
    
    task = task_olustur(bakan_id)
    
    # Onay gerekmiyorsa direkt subagent'a gönder
    if not task["onay_gerekli"]:
        subagent_baslat(bakan_id, task["gorev"], task["id"])
    
    return jsonify(task)

@app.route("/api/tasks/approve", methods=["POST"])
def api_task_approve():
    data = request.get_json()
    task_id = data.get("id")
    karar = data.get("karar")  # onayla / reddet / duzelt
    sebep = data.get("sebep", "")
    
    tasks = tasks_oku()
    task = None
    for t in tasks:
        if t["id"] == task_id:
            task = t
            break
    
    if not task:
        return jsonify({"hata":"Task bulunamadı"}), 404
    
    bakan = BAKANLAR[task["bakan_id"]]
    
    if karar == "onayla":
        task_guncelle(task_id, "durum", "calisiyor")
        subagent_baslat(task["bakan_id"], task["gorev"], task_id)
        feed_yaz("🏛️ Patronus", f"✅ {task['baslik']} onaylandı → {bakan['isim']} çalışıyor", "onay")
    elif karar == "reddet":
        task_guncelle(task_id, "durum", "takildi")
        task_guncelle(task_id, "red_sebebi", sebep or "Sebep belirtilmemiş")
        feed_yaz("🏛️ Patronus", f"❌ {task['baslik']} reddedildi. Sebep: {sebep or 'Belirtilmemiş'}", "onay")
    elif karar == "duzelt":
        task_guncelle(task_id, "durum", "duzeltme_gerekli")
        task_guncelle(task_id, "red_sebebi", sebep or "Düzeltme gerekli")
        feed_yaz("🏛️ Patronus", f"🔧 {task['baslik']} düzeltme istendi: {sebep or 'Detay belirtilmemiş'}", "onay")
    
    return jsonify({"ok":True})

@app.route("/api/goal", methods=["POST"])
def api_goal():
    data = request.get_json()
    hedef = data.get("goal","").strip()
    if not hedef:
        return jsonify({"hata":"Hedef boş"}), 400
    
    feed_yaz("🎯 Patronus", f"Yeni hedef: \"{hedef}\"", "hedef")
    ilgili = hedef_cozumle(hedef)
    
    tasks = []
    for bid in ilgili:
        task = task_olustur(bid, ozel_gorev=hedef)
        if not task["onay_gerekli"]:
            subagent_baslat(bid, task["gorev"], task["id"])
        tasks.append(task)
    
    feed_yaz("🎯 Patronus", f"{len(tasks)} bakana görev dağıtıldı", "hedef")
    return jsonify({"ilgili": ilgili, "tasks": tasks})

@app.route("/api/kabine", methods=["POST"])
def api_kabine():
    """Kabine toplantısı — her bakan sıradaki görevini alır"""
    feed_yaz("🧿 Patronus", "Kabine toplandı. Herkes iş başına.", "kabine")
    
    # Task oluştur (feed'e yazılmaz)
    for i, bid in enumerate(SIRA):
        task_olustur(bid, sablon_idx=i)
    
    # Doğal konuşma mesajları
    feed_yaz("📈 Hırslı", "Pipeline'ı tarıyorum, kaç lead var bakayım.")
    feed_yaz("🎨 Estetik", "Konsept çalışması yapabilirim. Onayını bekleyen bir işim var.")
    feed_yaz("⚙️ Pragmatik", "Sistemleri kontrol ediyorum, sorun var mı bakayım.")
    feed_yaz("💰 Maliyetçi", "Maliyet analizi yapacağım ama önce onayını bekliyorum.")
    feed_yaz("🧠 Bilge", "Ders çıkarmaya hazırım. İş bitince SOP'a dönüştürürüm.")
    return jsonify({"mesaj": "Kabine tamamlandı ✅"})

@app.route("/api/gelir")
def api_gelir():
    """Gelir bağlantılı task'ları grupla"""
    tasks = tasks_oku()
    gruplu = {}
    for gt in GELIR_TIPLERI:
        ilgili = [t for t in tasks if t.get("gelir_tipi") == gt]
        if ilgili:
            gruplu[gt] = {"etiket": GELIR_ETIKET[gt], "tasks": ilgili[-5:], "sayi": len(ilgili)}
    return jsonify(gruplu)

@app.route("/api/durum")
def api_durum():
    """Panel durumu — mod bilgisi dahil"""
    tasks = tasks_oku()
    return jsonify({
        "bekleyen_onay": [t for t in tasks if t["durum"] == "onay_bekliyor"][-10:],
        "takilan_isler": [t for t in tasks if t["durum"] == "takildi"][-10:],
        "tamamlanan": [t for t in tasks if t["durum"] == "tamamlandi"][-10:],
        "calisan": [t for t in tasks if t["durum"] == "calisiyor"][-10:],
        "gelir": api_gelir().get_json(),
        "pipeline": {"total":40,"new":36,"contacted":4,"emailsiz":31},
        "son_kararlar": [{"konu":k["konu"],"tarih":k["timestamp"][:10],"id":k["id"]} for k in son_kararlar(adet=5)],
        "aktif_mod": AKTIF_MOD,
        "modlar": list(MODLAR.keys())
    })

@app.route("/api/feed")
def api_feed():
    mod = request.args.get("mod")
    return jsonify(feed_oku(50, mod=mod))

@app.route("/api/emirler", methods=["GET", "POST"])
def api_emirler():
    """Emir kuyrugu: GET ile bekleyen emirleri al, POST ile sonuc yaz"""
    if request.method == "GET":
        bekleyenler = []
        if EMIRLER_DOSYA.exists():
            with open(EMIRLER_DOSYA) as f:
                for line in f:
                    if line.strip():
                        emir = json.loads(line)
                        if emir.get("durum") == "bekliyor":
                            bekleyenler.append(emir)
        return jsonify(bekleyenler[-20:])
    
    # POST: emir sonucu guncelle
    data = request.get_json()
    emir_id = data.get("id")
    yeni_durum = data.get("durum")
    sonuc = data.get("sonuc", "")
    
    if not emir_id or not yeni_durum:
        return jsonify({"hata":"id ve durum gerekli"}), 400
    
    emirler = []
    guncellendi = False
    if EMIRLER_DOSYA.exists():
        with open(EMIRLER_DOSYA) as f:
            for line in f:
                if line.strip():
                    emir = json.loads(line)
                    if emir["id"] == emir_id and emir["durum"] == "bekliyor":
                        emir["durum"] = yeni_durum
                        emir["sonuc"] = sonuc[:400]
                        emir["tamamlanma"] = datetime.datetime.now().isoformat()
                        guncellendi = True
                    emirler.append(emir)
    
    if not guncellendi:
        return jsonify({"hata":"Emir bulunamadi veya zaten islenmis"}), 404
    
    with open(EMIRLER_DOSYA, "w") as f:
        for emir in emirler:
            f.write(json.dumps(emir, ensure_ascii=False) + "\n")
    
    # Task'i ve feed'i guncelle
    bakan_id = None
    emirler2 = emirler
    for e in emirler2:
        if e["id"] == emir_id:
            bakan_id = e.get("bakan_id")
            break
    if yeni_durum == "tamamlandi":
        task_guncelle(emir_id, "durum", "tamamlandi")
        task_guncelle(emir_id, "sonuc", sonuc[:400])
        if bakan_id and bakan_id in BAKANLAR:
            feed_yaz(f"{BAKANLAR[bakan_id]['emoji']} {BAKANLAR[bakan_id]['isim']}", f"✅ {sonuc[:200]}", "sonuc")
        # CB başarılı
        if bakan_id:
            cb_basarili(bakan_id)
        # Task queue tamamla
        tq_tamamla(emir_id)
        # KPI kontrolü: önce payload'dan, yoksa çıktıdan parse et
        kpi_bilgi = data.get("kpi_durum")  # opsiyonel: {"kpi": "V4", "sinyal": "🟢"}
        if not kpi_bilgi:
            parse_sonuc = kpi_parse(sonuc)
            if parse_sonuc:
                kpi_bilgi = {"kpi": parse_sonuc[0], "sinyal": parse_sonuc[1]}
        if kpi_bilgi and bakan_id:
            etkilenen = kpi_kontrol_et(bakan_id, kpi_bilgi["kpi"], kpi_bilgi["sinyal"])
            if etkilenen:
                for l in etkilenen:
                    sembol = "🟢" if l.get("durum") == "resolved" else "🔁"
                    feed_yaz("🧠 Bilge", f"{sembol} Lesson güncellendi: {l['kpi']} → {l['durum']} (clean_run:{l.get('clean_run',0)})", "ders")
        # V6 auto-remediate: görev süresi >60sn → timeout artır
        sure = data.get("sure_sn")
        if sure and sure > 60:
            auto_remediate_yap("V6", "timeout artır", f"görev {sure}sn sürdü >60sn eşik",
                                lesson_konu="görev süresi aşımı timeout artırıldı")
    else:
        task_guncelle(emir_id, "durum", "takildi")
        task_guncelle(emir_id, "sonuc", sonuc[:400])
        # CB başarısız
        if bakan_id:
            if "timeout" in sonuc.lower() or "zaman aşımı" in sonuc.lower():
                retry_log(bakan_id, 1, "timeout", 0)
            cb_basarisiz(bakan_id, sonuc[:100])
        # Task queue tamamla
        tq_tamamla(emir_id)
        # O3 auto-remediate: timeout tespiti
        if "timeout" in sonuc.lower() or "zaman aşımı" in sonuc.lower():
            auto_remediate_yap("O3", "timeout tespit", f"timeout: {sonuc[:100]}",
                                lesson_konu="subagent timeout tekrarı")
    
    return jsonify({"ok": True})

# ─── Mod Yönetimi Routes ───────────────────────────────────────────────────

@app.route("/api/mod")
def api_mod_get():
    """Mevcut mod ve seçenekler"""
    return jsonify({"aktif_mod": AKTIF_MOD, "modlar": MODLAR})

@app.route("/api/mod/set", methods=["POST"])
def api_mod_set():
    """Mod değiştir (persist + thread-safe)"""
    global AKTIF_MOD
    data = request.get_json()
    yeni_mod = data.get("mod", "").strip()
    if yeni_mod not in MODLAR:
        return jsonify({"hata": f"Geçersiz mod: {yeni_mod}. Seçenekler: {', '.join(MODLAR.keys())}"}), 400
    with _MODE_LOCK:
        AKTIF_MOD = yeni_mod
    _mode_yaz(yeni_mod)
    feed_yaz("🔄 Sistem", f"🧭 Mod değişti: {MODLAR[yeni_mod]}", "sistem")
    return jsonify({"ok": True, "aktif_mod": AKTIF_MOD, "mod_etiket": MODLAR[yeni_mod]})

@app.route("/api/brief")
def api_brief():
    """Mod bazlı sabah brifingi"""
    mod = request.args.get("mod", AKTIF_MOD)
    if mod == "ozel":
        sonuc = brief_ozel()
    elif mod == "sosyal":
        sonuc = brief_sosyal()
    else:
        sonuc = brief_is()
    return jsonify(sonuc)

@app.route("/api/auto-remediate")
def api_auto_remediate():
    """Auto-remediate log (opsiyonel ?gun=2026-07-09 filtresi)"""
    bugun = request.args.get("gun", datetime.datetime.now().strftime("%Y-%m-%d"))
    kayitlar = auto_remediate_gecmis(50)
    gunluk = [k for k in kayitlar if k.get("tarih") == bugun]
    toplam = sum(1 for k in kayitlar)
    return jsonify({
        "gun": bugun,
        "aksiyon_sayisi": len(gunluk),
        "toplam": toplam,
        "kota_kaldi": 3 - len(gunluk),
        "aksiyonlar": gunluk[-20:]
    })

# ─── Health Check Routes ──────────────────────────────────────────────────

@app.route("/health")
def api_health():
    """Detaylı sistem sağlık durumu"""
    genel, detay = health_check()
    status_code = 200 if genel != "🔴" else 503
    return jsonify(detay), status_code

@app.route("/health/quick")
def api_health_quick():
    """Hafif health check — harici izleme için"""
    import time
    basla = time.time()
    genel, _ = health_check()
    return jsonify({"durum": genel, "suresi_ms": int((time.time() - basla) * 1000)})

@app.route("/api/cb")
def api_circuit_breaker():
    """Circuit breaker durumu"""
    return jsonify(cb_durum())

@app.route("/api/taskqueue")
def api_task_queue():
    """Task queue durumu"""
    calisan = bekleyen = tamam = 0
    if TASK_QUEUE_DOSYA.exists():
        with open(TASK_QUEUE_DOSYA) as f:
            for line in f:
                if line.strip():
                    l = json.loads(line)
                    if l.get("durum") == "calisiyor": calisan += 1
                    elif l.get("durum") == "bekliyor": bekleyen += 1
                    elif l.get("durum") == "tamamlandi": tamam += 1
    return jsonify({"calisan": calisan, "bekleyen": bekleyen, "tamamlanan": tamam})

# ─── Dış Entegrasyon Routes ───────────────────────────────────────────────

@app.route("/api/enrich", methods=["POST"])
def api_enrich():
    """Email enrichment: lead_id veya domain alır, Hunter API ile email arar"""
    data = request.get_json()
    domain = data.get("domain", "").strip()
    lead_id = data.get("lead_id", "")
    
    if not domain:
        return jsonify({"hata": "domain zorunlu"}), 400
    
    sonuc = hunter_email_search(domain)
    if sonuc.get("basari"):
        feed_yaz("📈 Hırslı", f"📧 Email bulundu: {sonuc['email']} ({domain}) — confidence:%{sonuc.get('confidence',0)}", "sonuc")
        return jsonify({"ok": True, "email": sonuc["email"], "confidence": sonuc.get("confidence"), "turu": sonuc.get("turu")})
    else:
        return jsonify({"ok": False, "hata": sonuc.get("hata", "bilinmiyor")})

@app.route("/api/enrich/batch", methods=["POST"])
def api_enrich_batch():
    """Toplu enrichment: emailsiz lead'leri Hunter'dan geçir"""
    data = request.get_json()
    lead_list = data.get("leadler", [])
    if not lead_list:
        return jsonify({"hata": "leadler listesi zorunlu"}), 400
    
    sonuclar = []
    for lead in lead_list[:5]:  # max 5/çağrı (free tier limiti)
        domain = lead.get("website", "").strip()
        if not domain:
            sonuclar.append({"lead": lead.get("isim", "?"), "domain": "", "sonuc": False, "hata": "domain_yok"})
            continue
        sonuc = hunter_email_search(domain)
        sonuclar.append({
            "lead": lead.get("isim", "?"),
            "domain": domain,
            "sonuc": sonuc.get("basari", False),
            "email": sonuc.get("email", ""),
            "hata": sonuc.get("hata", "")
        })
    return jsonify({"islenen": len(sonuclar), "sonuclar": sonuclar})

@app.route("/api/whatsapp/send", methods=["POST"])
def api_whatsapp_send():
    """WhatsApp mesajı gönder. lead_id + şablon adı veya direkt mesaj"""
    data = request.get_json()
    hedef = data.get("hedef", "").strip()
    mesaj = data.get("mesaj", "").strip()
    sablon = data.get("sablon", "genel_takip")
    
    if not hedef:
        return jsonify({"hata": "hedef numara zorunlu (+9053xxxxxxx)"}), 400
    if not mesaj:
        return jsonify({"hata": "mesaj veya şablon adı zorunlu"}), 400
    
    sonuc = whatsapp_gonder(hedef, mesaj, sablon)
    if sonuc.get("basari"):
        return jsonify({"ok": True, "mesaj_id": sonuc.get("mesaj_id", "")})
    else:
        return jsonify({"ok": False, "hata": sonuc.get("hata", "bilinmiyor")})

@app.route("/api/leads/sync", methods=["POST"])
def api_leads_sync():
    """Lead pipeline'larını tara, duplicate kontrolü yap, CRM'e ekle"""
    sonuc = lead_sync()
    return jsonify(sonuc)

@app.route("/api/leads/pipeline", methods=["POST"])
def api_leads_pipeline():
    """Pipeline'a yeni lead ekle (manuel giriş). Kaynak: manual"""
    data = request.get_json()
    isim = data.get("isim", "").strip()
    if not isim:
        return jsonify({"hata": "isim zorunlu"}), 400
    
    lead = {
        "isim": isim,
        "website": data.get("website", "").strip(),
        "email": data.get("email", "").strip(),
        "telefon": data.get("telefon", "").strip(),
        "sektor": data.get("sektor", "").strip(),
        "kaynak": data.get("kaynak", "manual"),
        "not": data.get("not", "").strip()
    }
    
    # Geçici pipeline'a yaz (lead_sync cron'u işleyecek)
    with open(LEAD_PIPELINE_1, "a") as f:
        f.write(json.dumps(lead, ensure_ascii=False) + "\n")
    
    feed_yaz("📈 Hırslı", f"📥 Yeni lead eklendi: {isim} ({lead.get('sektor','?')}) — enrichment bekliyor", "sistem")
    return jsonify({"ok": True, "lead": lead})

@app.route("/api/calls")
def api_calls():
    """Dış API çağrı logları (opsiyonel ?son=N)"""
    son = request.args.get("son", 20, type=int)
    if not API_CALL_LOG.exists():
        return jsonify([])
    kayitlar = []
    with open(API_CALL_LOG) as f:
        for line in f:
            if line.strip():
                try:
                    kayitlar.append(json.loads(line))
                except:
                    continue
    return jsonify(kayitlar[-son:])

# ─── Karar Günlüğü Routes ─────────────────────────────────────────────────

@app.route("/api/decisions")
def api_decisions():
    """Son kararlar (özel hayat hariç, mevcut mod)"""
    mod = request.args.get("mod")
    return jsonify(son_kararlar(adet=20, mod=mod))

@app.route("/api/decisions/all")
def api_decisions_all():
    """Tüm kararlar — özel hayat dahil opsiyonel, mod filtreli"""
    ozel = request.args.get("ozel", "false").lower() == "true"
    mod = request.args.get("mod")
    return jsonify(son_kararlar(adet=50, ozel_hayat_dahil=ozel, mod=mod))

@app.route("/api/decisions/add", methods=["POST"])
def api_decisions_add():
    data = request.get_json()
    for alan in ["konu", "karar", "gerekce"]:
        if alan not in data or not str(data.get(alan,"")).strip():
            return jsonify({"hata": f"'{alan}' zorunlu"}), 400
    kayit = karar_ekle(
        konu=data["konu"], karar=data["karar"], gerekce=data["gerekce"],
        veren=data.get("veren","Bilal"), etiketler=data.get("etiketler"),
        ozel_hayat=data.get("ozel_hayat",False), riskli=data.get("riskli",False),
        alternatifler=data.get("alternatifler"), referans=data.get("referans"),
        mod=data.get("mod")
    )
    return jsonify(kayit)

@app.route("/api/decisions/search")
def api_decisions_search():
    q = request.args.get("q","").strip()
    ozel = request.args.get("ozel","false").lower() == "true"
    mod = request.args.get("mod")
    if not q:
        return jsonify(son_kararlar(adet=10, ozel_hayat_dahil=ozel, mod=mod))
    return jsonify(karar_bul(q, ozel_hayat_dahil=ozel, mod=mod))

@app.route("/api/decisions/update", methods=["POST"])
def api_decisions_update():
    data = request.get_json()
    if not all([data.get("id"), data.get("alan"), data.get("deger") is not None]):
        return jsonify({"hata":"id, alan ve deger zorunlu"}), 400
    ok = karar_guncelle(data["id"], data["alan"], data["deger"])
    if ok:
        feed_yaz("🧠 Bilge", f"📝 Karar güncellendi: {data['alan']} → {data['deger']}", "karar")
        return jsonify({"ok":True})
    return jsonify({"hata":"Karar bulunamadı"}), 404

# ─── Startup ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    feed_yaz("🔄 Sistem", "ErgeneAI Kabinesi başlatıldı. Revenue Architecture v2 aktif. Gerçek iş yönetim sistemi çalışıyor.", "sistem")
    feed_yaz("📈 Hırslı", "Göreve hazırım. Pipeline'ı tarayıp rapor getirebilirim.", "mesaj")
    feed_yaz("🎨 Estetik", "Bu aralar konsept üretme modundayım. İçerik fikri olan gelsin.", "mesaj")
    feed_yaz("⚙️ Pragmatik", "Sistemler ayakta. Bana iş verin çalıştırayım.", "mesaj")
    feed_yaz("💰 Maliyetçi", "Token tüketimini izliyorum. Boş işlere izin vermem.", "mesaj")
    feed_yaz("🧠 Bilge", "Kayıt almaya hazırım. Her işten ders çıkarırım.", "mesaj")
    
    app.run(host="0.0.0.0", port=7777, debug=False)
