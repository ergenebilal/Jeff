# SOP: Lead Enrichment Pipeline v2
**Oluşturan:** Jeff (Patronus)
**Tarih:** 2026-07-09 (v2)
**Geçerlilik:** 2026-10-07 (+90 gün)
**Durum:** ✅ Patronus onaylı

## Amaç
Lead bulma sonrası email adreslerinin zorunlu olarak tamamlanmasını sağlamak. emailsiz lead oranını %77'den %20 altına düşürmek. Her enrichment denemesi loglanır ve maliyeti kaydedilir.

## Adımlar

### Aşama 1 — Lead Alındığı Anda (Hırslı)
1. Lead kaydedildikten sonra `email` alanını kontrol et
2. Email varsa → Aşama 3'e geç
3. Email yoksa → Aşama 2'ye geç

### Aşama 2 — Email Tamamlama (Hırslı + Pragmatik)
**Üç durumlu kural (SOP Uyum Spec'e göre):**

**A) ZORUNLU TARAMA** — Şu durumlarda website taranır, email bulunur veya bulunamaz:
- Lead'de hiçbir iletişim bilgisi yoksa (email yok, telefon yok, WhatsApp yok)
- Lead sektörü dijital varlığı yüksek bir sektörse (yazılım, SaaS, e-ticaret, kurumsal hizmet)
- Lead'in websitesi biliniyorsa ve çalışıyorsa (404 değilse)

**B) KOŞULLU TARAMA** — Şu durumlarda önce telefon/WhatsApp kontrol edilir, taranmazsa sorun değil:
- Lead'de telefon numarası varsa
- Lead sektörü dijital varlığı düşük bir sektörse (otel, saç ekimi, yerel esnaf, inşaat)
- Lead'in websitesi yoksa veya 404/seo'suz bir sayfaysa

**C) ATLANABİLİR TARAMA** — Şu durumlarda direkt WhatsApp/telefon kanalına geçilir:
- Lead'de hem telefon hem de WhatsApp varsa
- Lead daha önce enriched edilmişse ve tekrar deneniyorsa
- Lead "iletişime geçilmiş" statüsündeyse ve takip mesajı atılıyorsa

**Kritik kural:** Hiçbir kanalı olmayan lead (ne email, ne telefon, ne WhatsApp) ASLA atlanamaz. Bu lead'ler ZORUNLU TARAMA'ya girer.

**Tarama adımları (A ve B durumlarında):**
1. Lead'in website'ini tara (web_extract veya Crawl4AI)
   - "iletişim", "contact", "bize ulaşın" sayfalarını kontrol et
   - `mailto:` linklerini yakala
   - `info@`, `contact@`, `rezervasyon@` gibi pattern'leri tara
2. Bulunamazsa → Google'da site search yap: `site:[domain] email`
3. Bulunamazsa → lead'i "emailsiz" etiketiyle işaretle, haftalık toplu işleme havuzuna ekle
4. Bulunduysa → CRM'e işle (update_lead)

**Her deneme sonrası log hazırlanır (bkz. Enrichment Log Standardı).**

### Aşama 3 — Email Doğrulama (Pragmatik)
1. Email formatını kontrol et (`@` + domain varlığı)
2. Geçersizse → Aşama 2'ye geri dön
3. Geçerliyse → lead "outreach hazır" statüsüne geçer

### Aşama 4 — Takip (Hırslı)
1. Haftalık emailsiz lead raporu hazırla
2. 7 gün+ emailsiz kalan lead'leri Patronus'a bildir
3. 14 gün+ emailsiz kalan lead'leri arşivle

## Enrichment Log Standardı

Her enrichment denemesinde şu alanlar feed.jsonl'ye yazılır:

| Alan | Zorunlu | Açıklama |
|:-----|:--------|:---------|
| `provider` | ✅ | Kullanılan yöntem (web_extract, manual, hunter_api, apollo_api) |
| `lead_id` | ✅ | Lead ID |
| `attempt` | ✅ | Bu lead için kaçıncı deneme |
| `result` | ✅ | found / not_found / skipped |
| `email` | ✅ | Bulunan email (yoksa `-`) |
| `cost` | ✅ | Tahmini maliyet $ cinsinden |
| `channel` | ✅ | Enrichment sonrası kullanılacak kanal (email / whatsapp / phone / none) |

**Format (tek satır, feed.jsonl'ye):**
```
ENRICHMENT_LOG | lead-xxx | provider=web_extract | attempt=1 | result=founded | email=info@site.com | cost=0.00 | next_channel=email
```

**Kural:** Başarılı deneme de loglanır, başarısız da. Atlanan deneme de loglanır (result=skipped). Loglanmayan enrichment yoktur.

## Kontrol Listesi
- [ ] Yeni lead alındığında email kontrolü yapıldı
- [ ] Emailsiz lead için website tarandı (A/B/C kuralına göre)
- [ ] Enrichment log'u feed.jsonl'ye yazıldı
- [ ] Bulunan email CRM'e işlendi
- [ ] Email formatı doğrulandı
- [ ] Haftalık emailsiz lead raporu hazırlandı

## Hata Durumları
- **Website erişilemez (404)** → lead'i "emailsiz-ulaşılamaz" etiketiyle işaretle, 30 gün sonra tekrar dene. Log: `result=not_found, provider=web_extract`
- **Mailto linki bozuk** → domain'in genel contact formu varsa orayı dene, yoksa "emailsiz" etiketi
- **Email doğrulama geçersiz** → "doğrulanamadı" etiketi, manuel kontrole bırak
- **Website'de iletişim sayfası yok** → Google Maps'ten telefon numarası varsa WhatsApp outreach'e yönlendir. Log: `result=not_found, next_channel=whatsapp`

## İlgili Kaynaklar
- CRM: AgencyOS MCP (`update_lead`, `prime_lead_pitch`)
- Web tarama: web_extract, Crawl4AI MCP
- Email discovery skill: `/home/hermes/.hermes/skills/` (varsa)
- Mevcut emailsiz lead raporu: `/home/hermes/jeff2/reports/email_discovery_results.md`
- Cross-control denetim: SPEC_SOP_UYUM_COST_LOGGING.md
- Maliyet okuma: Maliyetçi haftalık brifing kontrolü

## Versiyon Geçmişi
| Tarih | Değişiklik | Yapan |
|:-----|:-----------|:------|
| 2026-07-09 | İlk sürüm | Bilge (🧠) → Patronus onayı |
| 2026-07-09 | v2: A/B/C kuralı + Enrichment Log Standardı eklendi | Jeff (Patronus) |
