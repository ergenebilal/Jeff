"""Jeff's daily work on top of the store: digest, morning message, context for the chat, lead notes and drafts."""
import datetime
import json
import re
import time

from . import llm, scoring
from .store import STAGES, now

NO_CLAIMS = ("Rakam, yüzde, istatistik, müşteri referansı, fiyat ya da garanti yazma. Em-dash ve emoji kullanma. "
             "Yalnızca verilen bilgiye dayan, bilmediğini uydurma.")


def _clip(s, n):
    return re.sub(r"\s+", " ", (s or "").replace("—", ",").replace("–", "-")).strip()[:n]


def you_text(lead, approved=False):
    """What is waiting on Bilal for this lead, derived from real state only. approved: its draft is approved but not yet sent."""
    stage = lead["stage"]
    if stage == "Onay bekliyor" and approved:
        return "Gönderip 'Gönderdim' deyin"
    if stage == "Yanıt geldi":
        return "Yanıtı okuyun"
    if stage == "Görüşme":
        return "Görüşmenin sonucunu işaretleyin"
    from .metrics import no_signal
    if no_signal(lead):
        return "Sinyal yok: kapatmayı düşünün"
    if stage == "Gönderildi" and lead.get("follow_at") and lead["follow_at"] <= now():
        return "Takip zamanı geldi"
    if stage == "Onay bekliyor":
        return "Taslağı onaylayın"
    if stage == "Taslak hazır":
        return "Taslağa bakın"
    return ""


SECTIONS = (("yeni", "Yeni bulunanlar"), ("bekleyen", "İşlem bekleyenler"), ("islemde", "İşlem yapılanlar"), ("kapandi", "Kapananlar"),
            ("elendi", "Kapıda elenenler"))


def section_of(lead):
    """Which lead list a lead belongs to. 'Yeni' and never opened = just found; opened but untouched = waiting; anything done = in progress."""
    if lead["stage"] in ("Kapandı", "Kazanıldı"):
        return "kapandi"
    if lead.get("gate") == "elendi" and not lead.get("gate_override") and lead["stage"] in ("Yeni", "İncelendi"):
        return "elendi"
    if lead["stage"] == "Yeni":
        return "bekleyen" if lead.get("reviewed_at") else "yeni"
    return "islemde"


# A rejected idea stays empty; the digest remains a separate useful summary.
_TR_FOLD = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
_TR_WORDS = "açık çözüm çözümler hızla erişim değişim dünyanın dünyasında zekâ yapay zekası gösteriyor gösterdiği müşteri müşteriler işletme işletmeler ölçüm ölçümler sürüm sürümü güçlü güç hız hızlı süreç süreci öğrenme öğrenmek gün bugün öne önemli büyüyor büyüme çalışıyor çalışan çalışanlar dönüşüm değiştirdi açıkladı geliştirdi gelişme gelişmeler paylaştı yayınlandı çıktı doğrulama doğrulanmış karşılaştırma".split()
_BAD_TR = {word.translate(_TR_FOLD).lower() for word in _TR_WORDS if word.translate(_TR_FOLD) != word}
_NAMED_ANCHORS = set("liquid inference perplexity claude haiku sonnet opus google workspace nous anthropic alibaba qwen gemini deepseek nvidia github hugging meta microsoft openai kimi moonshot".split())
_GENERIC_ANCHORS = {"yapay", "yeni", "bugün", "bir", "bu", "daha", "model", "ai", "llm", "the", "a", "an", "how", "why", "this", "new"}


