#!/usr/bin/env python3
"""ErgeneAI Günlük Bülten v3 — Türkçe kaynaklar + GitHub analiz + Telegram bildirimi."""
import json, smtplib, urllib.request, ssl, xml.etree.ElementTree as ET
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

EMAIL = "ergenebilal@gmail.com"
APP_PW = "quuu xaow rcvg lzsb"
SMTP_HOST, SMTP_PORT = "smtp.gmail.com", 587
TG_TOKEN = "8018339374:AAEvZ5Smdj7FOV1EW3ciTFrZ0992N495FLM"
TG_CHAT = "5506784207"

def fetch_url(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode("utf-8")

# ── Repo Analiz Motoru (deterministik) ──────────
def analyze_repo(repo):
    """Reponun ErgeneAI işine nasıl yarayacağını keyword eşleştirmeyle analiz et."""
    text = f"{repo['name']} {repo['description'] or ''} {' '.join(repo.get('topics', []))}".lower()
    matches = []

    rules = [
        (["agent", "chatbot", "assistant", "conversational", "dialog"], 
         "Instagram DM asistanına entegre edilerek müşteri karşılama kapasitesini artırabilir"),
        (["workflow", "automation", "orchestrat", "pipeline", "n8n"],
         "n8n workflow pipeline'larına bağlanarak otomasyon gücünü yükseltebilir"),
        (["api", "integration", "connector", "webhook", "gateway"],
         "Harici servis entegrasyonlarında ara katman olarak kullanılabilir"),
        (["docker", "container", "kubernetes", "deploy", "vps", "server"],
         "VPS altyapı yönetimini ve deployment süreçlerini optimize eder"),
        (["llm", "gpt", "language model", "transformer", "fine-tun", "rag"],
         "Mevcut AI modellerin yeteneklerini genişletir, özel LLM çözümleri sunar"),
        (["image", "generat", "diffusion", "stable", "visual", "media"],
         "Instagram görsel içerik üretim otomasyonunda kullanılabilir"),
        (["data", "analytics", "monitor", "track", "metric", "dashboard"],
         "Müşteri verilerini analiz ederek iş zekası katmanı oluşturur"),
        (["voice", "speech", "audio", "transcri", "tts", "stt"],
         "Sesli müşteri hizmetleri veya toplantı transkripsiyonu için kullanılabilir"),
    ]

    for keywords, explanation in rules:
        if any(kw in text for kw in keywords):
            matches.append(explanation)

    if not matches:
        lang = repo.get('language', '')
        if lang in ('Python', 'TypeScript', 'JavaScript'):
            matches.append(f"{lang} tabanlı — mevcut stack'e kolay entegre edilebilir")
        else:
            matches.append("Genel AI/otomasyon altyapısına katkı sağlayabilir")

    return " • ".join(matches[:2])  # max 2 sebep

# ── Türkçe Haber Kaynakları ─────────────────────
news_items = []

for query, label in [
    ("yapay+zeka+yapay+zek%C3%A2", "AI"),
    ("teknoloji+otomasyon+yapay+zeka", "Teknoloji"),
]:
    try:
        xml = fetch_url(f"https://news.google.com/rss/search?q={query}&hl=tr&gl=TR&ceid=TR:tr")
        root = ET.fromstring(xml)
        for item in root.findall(".//item")[:8]:
            title = item.find("title")
            link = item.find("link")
            source = item.find("source")
            news_items.append({
                "title": (title.text or "").strip(),
                "url": (link.text or "").strip(),
                "source": (source.text or "Google News").strip(),
            })
    except Exception as e:
        print(f"⚠️ Google News {label}: {e}")

# Donanım Haber
try:
    xml = fetch_url("https://www.donanimhaber.com/rss/tum/")
    root = ET.fromstring(xml)
    for item in root.findall(".//item")[:5]:
        title = item.find("title")
        link = item.find("link")
        news_items.append({
            "title": (title.text or "").strip(),
            "url": (link.text or "").strip(),
            "source": "Donanım Haber",
        })
except Exception as e:
    print(f"⚠️ Donanım Haber: {e}")

# Tekille
seen = set()
unique_news = []
for n in news_items:
    key = n["title"][:60]
    if key not in seen:
        seen.add(key)
        unique_news.append(n)
        if len(unique_news) >= 6:
            break

# ── GitHub Trending ─────────────────────────────
repo_items = []
try:
    data = json.loads(fetch_url(
        "https://api.github.com/search/repositories?q=AI+agent+automation+LLM&sort=stars&order=desc&per_page=5",
        {"Accept": "application/vnd.github.v3+json", "User-Agent": "ErgeneAI/1.0"},
    ))
    for repo in data.get("items", []):
        r = {
            "name": repo.get("full_name", ""),
            "url": repo.get("html_url", ""),
            "description": repo.get("description") or "Açıklama yok",
            "stars": repo.get("stargazers_count", 0),
            "language": repo.get("language"),
            "topics": repo.get("topics", [])[:3],
        }
        r["why"] = analyze_repo(r)
        repo_items.append(r)
except Exception as e:
    print(f"⚠️ GitHub: {e}")

# ── HTML ────────────────────────────────────────
tarih = datetime.now().strftime("%d %B %Y, %A")

html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="background:#000;margin:0;padding:20px;font-family:-apple-system,BlinkMacSystemFont,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;margin:0 auto;">

<tr><td style="padding:28px 20px;text-align:center;">
  <h1 style="margin:0;font-size:20px;color:#fff;">ErgeneAI Günlük Bülten</h1>
  <p style="margin:6px 0 0;color:#666;font-size:12px;">{tarih}</p>
</td></tr>

<tr><td style="padding:0 0 8px;border-bottom:1px solid #39FF14;">
  <h2 style="margin:0;font-size:15px;color:#39FF14;">📰 Gündem</h2>
</td></tr>"""

for n in unique_news:
    html += f"""
<tr><td style="padding:12px;background:#111;border-radius:8px;">
  <span style="font-size:10px;color:#39FF14;background:#0a0a0a;padding:1px 8px;border-radius:8px;">{n['source']}</span>
  <h3 style="margin:6px 0 4px;font-size:14px;color:#fff;">{n['title']}</h3>
  <a href="{n['url']}" style="color:#39FF14;text-decoration:none;font-size:11px;">Habere Git →</a>
</td></tr>"""

html += """
<tr><td style="padding:20px 0 8px;border-bottom:1px solid #39FF14;">
  <h2 style="margin:0;font-size:15px;color:#39FF14;">🔧 Repo Önerileri</h2>
</td></tr>"""

for r in repo_items:
    lang = f"<span style='background:#1a1a1a;padding:1px 8px;border-radius:10px;font-size:10px;color:#999;'>{r['language']}</span>" if r['language'] else ""
    topics = " ".join(f"<span style='background:#1a1a1a;padding:1px 6px;border-radius:8px;font-size:9px;color:#666;margin:0 1px;'>{t}</span>" for t in r['topics'])
    html += f"""
<tr><td style="padding:12px;background:#0a0a0a;border-left:3px solid #39FF14;border-radius:0 8px 8px 0;">
  <h3 style="margin:0 0 4px;font-size:14px;color:#fff;">{r['name']} <span style="background:#39FF14;color:#000;padding:1px 8px;border-radius:10px;font-size:10px;">⭐ {r['stars']}</span> {lang}</h3>
  <p style="margin:0 0 4px;color:#888;font-size:12px;line-height:1.4;">{r['description'][:200]}</p>
  <p style="margin:0 0 6px;color:#39FF14;font-size:11px;">💡 {r['why']}</p>
  {topics}<br>
  <a href="{r['url']}" style="color:#39FF14;text-decoration:none;font-size:11px;">GitHub →</a>
</td></tr>"""

html += f"""
<tr><td style="padding:24px 0 0;text-align:center;">
  <hr style="border:none;border-top:1px solid #222;">
  <p style="color:#444;font-size:10px;">ErgeneAI Otomasyon • Günlük Bülten • {datetime.now().strftime('%d.%m.%Y')}</p>
</td></tr>
</table></body></html>"""

# ── Email Gönder ────────────────────────────────
msg = MIMEMultipart("alternative")
msg["From"] = EMAIL
msg["To"] = EMAIL
msg["Subject"] = f"ErgeneAI Günlük Bülten — {datetime.now().strftime('%d.%m.%Y')}"
msg.attach(MIMEText(html, "html", "utf-8"))

ctx = ssl.create_default_context()
with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as s:
    s.starttls(context=ctx)
    s.login(EMAIL, APP_PW)
    s.sendmail(EMAIL, [EMAIL], msg.as_string())

# ── Telegram Bildirimi ──────────────────────────
tg_text = f"📰 *ErgeneAI Günlük Bülten*\n_{tarih}_\n\n"
tg_text += f"🔹 *{len(unique_news)} haber* • *{len(repo_items)} repo* incelendi\n"
tg_text += f"📧 Detaylı bülten mailinde\n\n"

if repo_items:
    tg_text += "*Öne Çıkan Repolar:*\n"
    for r in repo_items[:3]:
        tg_text += f"• `{r['name']}` ⭐{r['stars']}\n  _{r['why'][:100]}_\n"

try:
    tg_url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": TG_CHAT, "text": tg_text, "parse_mode": "Markdown"}).encode()
    req = urllib.request.Request(tg_url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        resp = json.loads(r.read())
    if resp.get("ok"):
        print("✅ Telegram bildirimi gönderildi")
    else:
        print(f"⚠️ Telegram hatası: {resp}")
except Exception as e:
    print(f"⚠️ Telegram: {e}")

print(f"✅ Bülten: {len(unique_news)} haber, {len(repo_items)} repo — {datetime.now().strftime('%H:%M')}")
