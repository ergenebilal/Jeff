#!/usr/bin/env python3
"""
Jeff V2 — Sabah Brifingi (Spec 009-A)
OpportunityRadar + ReportGenerator + Mission Map + Telegram
Her sabah 08:00'de Bilal'e proaktif rapor gönderir.
"""
import sys, json, os, time, requests
from pathlib import Path
from datetime import datetime, timedelta, timezone

TR_TZ = timezone(timedelta(hours=3))

# === PATHS ===
JEFF_DIR = Path('/opt/hermes/jeff_v2/jeff_v2')
STATE_FILE = Path('/opt/hermes/instagram-pipeline/output/state/post_tracker.json')
TOKEN_PATH = Path(os.path.expanduser('~/.hermes/secrets/ig_bot_token.txt'))
TOKEN = open(TOKEN_PATH).read().strip()
CHAT_ID = "5506784207"
BOT_API = f"https://api.telegram.org/bot{TOKEN}"

sys.path.insert(0, str(JEFF_DIR.parent))

# === TELEGRAM ===
def send_msg(text):
    for attempt in range(3):
        try:
            r = requests.post(f"{BOT_API}/sendMessage",
                data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
                timeout=15)
            if r.json().get("ok"): return True
        except: pass
        time.sleep(1)
    return False

# === MISSION MAP ===
def get_post_status():
    """Bugünkü post sırasını kontrol et."""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            state = json.load(f)
    else:
        state = {"last_post_id": 0, "last_date": "", "total_sent": 0}
    
    last_id = state.get("last_post_id", 0)
    next_id = last_id + 1 if last_id < 12 else 1
    today = datetime.now(TR_TZ).strftime("%Y-%m-%d")
    already_sent = state.get("last_date") == today
    
    themes = {
        1: "AI Farkındalık", 2: "FOMO", 3: "AI Korkusu",
        4: "Erişilebilirlik", 5: "Faydalar", 6: "Acı",
        7: "Saç Ekimi", 8: "Estetik", 9: "Güzellik",
        10: "Diş", 11: "Avukat", 12: "Emlak"
    }
    
    return {
        "last_post_id": last_id,
        "next_post_id": next_id,
        "next_theme": themes.get(next_id, "?"),
        "total_sent": state.get("total_sent", 0),
        "already_sent_today": already_sent,
        "today": today,
    }

def get_lead_status():
    """Lead pipeline durumu."""
    return {
        "total_leads": 40,
        "email_enriched": 0,
        "warm_leads": 0,
        "status": "⚠️ Email zenginleştirme yapılmadı"
    }

# === RADAR SCAN (Jeff V2) ===
def run_radar():
    """Trigger OpportunityRadar scan and return findings."""
    try:
        from jeff_v2.opportunity_radar import OpportunityRadar
        radar = OpportunityRadar()
        findings = radar.scan_now()
        stats = radar.stats()
        return {"findings": findings, "stats": stats}
    except Exception as e:
        return {"findings": [], "stats": {"error": str(e)}}

def run_report():
    """Generate daily brief from ObservationSummary."""
    try:
        from jeff_v2.report_generator import ReportGenerator
        rg = ReportGenerator()
        return rg.daily_brief()
    except Exception as e:
        return f"(Rapor üretilemedi: {e})"

# === PROAKTİF ÖNERİLER ===
def generate_suggestions(post_status, lead_status, radar_raw):
    """DecisionEngine-style proactive suggestions."""
    suggestions = []
    
    # Post pipeline
    ps = post_status
    if ps["already_sent_today"]:
        suggestions.append(f"✅ Bugün post #{ps['last_post_id']} gönderildi, sıradaki: #{ps['next_post_id']} {ps['next_theme']}")
    else:
        suggestions.append(f"🎯 Sıradaki post #{ps['next_post_id']} ({ps['next_theme']}) — henüz gönderilmedi")
    
    # Lead
    if lead_status["email_enriched"] == 0:
        suggestions.append("📡 40 lead bekliyor — email zenginleştirme yapılıp sıcak lead'lere dönüştürülebilir")
    
    # Radar findings
    radar_findings = (radar_raw or {}).get("findings") or []
    for f in radar_findings:
        suggestions.append(f"📡 Radar: {f['detail']}")
    
    # Default suggestions if nothing specific
    if not suggestions:
        suggestions.append("💡 Bugün için önerilen: lead pipeline'ı ilerletmek")
    
    return suggestions