def validate_idea(idea, news, source_index, fact):
    """Require a copied source fact and reject uncertain quality rather than repair it."""
    if not isinstance(idea, str) or not isinstance(fact, str) or type(source_index) is not int:
        return ""
    if len(idea) > 400 or len(fact) > 240:
        return ""
    idea, fact = _clip(idea, 400), _clip(fact, 240)
    if not idea or not 0 <= source_index < len(news) or len(idea.split()) > 45:
        return ""
    title = _clip(news[source_index].get("title"), 1000)
    if len(fact) < 12 or len(fact.split()) < 2 or fact.casefold() not in title.casefold() or fact.casefold() not in idea.casefold():
        return ""
    numbers = set(re.findall(r"\d+(?:[.,]\d+)*", idea))
    if not numbers <= set(re.findall(r"\d+(?:[.,]\d+)*", title)):
        return ""
    # A numeral/date/version, a named product/entity, or a distinctive mixed-case name.
    tokens = re.findall(r"[\w.-]+", fact, re.UNICODE)
    concrete = any(re.search(r"\d", t) or (t.lower() not in _GENERIC_ANCHORS and
                    (t.lower() in _NAMED_ANCHORS or re.search(r"[a-z][A-Z]", t) or (len(t) > 1 and t.isupper()) or
                     ("-" in t and len(t) > 5))) for t in tokens)
    if not concrete or "?" in idea or re.search(r"\b(siz|sizce|sence|hangi|nasıl|neden|ne|mi|mı|mu|mü|misiniz|mısınız|musunuz|müsünüz)\b", idea, re.I):
        return ""
    if not any(c in "çğıöşüÇĞİÖŞÜ" for c in idea) or any(c in idea for c in ("\ufffd", "Ã", "Å", "Ä")):
        return ""
    words = re.findall(r"[^\W\d_]+", idea, re.UNICODE)
    if any(word.lower() in _BAD_TR for word in words):
        return ""
    return idea


def make_digest(store):
    news = store.news(48)[:25]
    if not news:
        return None
    lines = "\n".join(f"[{i}] {'★' * (n['stars'] or 1)} {n['title']} ({n['src']})" for i, n in enumerate(news))
    out = llm.generate_json(
        "Yapay zekâ dünyasından bugünün başlıkları (yıldız = önem):\n" + lines,
        system=("Sen Jeff'sin. Bilal'e yapay zekâ dünyasında bugün olanları özetliyorsun. Yalnızca verilen başlıklara dayan. "
                "digest: Türkçe, en çok 60 kelime, sade, sesli okunabilir, en önemli gelişmeyi ve Bilal için anlamını söyle. "
                "idea: CyberGene'in sesiyle en çok 45 kelimelik Türkçe bir LinkedIn fikri; ürün satma. ÜÇ SERT ŞART: "
                "(1) Kaynak başlıktan somut sayı, isim, tarih veya sürüm taşı. idea_source_index seçtiğin haberin köşeli parantezdeki sıfır tabanlı indeksi; "
                "idea_fact başlığından birebir alınmış, en az iki kelimelik somut olgu parçası; bu parçayı idea içinde de aynen kullan. "
                "(2) Genel katılım sorusu ve soru cümlesi yazma; Siz bu değişime nasıl ayak uyduruyorsunuz gibi kapanışlar yasak. "
                "(3) ç, ğ, ı, İ, ö, ş, ü harflerini doğru kullan; açık, çözüm, hızla, erişim gibi kelimeleri ASCII'ye çevirme. "
                "Listede geçmeyen kurum veya model adı yasak. idea_fact içindeki ifadeyi idea içinde harfi harfine tekrar et. "
                "İlk haberin başlığı bu koşulları sağlıyorsa onu seç; emin olmadığın sayıyı veya sürümü asla ekleme. "
                "Şartların birini sağlayamıyorsan idea ve idea_fact boş olsun, idea_source_index -1 olsun. "
                "topics: haberlerden çıkan en çok 7 kısa konu etiketi. Kaynak başlıktaki somut bilgi dışında rakam, yüzde, müşteri referansı, fiyat veya garanti uydurma. Em-dash ve emoji kullanma."),
        schema={"type": "OBJECT", "properties": {"digest": {"type": "STRING"}, "idea": {"type": "STRING"},
                                                 "topics": {"type": "ARRAY", "items": {"type": "STRING"}},
                                                 "idea_source_index": {"type": "INTEGER"}, "idea_fact": {"type": "STRING"}},
                "required": ["digest", "idea", "idea_source_index", "idea_fact"]}, temperature=0.0)
    previous = store.get_meta("digest") or {}
    idea = validate_idea(out.get("idea"), news, out.get("idea_source_index"), out.get("idea_fact"))
    d = {"date": datetime.date.today().isoformat(), "digest": _clip(out.get("digest"), 500) or previous.get("digest", ""), "idea": idea,
         "topics": [_clip(t, 30) for t in (out.get("topics") or [])][:7], "made_at": now()}
    if idea:
        n = news[out["idea_source_index"]]
        d["idea_evidence"] = {"title": n["title"], "url": n.get("url", ""), "fact": out["idea_fact"]}
    store.set_meta("digest", d)
    return d


