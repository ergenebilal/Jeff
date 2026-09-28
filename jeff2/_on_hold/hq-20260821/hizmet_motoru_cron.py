# Hizmet Motoru — Cron için lead enrichment + outreach hazırlık scripti
# Her hafta Pazartesi 11:00'de çalışır
# CRITICAL lead'lere öncelik verir

import json, os

leads_file = "/home/hermes/jeff2/hq/lead_pipeline_1.jsonl"
feed_file = "/home/hermes/jeff2/hq/feed.jsonl"

leads = []
if os.path.exists(leads_file):
    with open(leads_file) as f:
        for line in f:
            if line.strip():
                leads.append(json.loads(line.strip()))

critical = [l for l in leads if l.get('priority') == 'CRITICAL']
high = [l for l in leads if l.get('priority') == 'HIGH']

# Özet
total_leads = len(leads)
emailsiz = sum(1 for l in leads if not l.get('email'))
tel_var = sum(1 for l in leads if l.get('phone'))
kanal_var = sum(1 for l in leads if l.get('phone') or l.get('email'))
kanalsiz = sum(1 for l in leads if not l.get('phone') and not l.get('email'))

outreach_ready = sum(1 for l in leads if l.get('email'))

print(f"📊 HİZMET MOTORU RAPORU — {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}")
print(f"{'='*50}")
print(f"Pipeline: {total_leads} lead")
print(f"  🔴 Kritik: {len(critical)}")
print(f"  🟡 Yüksek: {len(high)}")
print(f"  🟢 Orta/Düşük: {total_leads - len(critical) - len(high)}")
print()
print(f"İletişim Kanalı:")
print(f"  📧 Email var: {total_leads - emailsiz}")
print(f"  📞 Telefon var: {tel_var}")
print(f"  ✅ En az 1 kanal: {kanal_var}")
print(f"  ❌ Hiç kanal yok: {kanalsiz}")
print()
print(f"Outreach'e hazır (emaili olan): {outreach_ready} lead")
print()
if critical:
    print("🔴 EN KRİTİK LEAD'LER (bu hafta öncelik):")
    for l in critical:
        kanal = l.get('email') or l.get('phone') or '❌ KANAL YOK'
        print(f"  • {l['company']} → {kanal}")
