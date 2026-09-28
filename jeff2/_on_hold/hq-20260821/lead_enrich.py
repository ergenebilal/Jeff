import json

# Mevcut lead'leri oku
leads = []
with open("/home/hermes/jeff2/hq/lead_pipeline_1.jsonl") as f:
    for line in f:
        leads.append(json.loads(line.strip()))

# Email enrichment mapping
enrichment_map = {
    "Nework Smart Working Cafe": "info@neworkcafe.com",
    "Mudanya Petshop": "info@mudanyapetshop.com.tr",
}

# Güncelle
updated = 0
for lead in leads:
    if lead["company"] in enrichment_map:
        lead["email"] = enrichment_map[lead["company"]]
        lead["enriched_at"] = "2026-07-10"
        updated += 1

# Tekrar yaz
with open("/home/hermes/jeff2/hq/lead_pipeline_1.jsonl", "w") as f:
    for lead in leads:
        f.write(json.dumps(lead, ensure_ascii=False) + "\n")

print(f"✅ CRM güncellendi: {updated} lead enrichment yapıldı")
print(f"\n📊 CRM ÖZETİ:")
print(f"   Toplam lead: {len(leads)}")
print(f"   Email var: {sum(1 for l in leads if l['email'])}")
print(f"   Telefon var: {sum(1 for l in leads if l['phone'])}")
print(f"   İletişim yok: {sum(1 for l in leads if not l['email'] and not l['phone'])}")
print(f"\n🔴 CRITICAL enrichment durumu:")
for l in leads:
    if l['priority'] == 'CRITICAL':
        email = l.get('email', '—') or '—'
        phone = l.get('phone', '—') or '—'
        print(f"   {l['company']}: email={email} | tel={phone}")