LISTS = (("sira", "Sırada"), ("havuz", "Havuz"), ("bekle", "Yanıt bekleniyor"), ("arsiv", "Arşiv"))


def _j(v, empty):
    if isinstance(v, (dict, list)) or v is None:
        return v if v is not None else empty
    try:
        return json.loads(v) if v else empty
    except ValueError:
        return empty


def next_step(lead, pending=False, approved=False, optout=False, analysing=False, writable=True):
    """The one next step for a lead, from its real state only. The panel, the morning message and Jeff all use this.
    list: sira (waits on Bilal) / havuz (gate and analysis, Jeff's work) / bekle (message sent) / arsiv.
    act: [what the button does, its label]."""
    stage = lead["stage"]
    analysis = _j(lead.get("analysis"), None) or {}
    drafts = _j(lead.get("drafts"), None)
    contacts = _j(lead.get("contacts"), [])
    passed = lead.get("gate") == "geçti" or bool(lead.get("gate_override"))
    nf = len(analysis.get("bulgular") or [])
    from .metrics import no_signal
    if stage == "Kazanıldı":
        return {"list": "arsiv", "text": "Kazanıldı", "tone": "ok"}
    if optout:
        return {"list": "arsiv", "text": "Ret listesinde, bir daha yazılmaz"}
    if stage == "Kapandı":
        return {"list": "arsiv", "text": "Kapandı"}
    if stage == "Yanıt geldi":
        return {"list": "sira", "rank": 0, "text": "Yanıt geldi, okuyun", "act": ["meeting", "Görüşme ayarlandı"]}
    if stage == "Görüşme":
        return {"list": "sira", "rank": 1, "text": "Görüşme nasıl geçti?", "act": ["won", "Kazanıldı"]}
    if analysing and stage != 'Gönderildi':
        return {"list": "havuz", "rank": 0, "text": "Jeff araştırıyor ve taslak hazırlıyor", "busy": True}
    newflow = bool(drafts) or analysis.get("karar") == "bulgu_var"  # Jeff's finding-based message replaces an old draft
    if pending and not newflow:
        return {"list": "sira", "rank": 2, "text": "Eski taslak onayınızı bekliyor", "act": ["appr", "Taslağı aç"]}
    if approved and not newflow:
        return {"list": "sira", "rank": 2, "text": "Onaylı metin gönderilmedi", "act": ["sent", "Gönderdim"]}
    if stage == "Gönderildi":
        if no_signal(lead):
            return {"list": "sira", "rank": 3, "text": "İki mesaj, iki hafta, ses yok", "act": ["lost", "Kapat"]}
        if lead.get("follow_at") and lead["follow_at"] <= now():
            return {"list": "sira", "rank": 3, "text": "Takip zamanı geldi", "act": ["open", "Aç"]}
        return {"list": "bekle", "text": "Yanıt bekleniyor", "act": ["reply", "Yanıt geldi"]}
    if drafts and not contacts:
        if drafts.get('marketing_job'):
            return {"list": "sira", "rank": 4, "text": "Taslak hazır, değerlendirin", "act": ["open", "Taslağı incele"]}
        if not writable:
            return {"list": "sira", "rank": 4, "text": "Mesaj hazır, yazılı kanal yok", "act": ["open", "Yolları gör"]}
        return {"list": "sira", "rank": 4, "text": "Mesaj hazır, gönderin", "act": ["open", "Mesaja geç"]}
    if analysis.get("karar") == "bulgu_var":
        return {"list": "sira", "rank": 5, "text": f"{nf} bulgu var, mesajı Jeff yazsın", "act": ["drafts", "Mesajı yazdır"]}
    if analysis.get("karar") == "gerek_yok":
        return {"list": "arsiv", "text": "Keskin bulgu yok, yazılmıyor"}
    if lead.get("gate") == "elendi" and not lead.get("gate_override"):
        return {"list": "arsiv", "text": "Kapıda elendi"}
    if analysing:
        return {"list": "havuz", "rank": 0, "text": "Jeff araştırıyor", "busy": True}
    if passed:
        return {"list": "havuz", "rank": 1, "text": "Analiz yarım kaldı" if analysis.get("karar") == "hata" else "Analiz bekliyor", "act": ["analyze", "Analiz et"]}
    if lead.get("gate") == "şüpheli":
        return {"list": "havuz", "rank": 2, "text": "Kapı emin olamadı, karar sizin", "act": ["open", "İncele"]}
    return {"list": "havuz", "rank": 3, "text": "Kapı bekliyor", "act": ["gate-rerun", "Kapıdan geçir"]}


