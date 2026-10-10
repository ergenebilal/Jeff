"""HTTP layer for CybergeneOS. Standard library only.

Rules this file keeps:
- The Gemini key never leaves the process; nothing here can send a message anywhere.
- "Gönderildi" and "Yanıt geldi" only happen when Bilal says so. Approving a draft does not send it.
- Only GET /api/*, the panel files and POST /api/* are served. Everything else is 404.
"""
import hashlib
import hmac
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import analysis, briefing, contact, geo, intent, jeff, llm, marketing, metrics, outreach, places, qualification, reach, sources
from .jobs import Jobs
from .radar import Radar
from .store import CLOSED, STAGES, Store, now

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE.parent.parent
PORT = int(os.environ.get("CGOS_PORT", "5601"))
HOST = os.environ.get("CGOS_HOST", "127.0.0.1")
ALLOWED = {h.strip() for h in os.environ.get("CGOS_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",") if h.strip()}
PASSWORD = os.environ.get("CGOS_PASSWORD", "")
SECURE_COOKIE = os.environ.get("CGOS_SECURE_COOKIE") == "1"
# Only the web server on this machine may tell us the visitor's real address (cybergene.co/panel goes through nginx).
PROXIES = {h.strip() for h in os.environ.get("CGOS_TRUSTED_PROXIES", "127.0.0.1,::1").split(",") if h.strip()}
LOGIN_FAILS, LOGIN_WINDOW = 8, 15 * 60  # wrong passwords per address per window
LOGIN_FAILS_ALL = 40  # wrong passwords from everyone together per window: past this, nobody can log in until it cools down
DATA = Path(os.environ.get("CGOS_DATA", HERE / "data"))
SERVED = [HERE, ROOT / "public" / "fonts", ROOT / "public" / "logo-480.webp"]
HIDDEN_DIRS = {"data", "server", "tests", "deploy"}
TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
         ".woff2": "font/woff2", ".webp": "image/webp", ".png": "image/png", ".svg": "image/svg+xml"}

store = None
radar = None
jobs = None
JEFF_TOKEN = ""
_hits = {}
_fails = {}
_lock = threading.Lock()

# What Jeff may do with his own token (from the server, without the browser login). Nothing here can send a message anywhere.
JEFF_GET = {("api", "jobs"), ("api", "summary"), ("api", "state")}
JEFF_POST = {("api", "jobs"), ("api", "radar", "run"), ("api", "lead"), ("api", "opp", "manual")}


# ---------------- state ----------------
def _tags(s):
    return [t for t in (s or "").split(",") if t]


def job_view(j, pins=False):
    found = []
    if pins and j["kind"] == "lead_scan":
        found = [{"id": l["id"], "name": l["name"], "lat": l["lat"], "lon": l["lon"], "phone": bool(l["phone"]), "web": bool(l["website"]), "gate": l["gate"]}
                 for l in store.leads_by_ids((j["result"] or {}).get("ids") or [])]
    return {"found": found, "id": j["id"], "kind": j["kind"], "title": j["title"], "params": j["params"], "status": j["status"], "progress": j["progress"],
            "note": j["note"], "log": j["log"][-14:], "result": j["result"], "by": j["created_by"], "created_at": j["created_at"],
            "started_at": j["started_at"], "finished_at": j["finished_at"]}


def jobs_view():
    """Recent jobs; the three latest business scans also carry their map pins."""
    rows, pinned = store.jobs(16), 0
    out = []
    for j in rows:
        pins = j["kind"] == "lead_scan" and pinned < 3
        pinned += pins
        out.append(job_view(j, pins))
    return out


def source_view(cfg):
    health = {s["name"]: s for s in store.q("SELECT * FROM sources")}
    groups = {}
    for name, group, _, _ in sources.plan(cfg):
        h = health.get(name)
        groups.setdefault(group, []).append({"name": name, "state": h["state"] if h else "bekliyor", "last_ok": h["last_ok"] if h else None,
                                             "count": h["count"] if h else 0})
    out = []
    for g, items in groups.items():
        ok = sum(1 for i in items if i["state"] == "ok")
        down = sum(1 for i in items if i["state"] in ("down", "slow"))
        out.append({"name": g, "items": items, "ok": ok, "down": down,
                    "state": "ok" if ok and not down else "down" if down and not ok else "slow" if down else "bekliyor",
                    "count": sum(i["count"] for i in items), "last_ok": max([i["last_ok"] or 0 for i in items]) or None})
    return out


def lead_detail(lid):
    l = store.lead(lid)
    if not l:
        return None
    l["events"] = store.q("SELECT ts,title,detail FROM events WHERE lead_id=? ORDER BY ts,id", (lid,))
    ok = briefing.approved_leads(store)
    optouts = {r["lead_id"] for r in store.q("SELECT lead_id FROM optout")}
    marketing_views = marketing.views(store)
    qualification_views = qualification.views(store)
    st = briefing.steps(store, [l], marketing_views=marketing_views, qualification_views=qualification_views)
    you = briefing.you_text(l, l["id"] in ok)
    return {**{k: l[k] for k in ("id", "name", "city", "district", "sector", "category", "src", "stage", "need", "fit", "channel", "size",
                                            "note", "draft", "phone", "website", "email", "address", "lat", "lon", "ref", "opened_at", "tried_at",
                                            "gate", "gate_at", "gate_override")},
                      "gate_reasons": json.loads(l["gate_reasons"] or "[]"), "gate_info": json.loads(l["gate_info"] or "{}"),
                      "analysis": json.loads(l["analysis"] or "null"), "analysis_at": l["analysis_at"], "marketing": marketing_views.get(l['id']),
                      "qualification": qualification_views.get(l['id']),
                      "drafts": json.loads(l["drafts"] or "null"), "contacts": json.loads(l["contacts"] or "[]"),
                      "optout": l["id"] in optouts, "wa": reach.whatsapp_number(l["phone"]),
                      "instagram": reach.instagram_of(l), "form": reach.has_form(l),
                      "short": outreach.short_name(l["name"]),
                      "str": l["strength"], "you": you, "due": bool(you), "lastTouch": l["last_touch"], "follow_at": l["follow_at"],
                      "created_at": l["created_at"], "updated_at": l["updated_at"], "reviewed": bool(l["reviewed_at"]), "job": l["job_id"],
                      "section": briefing.section_of(l), "step": st[l["id"]], "events": [[e["ts"], e["title"], e["detail"]] for e in l["events"]], "opp": l["opp_id"]}


def build_state():
    cfg = radar.config()
    t = now()
    opps = [{"id": o["id"], "src": o["src"], "sub": o["sub"], "url": o["url"] if o["url"].startswith("http") else "", "title": o["title"],
             "quote": o["quote"], "why": o["why"], "step": o["step"], "gain": o["gain"] or "", "move": o["move"] or o["step"] or "",
             "effort": o["effort"] or "", "stars": o["stars"] or (5 if o["strength"] == "Güçlü" else 4 if o["strength"] == "Orta" else 2),
             "tags": _tags(o["tags"]), "status": o["status"], "ts": o["published_at"],
             "fresh": o["status"] == "Yeni" and t - o["found_at"] < 6 * 3600} for o in store.opps()]
    news = [{"id": n["id"], "src": n["src"], "url": n["url"], "title": n["title"], "why": n["why"], "stars": n["stars"] or 2,
             "tags": _tags(n["tags"]), "also": n["also"] or 0, "ts": n["published_at"]} for n in store.news()]
    leads = []
    ok = briefing.approved_leads(store)
    optouts = {r["lead_id"] for r in store.q("SELECT lead_id FROM optout")}
    all_leads = store.leads()
    marketing_views = marketing.views(store)
    qualification_views = qualification.views(store)
    st = briefing.steps(store, all_leads, marketing_views=marketing_views, qualification_views=qualification_views)
    for l in all_leads:
        q = qualification_views.get(l["id"]) or {}
        a = json.loads(l["analysis"] or "null") or {}
        findings = a.get("bulgular") or []
        reasons = json.loads(l["gate_reasons"] or "[]")
        info = json.loads(l["gate_info"] or "{}")
        summary = ("İhtiyaç hipotezi: " + q["hypothesis"] if q.get("current") and q.get("hypothesis")
                   else "İş hipotezi: " + str(findings[0].get("baslik", "")) if findings
                   else info.get("first_gap") or (reasons[0].get("text") if reasons else "") or l["category"] or l["sector"] or "")
        leads.append({**{k: l[k] for k in ("id", "name", "city", "district", "sector", "category", "stage", "channel",
                                          "lat", "lon", "gate", "gate_override", "created_at", "updated_at", "follow_at")},
                      "short": outreach.short_name(l["name"]), "due": bool(briefing.you_text(l, l["id"] in ok)),
                      "optout": l["id"] in optouts, "reviewed": bool(l["reviewed_at"]), "job": l["job_id"],
                      "section": briefing.section_of(l), "step": st[l["id"]], "summary": str(summary)[:120],
                      "qualification": {k: q.get(k) for k in ("current", "decision", "score", "job_id")} if q else None})
    d = store.get_meta("digest") or {}
    return {"now": t, "opps": opps, "news": news, "leads": leads, "approvals": store.approvals(), "sources": source_view(cfg),
            "jobs": [{**j, "log": j["log"][-6:]} for j in jobs_view()], "places": places.provider(),
            "places_usage": {"n": places.usage(), "cap": places.MONTHLY_CAP, "key": bool(os.environ.get("GOOGLE_PLACES_KEY"))},
            "digest": d.get("digest", ""), "idea": d.get("idea", ""), "topics": d.get("topics", []),
            "briefing": briefing.briefing(store), "radar": radar.status(), "voice": llm.ready(), "voices": sorted(llm.VOICES), "jeff": jeff.mode(),
            "arguments": [{k: a[k] for k in ("id", "title", "pain", "soru", "honest_limit")} for a in outreach.arguments().get("arguments", [])],
            "metrics": metrics.report(store.leads(), places.usage(), places.details_usage()),
            "meeting_candidates": qualification.board(store, qualification_views),
            "stages": STAGES, "sections": briefing.SECTIONS, "cities": {n: list(c) for n, c in geo.PROVINCES.items()},
            "districts": geo.DISTRICTS}


def scan_now(text):
    """A clear 'scan X in Y' command starts the scan at once. Jeff is told it already runs, so he only confirms."""
    if not jobs:
        return None
    p = intent.parse_scan(text)
    if not p:
        return None
    jid, e = jobs.start("lead_scan", p, "jeff")
    if not jid and e == "zaten_calisiyor":
        jid = next((j["id"] for j in jobs.active() if j["kind"] == "lead_scan" and j["params"].get("city") == p["city"]), None)
    if not jid:
        return None
    where = (p["district"] + ", " if p["district"] else "") + p["city"]
    note = (f"PANEL NOTU: Bilal'in bu komutunu panel anladı ve işletme taramasını ŞU AN başlattı ({p['niche']}, {where}, en çok {p['limit']} işletme, görev {jid}). "
            "Taramayı tekrar başlatma ve cybergeneos API'sini bu tarama için çağırma. Bilal'e tek kısa cümleyle taramanın başladığını, "
            "bulunan işletmelerin Komuta ekranındaki haritada numaralı olarak belireceğini söyle.")
    c = geo.PROVINCES.get(p["city"])
    return {"id": jid, "city": p["city"], "district": p["district"], "niche": p["niche"], "limit": p["limit"],
            "lon": c[0] if c else None, "lat": c[1] if c else None, "note": note}


def summary():
    """A short, plain view for Jeff: what is running, what was found, what waits on Bilal."""
    leads = store.leads()
    st = briefing.steps(store, leads)
    counts = {k: 0 for k, _ in briefing.LISTS}
    for s in st.values():
        counts[s["list"]] += 1
    return {"jobs": [{k: j[k] for k in ("id", "title", "status", "progress", "note")} for j in store.jobs(8)],
            "meeting_candidates": qualification.board(store),
            "leads": {label: counts[k] for k, label in briefing.LISTS},
            "sizden_bekleyen": [{"isletme": outreach.short_name(l["name"]), "adim": st[l["id"]]["text"]}
                                for l in sorted(leads, key=lambda l: st[l["id"]].get("rank", 9)) if st[l["id"]]["list"] == "sira"][:10],
            "gate": {g: sum(1 for l in leads if l["gate"] == g) for g in ("geçti", "şüpheli", "elendi")} | {"bekliyor": sum(1 for l in leads if not l["gate"])},
            "opps": [{"title": o["title"], "stars": o["stars"], "move": o["move"], "url": o["url"]}
                     for o in sorted(store.opps(), key=lambda o: -(o["stars"] or 0)) if o["status"] in ("Yeni", "Takipte")][:8],
            "news": [{"title": n["title"], "stars": n["stars"]} for n in store.news(48)][:8],
            "metrics": {k: v for k, v in metrics.report(leads).items() if k in ("funnel", "scorecard")},
            "radar": store.get_meta("last_summary", ""), "lead_source": "Google Haritalar" if places.provider() == "google" else "OpenStreetMap"}


TR_WORDS = {"randevu", "yapay", "kobi", "müşteri", "işletme", "otomasyon", "dijital", "mesaj", "asistan", "teklif", "esnaf"}


def news_query(q):
    """Turkish queries read Google News Turkey, everything else reads the US edition."""
    turkish = any(c in "çğıöşüÇĞİÖŞÜ" for c in q) or bool(TR_WORDS & set(q.lower().split()))
    return {"q": q, "hl": "tr", "gl": "TR", "ceid": "TR:tr"} if turkish else {"q": q, "hl": "en", "gl": "US", "ceid": "US:en"}


def clean_config(d, cur):
    out = dict(cur)
    def lines(v, n=20, m=140):
        v = v if isinstance(v, list) else str(v).splitlines()
        return [str(x).strip()[:m] for x in v if str(x).strip()][:n]
    if "definition" in d:
        out["definition"] = str(d["definition"]).strip()[:1500] or sources.DEFAULT_CONFIG["definition"]
    for k in ("hn_queries", "telegram_channels"):
        if k in d:
            out[k] = lines(d[k])
    if "github_topics" in d:
        out["github_topics"] = [t.lstrip("#").lower() for t in lines(d["github_topics"], 10, 40) if all(c.isalnum() or c in "-_" for c in t.lstrip("#"))]
    if "feeds" in d:
        feeds = []
        for line in lines(d["feeds"], 20, 300):
            name, _, url = line.rpartition("|") if "|" in line else ("", "", line)
            url = url.strip()
            if url.startswith(("https://", "http://")):
                feeds.append({"name": name.strip()[:60] or urlparse(url).hostname or url[:60], "url": url})
        out["feeds"] = feeds
    if "news_queries" in d:
        out["news_queries"] = [news_query(q) for q in lines(d["news_queries"])]
    if "interval_min" in d:
        out["interval_min"] = max(15, min(720, int(d["interval_min"])))
    return out


# ---------------- actions ----------------
def err(code, msg):
    return code, {"error": msg}


def act_opp(oid, action, body):
    o = store.one("SELECT * FROM opps WHERE id=?", (oid,))
    if not o:
        return err(404, "yok")
    if action in ("skip", "restore", "track", "done"):
        store.set_opp_status(oid, {"skip": "Geçildi", "restore": "Yeni", "track": "Takipte", "done": "Yapıldı"}[action])
        return 200, {"ok": True}
    if action == "to-lead":
        if o["lead_id"] and store.lead(o["lead_id"]):
            return 200, {"ok": True, "lead": o["lead_id"]}
        lead = {"name": o["title"][:90], "city": o["city"], "sector": o["sector"], "src": o["src"], "strength": o["strength"], "stage": "İncelendi",
                "draft": o["draft"], "need": o["why"], "opp_id": oid, "note": ""}
        if o["draft"]:
            lead["stage"] = "Taslak hazır"
        lid = store.create_lead(lead, "Fırsattan lead olarak eklendi", o["src"] + (", " + o["sub"] if o["sub"] else ""))
        store.add_event(lid, f"Jeff inceledi: {o['strength']}", "")
        if o["draft"]:
            store.add_event(lid, "Taslak hazırlandı", "Fırsat sırasında")
        store.x("UPDATE opps SET lead_id=?, status='Takipte' WHERE id=?", (lid, oid))
        if llm.ready():
            try:
                r = briefing.lead_research(store, store.lead(lid))
                store.update_lead(lid, {k: v for k, v in r.items() if v and v != "Bilinmiyor"})
                store.add_event(lid, "Jeff araştırma notunu hazırladı", "Yalnızca kaynak metne dayanır")
            except Exception:
                pass
        return 200, {"ok": True, "lead": lid}
    if action == "to-approval":
        text = str(body.get("text", o["draft"])).strip()[:1500]
        if not text:
            return err(400, "bos")
        store.x("UPDATE opps SET draft=?, status='Takipte' WHERE id=?", (text, oid))
        aid = store.create_approval({"opp_id": oid, "lead_id": o["lead_id"], "channel": f"{o['src']} yanıtı", "target": o["sub"] or o["src"], "text": text})
        if o["lead_id"] and store.lead(o["lead_id"]):
            store.update_lead(o["lead_id"], {"stage": "Onay bekliyor", "draft": text})
            store.add_event(o["lead_id"], "Onayınıza sunuldu", "")
        return 200, {"ok": True, "approval": aid}
    return err(404, "yok")


def act_lead(lid, action, body):
    l = store.lead(lid)
    if not l:
        return err(404, "yok")
    if action == 'qualify':
        jid, e = jobs.start('qualification', {'ids': [lid], 'request_key': body.get('request_key')}, 'bilal')
        return (200, {'ok': True, 'job': jid}) if jid else (409, {'error': 'secim_baslamadi', 'detail': e})
    if action in ('prepare', 'prepare-qualified'):
        jid, e = jobs.start('marketing', {'ids': [lid], 'request_key': body.get('request_key'),
                                         'source':'qualification' if action == 'prepare-qualified' else 'research',
                                         'note':body.get('note','')}, 'bilal')
        return (200, {'ok': True, 'job': jid}) if jid else (409, {'error': 'inceleme_baslamadi', 'detail': e})
    if action == 'draft-review':
        try:
            return 200, {'ok': True, **marketing.review(store, lid, body.get('digest'), body.get('decision'), body.get('text'))}
        except (marketing.Conflict, contact.Refused) as e:
            return 409, {'error': 'taslak_degisti', 'detail': str(e)}
    if action in ('drafts', 'draft') and json.loads(l.get('drafts') or '{}').get('source') == 'qualification':
        return 409, {'error':'karsit_inceleme_gerekli', 'detail':'Kaynaklı taslağı değiştirmek için güncel rapordan Jeff’e yeniden hazırlatın; yeni metin karşıt incelemeden geçmeli.'}
    if action in ('drafts', 'draft', 'research') and store.one("SELECT 1 FROM marketing_runs r JOIN jobs j ON j.id=r.job_id WHERE r.lead_id=? AND j.status IN ('queued','running')", (lid,)):
        return 409, {'error': 'inceleme_suruyor', 'detail': 'Jeff firma için inceleme ve taslak hazırlıyor; bitmesini bekleyin.'}
    if action in ("drafts", "contacted", "email", "optout"):
        try:
            if action == "drafts":
                use = [i for i in (body.get("use") or []) if isinstance(i, int)]
                return 200, {"ok": True, "drafts": contact.write_drafts(store, l, use, str(body.get("note", "")))}
            if action == "contacted":
                ch = str(body.get("channel", ""))
                if ch not in ("whatsapp", "instagram", "form"):
                    return err(400, "kanal")
                contact.must_allow(store, l, need_finding=False)
                return 200, {"ok": True, "contact": contact.record_contact(store, l, ch, str(body.get("text", ""))[:2000])}
            if action == "email":
                return 200, {"ok": True, "contact": contact.send_email(store, l, str(body.get("to", "")), str(body.get("subject", "")), str(body.get("body", "")))}
            contact.opt_out(store, l, str(body.get("reason", "")))
            return 200, {"ok": True}
        except contact.Refused as e:
            return 409, {"error": "reddedildi", "detail": str(e)}
        except analysis.NotReady as e:
            return 503, {"error": "analiz_hazir_degil", "detail": str(e)}
    if action == "link":
        if contact.opted_out(store, lid):
            return 409, {"error": "reddedildi", "detail": "Bu işletme ret listesinde; bağlantı hazırlanmaz."}
        aid = str(body.get("argument", ""))
        if not outreach.argument(aid):
            return err(400, "arguman")
        ref = l["ref"] or outreach.new_ref()
        if not l["ref"]:
            store.update_lead(lid, {"ref": ref})
        url = contact.short_link(store, outreach.showroom_link(l["name"], ref, aid))
        store.add_event(lid, "Kişisel bağlantı hazırlandı: " + outreach.argument(aid)["title"], "Bağlantı açılınca burada görünür")
        return 200, {"ok": True, "url": url, "ref": ref}
    if action == "gate-override":
        store.update_lead(lid, {"gate_override": 1, "reviewed_at": l["reviewed_at"] or now()})
        store.add_event(lid, "Kapıda elenmişti, havuza siz aldınız", "Sizin kararınızla")
        return 200, {"ok": True}
    if action == "observe":
        text = str(body.get("text", "")).strip()
        if len(text) < 15:
            return err(400, "kisa")
        url = str(body.get("url", "")).strip()
        store.add_observation(lid, text, url if url.startswith(("http://", "https://")) else "")
        store.add_event(lid, "Gözlem eklendi", "Sizin yapıştırdığınız metin; kapı yeniden değerlendirir")
        jid, e = jobs.start("gate", {"ids": [lid]}, "bilal")
        return 200, {"ok": True, "job": jid}
    if action == "analyze":
        if l["gate"] != "geçti" and not l["gate_override"]:
            return err(400, "kapi")
        try:
            analysis.check_ready()
        except analysis.NotReady as e:
            return 503, {"error": "analiz_hazir_degil", "detail": str(e)}
        jid, e = jobs.start("analysis", {"ids": [lid]}, "bilal")
        return (200, {"ok": True, "job": jid}) if jid else err(409, e)
    if action == "gate-rerun":
        jid, e = jobs.start("gate", {"ids": [lid]}, "bilal")
        return (200, {"ok": True, "job": jid}) if jid else err(409, e)
    if action == "review":
        if not l["reviewed_at"]:
            store.update_lead(lid, {"reviewed_at": now()})
        return 200, {"ok": True}
    if action == "update":
        ch = {k: body[k] for k in ("name", "city", "district", "sector", "channel", "note", "need", "fit", "size", "draft", "phone", "website", "email", "address")
              if k in body}
        if "city" in ch:
            ch["city"] = geo.canon_city(ch["city"]) or None
        for k, v in ch.items():
            ch[k] = str(v or "")[:1500] if k in ("note", "draft", "need", "fit") else (v if k == "city" else str(v or "")[:200])
        if ch.get("website") and not ch["website"].startswith(("http://", "https://")):
            ch["website"] = "https://" + ch["website"]
        ch["reviewed_at"] = l["reviewed_at"] or now()
        if "stage" in body and (body["stage"] in STAGES or body["stage"] == CLOSED) and body["stage"] != l["stage"]:
            ch["stage"] = body["stage"]
            reason = str(body.get("reason") or "").strip()[:300]
            store.add_event(lid, "Aşama elle değiştirildi: " + body["stage"], ("Gerekçe: " + reason) if reason else "Sizin tarafınızdan")
            if body["stage"] in (CLOSED, "Kazanıldı", "Görüşme"):
                ch["follow_at"] = None
        if "follow_days" in body:
            days = int(body["follow_days"])
            ch["follow_at"] = now() + days * 86400 if days > 0 else None
            store.add_event(lid, f"Hatırlatma kuruldu: {days} gün sonra" if days > 0 else "Hatırlatma kaldırıldı", "Hatırlatma yalnızca size haber verir, kimseye mesaj atmaz")
        store.update_lead(lid, ch)
        return 200, {"ok": True}
    if action == "reply":
        store.update_lead(lid, {"stage": "Yanıt geldi", "last_touch": time.strftime("%d.%m.%Y") + " yanıt geldi", "follow_at": None})
        store.add_event(lid, "Yanıt geldi", "Sizin bildiriminizle")
        return 200, {"ok": True}
    if action == "sent":
        store.update_lead(lid, {"stage": "Gönderildi", "last_touch": time.strftime("%d.%m.%Y") + " elle gönderildi", "follow_at": now() + 3 * 86400})
        store.add_event(lid, "Elle gönderildi", "Sizin bildiriminizle; 3 gün sonra takip hatırlatması kuruldu")
        return 200, {"ok": True}
    if action == "research":
        if not llm.ready():
            return err(503, "anahtar_yok")
        r = briefing.lead_research(store, l)
        ch = {k: v for k, v in r.items() if v}
        if l["stage"] == "Yeni":
            ch["stage"] = "İncelendi"
        store.update_lead(lid, ch)
        store.add_event(lid, "Jeff araştırma notunu hazırladı", "Yalnızca sizin verdiğiniz bilgilere dayanır")
        return 200, {"ok": True}
    if action == "draft":
        if not llm.ready():
            return err(503, "anahtar_yok")
        channel = str(body.get("channel") or l["channel"] or "WhatsApp")[:40]
        text = briefing.lead_draft(store, l, channel)
        ch = {"draft": text, "channel": channel}
        if l["stage"] in ("Yeni", "İncelendi"):
            ch["stage"] = "Taslak hazır"
        store.update_lead(lid, ch)
        store.add_event(lid, "Taslak hazırlandı", channel)
        return 200, {"ok": True, "text": text}
    if action == "to-approval":
        text = str(body.get("text", l["draft"])).strip()[:1500]
        if not text:
            return err(400, "bos")
        aid = store.create_approval({"lead_id": lid, "channel": l["channel"] or "Mesaj", "target": l["name"], "text": text})
        store.update_lead(lid, {"stage": "Onay bekliyor", "draft": text})
        store.add_event(lid, "Onayınıza sunuldu", "")
        return 200, {"ok": True, "approval": aid}
    return err(404, "yok")


def act_approval(aid, action, body):
    a = store.approval(aid)
    if not a:
        return err(404, "yok")
    lid = a["lead_id"]
    if action == "edit":
        store.x("UPDATE approvals SET text=? WHERE id=?", (str(body.get("text", ""))[:1500], aid))
    elif action == "approve":
        store.decide(aid, "Onaylandı")
        if lid:
            store.add_event(lid, "Taslağı onayladınız", "Panel mesajı göndermez: metni kopyalayıp kendiniz gönderin, sonra 'Gönderdim' deyin")
    elif action == "reject":
        store.decide(aid, "Reddedildi")
        if lid:
            store.update_lead(lid, {"stage": "Taslak hazır"})
            store.add_event(lid, "Taslağı reddettiniz", "")
    elif action == "sent":
        store.decide(aid, "Gönderildi")
        if lid:
            act_lead(lid, "sent", {})
    else:
        return err(404, "yok")
    return 200, {"ok": True}


def act_news(nid, action, body):
    n = store.one("SELECT * FROM news WHERE id=?", (nid,))
    if not n:
        return err(404, "yok")
    if action == "to-opp":
        oid = store.add_opp({"src": n["src"], "sub": "haberden", "url": n["url"] or "news:" + nid, "title": n["title"], "quote": n["title"], "why": n["why"],
                             "move": "Jeff'le konuşup ilk hamleyi belirleyin.", "stars": max(4, n["stars"] or 0), "tags": _tags(n["tags"]),
                             "strength": "Orta", "published_at": n["published_at"]})
        return 200, {"ok": True, "opp": oid or "var"}
    return err(404, "yok")


def login_blocked(ip):
    with _lock:
        t = time.time()
        for k in list(_fails):
            _fails[k] = [x for x in _fails[k] if t - x < LOGIN_WINDOW]
        return len(_fails.get(ip, [])) >= LOGIN_FAILS or sum(len(v) for v in _fails.values()) >= LOGIN_FAILS_ALL


def login_failed(ip):
    with _lock:
        _fails.setdefault(ip, []).append(time.time())


def llm_limited(ip):
    with _lock:
        t = time.time()
        h = [x for x in _hits.get(ip, []) if t - x < 60]
        if len(h) >= 90:
            _hits[ip] = h
            return True
        h.append(t)
        _hits[ip] = h
        return False


# ---------------- auth ----------------
def _secret():
    return hashlib.sha256(("cgos|" + os.environ.get("CGOS_SECRET", PASSWORD)).encode()).digest()


def make_token():
    exp = str(int(time.time()) + 30 * 86400)
    return exp + "." + hmac.new(_secret(), exp.encode(), hashlib.sha256).hexdigest()


def valid_token(tok):
    try:
        exp, sig = tok.split(".", 1)
        return int(exp) > time.time() and hmac.compare_digest(sig, hmac.new(_secret(), exp.encode(), hashlib.sha256).hexdigest())
    except Exception:
        return False


LOGIN = """<!doctype html><html lang="tr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>CybergeneOS</title><style>body{margin:0;min-height:100dvh;display:grid;place-items:center;background:#030508;color:#F2F2F5;font:15px/1.6 Inter,system-ui,sans-serif}
form{width:min(360px,calc(100% - 32px));padding:28px;border:1px solid #ffffff1f;border-radius:22px;background:#0A0D14;display:grid;gap:12px}
h1{margin:0;font:500 22px 'Space Grotesk',system-ui;letter-spacing:-.03em}label{font-size:13px;color:#B4B7C6}
input{min-height:44px;padding:0 14px;border-radius:12px;border:1px solid #ffffff1f;background:#0D1119;color:inherit;font:inherit}
input:focus{outline:2px solid #A2BCE7;outline-offset:2px}button{min-height:44px;border:0;border-radius:7px;background:#e7dff4;color:#171020;font:550 14px inherit;cursor:pointer}
p{margin:0;font-size:13px;color:#F4A3A3}</style><form method="post" action="/login"><h1>CybergeneOS</h1><label for="p">Şifre</label>
<input id="p" name="password" type="password" autocomplete="current-password" autofocus required>{msg}<button>Giriş yap</button></form></html>"""


# ---------------- handler ----------------
class H(BaseHTTPRequestHandler):
    server_version = "CGOS"

    def log_message(self, fmt, *a):
        sys.stderr.write("[cgos] %s\n" % (fmt % a))

    def _jeff(self):
        """Jeff calls from the server with his own token. A browser cannot set this header across sites, so no Origin check is needed for it."""
        tok = self.headers.get("X-CGOS-Token") or ""
        return bool(JEFF_TOKEN) and bool(tok) and hmac.compare_digest(tok.encode(), JEFF_TOKEN.encode())

    def _from_proxy(self):
        return self.client_address[0] in PROXIES

    def _ip(self):
        if self._from_proxy():
            real = (self.headers.get("X-Real-IP") or "").strip()
            if real:
                return real
        return self.client_address[0]

    def _https(self):
        return SECURE_COOKIE or (self._from_proxy() and (self.headers.get("X-Forwarded-Proto") or "").lower() == "https")

    def _host_ok(self):
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
        if host not in ALLOWED:
            return False
        if self.command == "POST" and not self._jeff():
            o = urlparse(self.headers.get("Origin") or "")
            return bool(o.hostname) and o.hostname in ALLOWED
        return True

    def _send(self, code, body=b"", ctype="application/json", extra=None):
        try:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Referrer-Policy", "same-origin")
            self.send_header("X-Robots-Tag", "noindex, nofollow")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode())

    def _authed(self):
        if not PASSWORD:
            return True
        for part in (self.headers.get("Cookie") or "").split(";"):
            k, _, v = part.strip().partition("=")
            if k == "cgos" and valid_token(v):
                return True
        return False

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        if not self._host_ok():
            return self._json(403, {"error": "host"})
        path = urlparse(self.path).path
        if path == "/login":
            return self._send(200, LOGIN.replace("{msg}", "").encode(), "text/html; charset=utf-8")
        jeff_call = self._jeff() and tuple(p for p in path.split("/") if p) in JEFF_GET
        if not (jeff_call or self._authed()):
            return self._send(302, extra={"Location": "/login"}) if not path.startswith("/api/") else self._json(401, {"error": "giris"})
        if path == "/api/state":
            return self._send(200, json.dumps(build_state(), ensure_ascii=False, separators=(",", ":")).encode())
        if path == "/api/jobs":
            return self._json(200, {"jobs": jobs_view(), "lead_source": places.provider()})
        if path == "/api/summary":
            return self._json(200, summary())
        if path == "/api/leads/search-data":
            return self._json(200, {"leads": [{k: l[k] for k in ("id", "note", "address")} for l in store.leads()]})
        if path.startswith("/api/lead/") and path.endswith("/detail"):
            parts = path.split("/")
            if len(parts) != 5 or not parts[3]:
                return self._json(404, {"error": "yok"})
            lead = lead_detail(parts[3])
            return self._json(200, {"lead": lead}) if lead else self._json(404, {"error": "yok"})
        if path.startswith("/api/lead/") and path.endswith("/evidence"):
            lid = path.split("/")[3]
            return self._json(200, {"evidence": [{k: e[k] for k in ("id", "kind", "label", "url", "text", "suspicious", "fetched_at", "expires_at")}
                                                 for e in store.evidence(lid)]})
        if path == "/api/radar/status":
            return self._json(200, radar.status())
        if path == "/api/config":
            return self._json(200, radar.config())
        if path == "/api/status":
            return self._json(200, {"voice": llm.ready(), "voices": sorted(llm.VOICES), "jeff": jeff.mode()})
        if path in ("/", ""):
            return self._send(302, extra={"Location": "/docs/cybergeneos/"})
        rel = path.lstrip("/")
        if rel.startswith("fonts/") or rel == "logo-480.webp":
            rel = "public/" + rel  # the page uses the site's own addresses, so it looks the same on cybergene.co and on Tailscale
        target = (ROOT / rel).resolve()
        if target.is_dir():
            target = target / "index.html"
        base = next((s for s in SERVED if target == s or s in target.parents), None)
        ok = base is not None and target.is_file() and target.suffix in TYPES and not target.name.startswith(".") \
            and not (set(target.relative_to(base).parts[:-1]) & HIDDEN_DIRS) and (".local." not in target.name or target.name == "config.local.js")
        if not ok:
            return self._json(404, {"error": "yok"})
        self._send(200, target.read_bytes(), TYPES[target.suffix])

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = -1
        if n < 0 or n > 40000:
            return self._json(413, {"error": "boyut"})
        raw = self.rfile.read(n) if n else b""  # always read the body first, so a refusal is not cut off by a reset connection
        if not self._host_ok():
            return self._json(403, {"error": "host"})
        if path == "/login":
            ip = self._ip()
            if not PASSWORD:
                return self._send(429, b"", "text/plain")
            if login_blocked(ip):
                sys.stderr.write(f"[cgos] giris kilitli: {ip}\n")
                return self._send(429, LOGIN.replace("{msg}", "<p>Çok fazla yanlış deneme. 15 dakika sonra tekrar deneyin.</p>").encode(), "text/html; charset=utf-8")
            given = (parse_qs(raw.decode("utf-8", "replace")).get("password") or [""])[0]
            if hmac.compare_digest(given.encode(), PASSWORD.encode()):
                cookie = f"cgos={make_token()}; HttpOnly; SameSite=Strict; Path=/; Max-Age={30 * 86400}" + ("; Secure" if self._https() else "")
                return self._send(303, extra={"Location": "/docs/cybergeneos/", "Set-Cookie": cookie})
            login_failed(ip)
            sys.stderr.write(f"[cgos] yanlis sifre: {ip}\n")
            return self._send(401, LOGIN.replace("{msg}", "<p>Şifre yanlış.</p>").encode(), "text/html; charset=utf-8")
        self.by = "bilal"
        if self._jeff() and tuple(p for p in path.split("/") if p) in JEFF_POST:
            self.by = "jeff"
        elif not self._authed():
            return self._json(401, {"error": "giris"})
        try:
            body = json.loads(raw) if raw else {}
            if not isinstance(body, dict):
                raise ValueError
        except ValueError:
            return self._json(400, {"error": "gecersiz"})
        parts = [p for p in path.split("/") if p]
        if parts in (["api", "jeff", "stream"], ["api", "tts", "stream"]):
            return self.stream(parts[1], body)
        try:
            code, out = self.route(parts, body)
        except (RuntimeError, TimeoutError, OSError) as e:
            sys.stderr.write("[cgos] upstream error on %s: %s\n" % (path, type(e).__name__))
            code, out = 502, {"error": "jeff_ulasilamadi"}
        except Exception as e:
            sys.stderr.write("[cgos] error on %s: %s\n" % (path, type(e).__name__))
            code, out = 500, {"error": "hata"}
        if isinstance(out, bytes):
            return self._send(code, out, "audio/wav")
        self._json(code, out)

    def _stream_headers(self, ctype, extra=None):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()

    def stream(self, kind, body):
        """Jeff's words (NDJSON) or his voice (raw PCM), sent as they are produced. The connection closes at the end."""
        if kind == "jeff" and jeff.mode() == "kapali" or kind == "tts" and not llm.ready():
            return self._json(503, {"error": "anahtar_yok"})
        if llm_limited(self._ip()):
            return self._json(429, {"error": "cok_sik"})
        text = str(body.get("text", "")).strip()[:1200 if kind == "jeff" else 700]
        if not text:
            return self._json(400, {"error": "bos"})
        try:
            if kind == "tts":
                gen = llm.speak_stream(text, body.get("voice"))
                first = next(gen)  # fails here, before any header is sent, when no voice model answers
                self._stream_headers("audio/L16", {"X-Sample-Rate": "24000"})
                self.wfile.write(first)
                for chunk in gen:
                    self.wfile.write(chunk)
                    self.wfile.flush()
                return
            self._stream_headers("application/x-ndjson")
            def emit(o):
                self.wfile.write((json.dumps(o, ensure_ascii=False) + "\n").encode())
                self.wfile.flush()
            context = briefing.jeff_context(store)
            started = scan_now(text)
            if started:
                emit({"t": "job", **{k: v for k, v in started.items() if k != "note"}})  # the map moves before Jeff has said a word
                context = started["note"] + "\n\n" + context
            try:
                for piece in jeff.stream_reply(text, context):
                    emit({"t": "d", "x": piece})
                emit({"t": "end"})
            except (BrokenPipeError, ConnectionResetError):
                raise
            except Exception as e:
                sys.stderr.write("[cgos] jeff stream error: %s\n" % type(e).__name__)
                emit({"t": "err", "e": "jeff_ulasilamadi"})
        except (BrokenPipeError, ConnectionResetError):
            self.close_connection = True
            return
        except StopIteration:
            return self._json(502, {"error": "jeff_ulasilamadi"})
        except Exception as e:
            quota = kind == "tts" and "HTTP429" in str(e)
            sys.stderr.write("[cgos] stream error on %s: %s%s\n" % (kind, type(e).__name__, " (kota)" if quota else ""))
            if not self.wfile.closed:
                try:
                    self._json(429 if quota else 502, {"error": "ses_kotasi" if quota else "jeff_ulasilamadi"})
                except (BrokenPipeError, ConnectionResetError):
                    self.close_connection = True

    def route(self, p, body):
        if len(p) < 2 or p[0] != "api":
            return err(404, "yok")
        r = p[1:]
        needs_llm = (r[0] in ("lead",) and len(r) == 3 and r[2] in ("research", "draft")) or r == ["opp", "manual"]
        if needs_llm:
            if not llm.ready():
                return err(503, "anahtar_yok")
            if llm_limited(self._ip()):
                return err(429, "cok_sik")
        if r == ["jeff", "reset"]:
            jeff.reset()
            return 200, {"ok": True}
        if r == ["radar", "run"]:
            jid, e = jobs.start("radar", {}, self.by)
            return 200, {"started": bool(jid), "job": jid, "error": e}
        if r == ["jobs"]:
            jid, e = jobs.start(str(body.get("kind") or "lead_scan"), body, self.by)
            if not jid:
                return err(409 if e == "zaten_calisiyor" else 400, e)
            return 200, {"ok": True, "job": jid, "lead_source": places.provider()}
        if len(r) == 3 and r[0] == "jobs" and r[2] == "cancel":
            return (200, {"ok": True}) if jobs.cancel(r[1]) else err(404, "yok")
        if r == ["config"]:
            cfg = clean_config(body, radar.config())
            store.set_meta("config", cfg)
            return 200, cfg
        if r == ["opp", "manual"]:
            text = str(body.get("text", "")).strip()[:1500]
            if len(text) < 15:
                return err(400, "kisa")
            oid = briefing.manual_opportunity(store, text, str(body.get("url", ""))[:300], geo.canon_city(body.get("city")))
            return (200, {"ok": True, "opp": oid}) if oid else err(409, "var")
        if r == ["lead"]:
            name = str(body.get("name", "")).strip()
            if not name:
                return err(400, "ad")
            lid = store.create_lead({"name": name, "city": geo.canon_city(body.get("city")), "sector": str(body.get("sector", "")), "note": str(body.get("note", ""))[:1500],
                                     "src": "Jeff ekledi" if self.by == "jeff" else "Elle eklenen", "stage": "Yeni"},
                                    "Jeff ekledi" if self.by == "jeff" else "Elle eklendi", str(body.get("origin", ""))[:200])
            extra = {k: str(body[k])[:200] for k in ("phone", "website", "email", "address", "district") if body.get(k)}
            if extra:
                store.update_lead(lid, extra)
            return 200, {"ok": True, "lead": lid}
        if r == ["leads", "review"]:
            ids = [str(i) for i in (body.get("ids") or [])][:500]
            for lid in ids:
                if store.lead(lid):
                    act_lead(lid, "review", {})
            return 200, {"ok": True, "n": len(ids)}
        if len(r) == 3 and r[0] == "opp":
            return act_opp(r[1], r[2], body)
        if len(r) == 3 and r[0] == "lead":
            return act_lead(r[1], r[2], body)
        if len(r) == 3 and r[0] == "approval":
            return act_approval(r[1], r[2], body, actor=self.by)
        if len(r) == 3 and r[0] == "news":
            return act_news(r[1], r[2], body)
        if r == ["idea", "approve"]:
            idea = (store.get_meta("digest") or {}).get("idea", "")
            if not idea:
                return err(400, "bos")
            return 200, {"ok": True, "approval": store.create_approval({"channel": "LinkedIn paylaşımı", "target": "Kendi sayfanız", "text": idea})}
        return err(404, "yok")