# === MAIN ===
def main():
    print("=" * 60)
    now = datetime.now(TR_TZ)
    print(f"📋 Jeff Sabah Brifingi — {now.strftime('%d.%m.%Y %H:%M')}")
    print("=" * 60)
    
    # 1. Mission Map
    print("\n📍 Mission Map...")
    post_status = get_post_status()
    lead_status = get_lead_status()
    
    # 2. Radar
    print("📡 OpportunityRadar...")
    radar = run_radar()
    
    # 3. Report
    print("📊 ReportGenerator...")
    report = run_report()
    
    # 4. Suggestions
    print("💡 Proaktif öneriler...")
    suggestions = generate_suggestions(post_status, lead_status, radar)
    
    # === BUILD MESSAGE ===
    lines = []
    lines.append(f"☀️ <b>Günaydın Bilal</b> — {now.strftime('%d %B %Y, %A')}")
    lines.append("")
    
    # Durum Özeti
    lines.append("📊 <b>Durum Özeti</b>")
    lines.append(f"  📸 Post #{post_status['next_post_id']} ({post_status['next_theme']}) {'✅ gönderildi' if post_status['already_sent_today'] else '⏳ sıradaki'}")
    lines.append(f"  📡 {lead_status['total_leads']} lead | Email: {'✅' if lead_status['email_enriched'] > 0 else '⚠️ zenginleştirilmedi'}")
    lines.append(f"  📈 Toplam {post_status['total_sent']} post yayında")
    lines.append("")
    
    # Radar
    radar_findings = radar.get("findings") or []
    if radar_findings:
        lines.append("📡 <b>Radar Tespitleri</b>")
        for f in radar_findings:
            icon = "🔴" if f.get("severity") == "critical" else "🟡" if f.get("severity") == "warning" else "🟢"
            lines.append(f"  {icon} {f['detail']}")
        lines.append("")
    
    # Proaktif Öneriler
    lines.append("💡 <b>Bugün İçin Öneriler</b>")
    for s in suggestions[:5]:
        lines.append(f"  {s}")
    lines.append("")
    
    # Haftalık İstatistikler
    lines.append("📊 <b>Haftalık Görünüm</b>")
    days_left = 7 - now.weekday()  # Pazar=6, bugünün günü
    lines.append(f"  🎯 Bu hafta {post_status['total_sent']} post paylaşıldı")
    lines.append(f"  ⏳ Kalan: {max(0, 12 - post_status['total_sent'])} post (sektör serisi)")
    if post_status["already_sent_today"]:
        lines.append(f"  ✅ Bugünkü post (#{post_status['last_post_id']}) tamam")
    lines.append("")
    
    # Otonomi Kararları
    lines.append("🤖 <b>Otonomi Kararları</b>")
    lines.append("  • İçerik üretimi: ✅ Otonom (onay gereksiz)")
    lines.append("  • Lead email: ⚠️ Önce senin onayını bekliyor")
    lines.append("  • Harcama >$10: ❌ Senin onayın gerekli")
    lines.append("")
    
    lines.append("—")
    lines.append(f"<i>Jeff V2 JARVIS • {now.strftime('%H:%M')}</i>")
    
    message = "\n".join(lines)
    
    # Send
    print("\n📤 Sending brief...")
    if send_msg(message):
        print("✅ Brief sent!")
    else:
        print("❌ Send failed!")
    
    print(f"\nMessage length: {len(message)} chars")
    print("=" * 60)


if __name__ == "__main__":
    main()