def steps(store, leads=None, *, marketing_views=None, qualification_views=None):
    """next_step for every lead, keyed by id, with approvals, opt-outs and running analyses read once."""
    leads = store.leads() if leads is None else leads
    pending = {a["lead_id"] for a in store.approvals() if a["status"] == "Bekliyor"}
    ok = approved_leads(store)
    optouts = {r["lead_id"] for r in store.q("SELECT lead_id FROM optout")}
    running = set()
    for j in store.jobs(20):
        if j["kind"] in ("analysis", "marketing") and j["status"] in ("running", "queued"):
            running |= set((_j(j.get("params"), {}) or {}).get("ids") or [])
    from . import reach
    result = {l["id"]: next_step(l, l["id"] in pending, l["id"] in ok, l["id"] in optouts, l["id"] in running, reach.writable(l)) for l in leads}
    from . import marketing, qualification
    marketing_views = marketing.views(store) if marketing_views is None else marketing_views
    qualification_views = qualification.views(store) if qualification_views is None else qualification_views
    for lead in leads:
        lid = lead['id']
        if lid in optouts or lid in running or lead['stage'] in ('Gönderildi','Yanıt geldi','Görüşme','Kazanıldı','Kapandı'):
            continue
        m = marketing_views.get(lid) or {}
        q = qualification_views.get(lid) or {}
        if m.get('source') == 'qualification':
            if not m.get('current'):
                text = 'Taslak yeniden inceleme gerektiriyor' if m.get('published_at') else 'Taslak denetlenemedi; gerekçeyi inceleyin' if m.get('status') == 'failed' else 'Jeff kaynaklı taslağı hazırlıyor'
            else:
                text = {'accepted':'Taslak uygun bulundu; gönderilmedi', 'rejected':'Taslak uygun bulunmadı; yeniden hazırlatın'}.get((m.get('review') or {}).get('decision'),'Kaynaklı taslağı değerlendirin')
            result[lid] = {'list':'sira','rank':4,'text':text,'act':['open','Taslağı incele']}
        elif q.get('current') and q.get('decision') == 'gorusme_adayi':
            result[lid] = {'list':'havuz','rank':1,'text':'Kaynaklı görüşme adayı; taslağı Jeff hazırlasın','act':['prepare-qualified','Taslak hazırlat']}
    return result


def approved_leads(store):
    return {a["lead_id"] for a in store.q("SELECT lead_id FROM approvals WHERE status='Onaylandı' AND lead_id IS NOT NULL")}