def jeff_token():
    """Jeff's own key for the panel API. Kept in the data folder (only the hermes user can read it); Jeff's skill reads the same file."""
    if os.environ.get("CGOS_JEFF_TOKEN"):
        return os.environ["CGOS_JEFF_TOKEN"]
    f = DATA / "jeff-token"
    if not f.exists():
        import secrets
        f.write_text(secrets.token_urlsafe(32))
        try:
            os.chmod(f, 0o600)
        except OSError:
            pass
    return f.read_text().strip()


def main():
    global store, radar, jobs, JEFF_TOKEN
    if HOST not in ("127.0.0.1", "localhost") and not PASSWORD:
        sys.exit("CGOS_PASSWORD olmadan yalnızca 127.0.0.1 üzerinde çalışır.")
    DATA.mkdir(parents=True, exist_ok=True)
    store = Store(DATA / "cgos.db")
    from .approval_adapter import install as install_approval_adapter
    install_approval_adapter(sys.modules[__name__])
    from .jarvis_adapter import install as install_jarvis_adapter
    install_jarvis_adapter(sys.modules[__name__])
    from .live_adapter import install as install_live_adapter
    install_live_adapter(sys.modules[__name__])
    from .opportunity_context import install as install_opportunity_context
    install_opportunity_context(sys.modules[__name__])
    from .panel_correction import install as install_panel_correction
    install_panel_correction(sys.modules[__name__])
    JEFF_TOKEN = jeff_token()
    has = llm.load_key()
    radar = Radar(store)
    jobs = Jobs(store, radar)
    radar.jobs = jobs
    places._usage["store"] = store
    outreach.start_sync(store, also=(contact.shorten_drafts, contact.fix_emails))
    contact.ensure_token()  # the site's mail service reads this file to trust the panel
    if has and os.environ.get("CGOS_RADAR", "1") == "1":
        radar.schedule()
    print(f"CybergeneOS: http://{HOST}:{PORT}/docs/cybergeneos/  (Jeff: {'hazır' if has else 'anahtar yok'}, giriş şifresi: {'var' if PASSWORD else 'yok, yerel'}, radar: {'açık' if has else 'kapalı'})")
    ThreadingHTTPServer((HOST, PORT), H).serve_forever()
