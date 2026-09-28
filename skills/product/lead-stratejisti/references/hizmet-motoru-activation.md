# Hizmet Motoru Aktivasyonu — Outbound Altyapı Kurulumu

Bu, CRM'deki lead'leri active outbound pipeline'a dönüştürmek için gereken adımları içerir.
`lead-stratejisti` (lead bulma → CRM) ile `kampanya-yonetimi` (campaign → email) arasındaki köprü.

## Aktivasyon Sırası

### 1. Mevcut Durumu Gör
```
get_sales_pipeline               → kaç lead, hangi stage, email/website coverage
list_sequences                   → mevcut sequence template'leri
autoreach_status                 → AutoReach açık mı?
outbound_provider_status         → Resend/Instantly/Gmail bağlı mı?
list_enrichment_sources_status   → Hunter/Apollo/Clearbit API key var mı?
```

### 2. Sequence'leri Kur/Hazırla
```python
# Varsayılan sequence'leri oluştur (generic, dental, restaurant, law-firm)
seed_default_sequences()

# Niche-specific sequence'ler
create_sequence(name="Saç Ekimi — 3 Adım TR", description="...",
  steps=[{order:1, delayDays:0, subject:"...", bodyTemplate:"..."}, ...])
create_sequence(name="Otel — 3 Adım TR", steps=[...])
```

### 3. Workflow'ları Kur
```python
install_workflow_template(templateId="auto-qualify-on-import")  # yeni lead otomatik ICP skorla
install_workflow_template(templateId="reply-received-triage")   # cevap gelince sınıflandır
```

### 4. Lead'leri Zenginleştir (Email/Instagram Bul)
```python
# Gemini ücretsiz (light) — Instagram, sektör, çalışan sayısı bulur
enrich_lead(leadId="...", mode="light")

# Waterfall enrichment (premium) — email bulma
enrich_lead_waterfall(leadId="...", desiredFields=["email"])
```

### 5. AutoReach'i Aktive Et
```python
enable_autoreach()
# → Resend/Instantly/Gmail bağlı değilse "no_outbound_provider" hatası verir
# Önce provider'ı kur, sonra tekrar dene
```

### 6. Performansı İzle
```python
get_next_best_action()           # sıradaki en iyi aksiyon
get_email_stats()                # sent/opened/replied/bounced
get_sequence_stats(sequenceId)    # per-sequence performans
```

## Kritik Bağımlılıklar

| Bileşen | API Key Gerekli mi? | Ücretsiz? |
|---------|---------------------|-----------|
| Pipeline analizi | Hayır | ✅ |
| Sequence oluşturma | Hayır | ✅ |
| Workflow kurulumu | Hayır | ✅ |
| Light enrichment (Gemini) | Hayır (AgencyOS Gemini key) | ✅ |
| Email enrichment (Hunter/Apollo/Clearbit) | Evet — Vault'a ekle | Hayır — $ |
| Email gönderme (Resend/Instantly) | Evet — Vault'a ekle | Kısmen (Resend: 3K/ay ücretsiz) |

## Engeller ve Çözümleri

| Engellenen | Mesaj | Çözüm |
|-----------|-------|-------|
| `no_outbound_provider` | Resend/Instantly/Gmail bağlı değil | Settings → Vault → RESEND_API_KEY ekle |
| `premium_required` | Waterfall enrichment premium plan | Light enrichment (Gemini, ücretsiz) kullan |
| AutoReach kapalı | `enabled: false` | Provider bağlanınca `enable_autoreach()` çağır |

Bu doküman 07.07.2026 Jeff 2.0 kurulum session'ında oluşturuldu. Test edilen lead sayısı: 40 (5 email, 4 Contacted).