def briefing(store):
    """Jeff's morning message, built from real counts. No model call, so it is instant and cannot invent anything."""
    opps = [o for o in store.opps() if o["status"] in ("Yeni", "Takipte")]
    strong = sorted(opps, key=lambda o: -(o.get("stars") or 0))
    leads = store.leads()
    st = steps(store, leads)
    mine = [s for s in st.values() if s["list"] == "sira"]
    ready = sum(1 for s in mine if s["text"].startswith("Mesaj hazır"))
    to_analyse = sum(1 for s in st.values() if s.get("act") and s["act"][0] == "analyze")
    appr = [a for a in store.approvals() if a["status"] == "Bekliyor"]
    parts = []
    if not store.get_meta("last_run"):
        return {"text": "Merhaba. Radar henüz hiç çalışmadı. Radar ekranından ilk taramayı başlatabilirsiniz.", "focus": None}
    h = datetime.datetime.now().hour
    hello = "Günaydın" if h < 12 else "İyi günler" if h < 18 else "İyi akşamlar"
    parts.append(f"{hello}.")
    if mine:
        parts.append(f"{len(mine)} işletme sizden bir adım bekliyor" + (f", {ready} tanesinin mesajı hazır." if ready else "."))
    if to_analyse:
        parts.append(f"{to_analyse} işletme analiz bekliyor.")
    if appr:
        parts.append(f"{len(appr)} onay bekliyor.")
    focus = None
    if strong and (strong[0].get("stars") or 0) >= 4:
        o = strong[0]
        focus = {"opp": o["id"], "city": o["city"]}
        parts.append(f"Fırsatlarda öne çıkan: {o['title']}.")
    if not (opps or appr or mine):
        parts.append("Şu an sizi bekleyen bir şey yok.")
    return {"text": " ".join(parts), "focus": focus}


def jeff_context(store):
    from . import qualification
    opps = sorted([o for o in store.opps() if o["status"] != "Geçildi"], key=lambda o: -(o.get("stars") or 0))[:10]
    leads = store.leads()
    ok = approved_leads(store)
    appr = [a for a in store.approvals() if a["status"] == "Bekliyor"]
    news = store.news(48)[:10]
    jobs = store.jobs(6)
    st = steps(store, leads)
    counts = {k: 0 for k, _ in LISTS}
    for s in st.values():
        counts[s["list"]] += 1
    o_txt = "\n".join(f"- {'★' * (o.get('stars') or 1)} {o['title']} ({o['src']}, durum: {o['status']})" for o in opps) or "- yok"
    l_txt = "\n".join([f"- {l['name']} ({l['city'] or 'şehir yok'}, {l['sector'] or 'sektör yok'}), aşama: {l['stage']}"
                       + f", sıradaki adım: {st[l['id']]['text']}"
                       for l in sorted(leads, key=lambda l: (st[l["id"]]["list"] != "sira", st[l["id"]].get("rank", 9)))
                       if st[l["id"]]["list"] in ("sira", "bekle")][:15]) or "- yok"
    n_txt = "\n".join(f"- {'★' * (n.get('stars') or 1)} {n['title']}" for n in news) or "- yok"
    a_txt = "\n".join(f"- {a['channel']}: {a['target']}" for a in appr) or "- yok"
    j_txt = "\n".join(f"- {j['title']}: {({'queued': 'sırada', 'running': 'çalışıyor', 'done': 'bitti', 'failed': 'olmadı', 'cancelled': 'durduruldu'}).get(j['status'], j['status'])}"
                      f" (%{j['progress']}) {j['note'] or ''}" for j in jobs) or "- yok"
    sec = ", ".join(f"{label}: {counts[k]}" for k, label in LISTS)
    from .metrics import funnel
    sec += "\nHuni: " + " → ".join(f"{x['step']} {x['n']}" for x in funnel(leads))
    shortlist = qualification.board(store)
    sec += f"\nGörüşme adayı hedefi: {len(shortlist['ids'])}/10. İhtiyaç ve satın alma niyeti görüşmede doğrulanmalı."
    sec += "\nAday firma kimlikleri: " + ", ".join(shortlist['ids'])
    d = store.get_meta("digest") or {}
    return (f"Radar son çalışma: {store.get_meta('last_summary', 'henüz çalışmadı')}\n\nSon görevler (Radar ekranında görünür):\n{j_txt}\n\n"
            f"Fırsatlar (yıldız = önem):\n{o_txt}\n\nLead listeleri: {sec}\nÜzerinde çalışılan leadler:\n{l_txt}\n\n"
            f"Yapay zekâ haberleri:\n{n_txt}\n\nOnay bekleyenler:\n{a_txt}\n\nGünün özeti: {d.get('digest', '')}")[:4200]


def lead_research(store, lead):
    """Jeff's research note, written only from what Bilal gave (name, city, sector, notes, source quote)."""
    opp = store.one("SELECT quote, why FROM opps WHERE id=?", (lead.get("opp_id"),)) if lead.get("opp_id") else None
    facts = (f"İşletme: {lead['name']}\nŞehir: {lead.get('city') or 'bilinmiyor'}{', ' + lead['district'] if lead.get('district') else ''}\n"
             f"Sektör: {lead.get('sector') or 'bilinmiyor'}\nKaynak: {lead.get('src')}\n"
             f"Web sitesi var mı: {'evet' if lead.get('website') else 'bilinmiyor'}\nHarita bilgisi: {lead.get('size') or 'yok'}\n"
             f"Bilal'in notu: {lead.get('note') or 'yok'}\n"
             + (f"Kaynak alıntısı: {opp['quote']}\n" if opp else ""))
    out = llm.generate_json(
        facts,
        system=("Sen Jeff'sin. Bir potansiyel müşteri için kısa araştırma notu yazıyorsun. SADECE yukarıdaki bilgilere dayan; internette arama yapmadın. "
                "Bilgi yetersizse ilgili alana 'Bilinmiyor' yaz. Tahmin ettiğin yerin sonuna ' (tahmin)' ekle. Türkçe, sade, her alan en çok 22 kelime. "
                "need: işletmenin yaşadığı ihtiyaç. fit: CyberGene'in dijital çalışanı bunda nasıl yardımcı olabilir (mesaj/randevu/teklif/takip gibi). "
                "size: büyüklük. " + NO_CLAIMS),
        schema={"type": "OBJECT", "properties": {k: {"type": "STRING"} for k in ("need", "fit", "size")}})
    return {k: _clip(out.get(k), 160) for k in ("need", "fit", "size")}


def lead_draft(store, lead, channel):
    facts = (f"İşletme: {lead['name']}\nŞehir: {lead.get('city') or '-'}\nSektör: {lead.get('sector') or '-'}\n"
             f"İhtiyaç: {lead.get('need') or '-'}\nBizim karşılığımız: {lead.get('fit') or '-'}\nKanal: {channel}")
    text = llm.generate(
        facts,
        system=("Bilal'in göndereceği ilk mesajı yazıyorsun. Mesaj doğrudan Bilal'in ağzından çıkar: Türkçe, ilk kişi tekil, sıcak ama sade. "
                "'Merhaba, ben Bilal, CyberGene'den.' diye başla. 'Bilal adına', 'Jeff' ya da 'dijital asistan' diye söz etme, imza ekleme. "
                "WhatsApp ise 2-3 kısa cümle; E-posta ise konu satırı yok, 4-5 cümle. En çok 70 kelime. "
                "Önce işletmenin durumunu anladığını göster, sonra 15 dakikalık kısa bir görüşme öner. Ürün özelliği sıralama. "
                + NO_CLAIMS + " Yalnızca mesaj metnini yaz, açıklama ekleme."), temperature=0.5, max_tokens=300)
    return _clip(text, 700)


def manual_opportunity(store, text, url="", city=None):
    """Bilal pasted a post he found (X, LinkedIn, anywhere). Nothing is fetched from the link."""
    item = {"id": "c0", "src": "Elle eklenen", "sub": "sizin eklediğiniz", "title": text[:120], "text": text}
    cfg = store.get_meta("config", {}) or {}
    from .sources import DEFAULT_CONFIG
    v = scoring.classify([item], cfg.get("definition") or DEFAULT_CONFIG["definition"]).get("c0")
    if not v or v["kind"] == "ignore":
        v = {"title": _clip(text, 120), "why": "Jeff bunu güçlü bir fırsat olarak görmedi; yine de sizin eklediğiniz için listede.",
             "move": "Kaynağa kendiniz bakıp karar verin.", "strength": "Zayıf", "stars": 2, "tags": []}
    v["step"] = v.get("move", "")
    v["city"] = city
    return store.add_opp({**v, "src": "Elle eklenen", "sub": "sizin eklediğiniz", "url": url or f"manual:{time.time()}", "quote": text[:280],
                          "published_at": now()})
