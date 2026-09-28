# Kampanya Yönetim Sistemi — Teknik Referans

## Mimari

```
┌─────────────────────────────────────────────────┐
│                Kullanıcı (Browser)              │
│  http://193.164.4.149:8892/campaigns-page       │
└──────────────────┬──────────────────────────────┘
                   │ HTTP
┌──────────────────▼──────────────────────────────┐
│          Jeff Web API (port 8892)               │
│  /opt/hermes/jeff-web-api.py                    │
│  ┌──────────────────────────────────────────┐   │
│  │ do_GET → JSON veya HTML endpoint'leri    │   │
│  │ do_POST → campaign/create, start, vs.    │   │
│  └──────────────────────────────────────────┘   │
└──────┬─────────────────────────────┬────────────┘
       │ import                      │ POST
┌──────▼──────────────┐  ┌──────────▼────────────┐
│  Campaign Manager   │  │  Mail Webhook Server  │
│  campaign_manager.py│  │  mail-webhook-server  │
│  ┌──────────────┐   │  │  .py (port 8877)     │
│  │ Lead Scoring │   │  │  ┌────────────────┐  │
│  │ DeepSeek     │───┼──┼──┤ Brevo SMTP     │  │
│  │ Personalize  │   │  │  │ smtp-relay.    │  │
│  │ Campaign     │   │  │  │ brevo.com:587  │  │
│  │ CRUD         │   │  │  └────────────────┘  │
│  └──────────────┘   │  └──────────────────────┘
└─────────────────────┘
```

## Veri Akışı

### Kampanya Oluşturma (POST /campaign/create)

1. `create_campaign(niche, name)` çağrılır
2. `leads.json`'dan o niche'e ait lead'ler filtrelenir
3. Her lead `score_lead()` ile 0-100 arası skorlanır
4. Skora göre sıralanır (yüksekten düşüğe)
5. Her lead için `analyze_and_generate_email()` çağrılır:
   - DeepSeek API'ye prompt gönderilir (işletme adı, sektör, puan, website, niche ihtiyaçları)
   - Dönen cevap lead'in email_body'si olur
6. Kampanya JSON dosyası `/home/hermes/campaigns/{id}.json`'a yazılır
7. Kampanya index `/home/hermes/campaigns/campaigns.json` güncellenir
8. Phase: "hazir" olarak başlar

### Kampanya Başlatma (POST /campaign/{id}/start)

1. `start_campaign(cid)` çağrılır
2. Phase "gonderiliyor" yapılır
3. Background thread başlatılır (`_send_campaign_emails`)
4. Her lead için sırayla:
   - Status "hazir" mı? → devam, değilse atla
   - Email adresi var mı? → yoksa "email_yok" işareti
   - HTML body oluştur (kişisel mesaj + imza)
   - `POST http://127.0.0.1:8877/send-mail`'e gönder
   - Başarılı → "gonderildi", hata → "hata"
   - Kampanya JSON dosyası her lead'den sonra güncellenir
   - 2 saniye bekle
5. Tüm lead'ler bitince → "tamamlandi"

## Lead Scoring Detayı

```python
def score_lead(lead):
    score = 30  # base
    website = lead.get("website","").strip()
    if not website: score += 30  # no website = high need
    else: score += 15            # has some presence
    
    rating = float(lead.get("rating",0) or 0)
    if rating >= 4.5: score += 15
    elif rating >= 4.0: score += 10
    
    reviews = int(lead.get("reviews",0) or 0)
    if reviews >= 200: score += 10
    elif reviews >= 100: score += 7
    
    niche_bonus = {"klinik":15, "dis":15, "guzellik":12, 
                   "kuafor":10, "avukat":10, "emlak":8,
                   "fitness":8, "kafe":5, "restoran":5}
    score += niche_bonus.get(niche, 5)
    
    return min(score, 100)
```

## Niche AI Opportunity Map

Her niche için önceden tanımlı AI ihtiyaçları ve teklif:

```python
NICHE_OPPORTUNITIES = {
    "guzellik": {
        "ai_gaps": ["randevu takip sistemi", "müşteri sadakat programı"],
        "offer": "AI Randevu Asistanı ile boş randevuları %40 azaltın"
    },
    "klinik": {
        "ai_gaps": ["hasta takip sistemi", "randevu hatırlatma"],
        "offer": "AI Hasta Takip Sistemi ile no-show oranını sıfıra indirin"
    },
    "dis": {
        "ai_gaps": ["randevu hatırlatma", "tedavi planı takibi"],
        "offer": "AI Randevu Otomasyonu ile doluluk oranınızı artırın"
    },
    "avukat": {
        "ai_gaps": ["müvekkil takip sistemi", "dava dosya yönetimi"],
        "offer": "AI Müvekkil Yönetim Sistemi ile dosya takibini otomatikleştirin"
    },
    "emlak": {
        "ai_gaps": ["müşteri takip sistemi", "ilan otomasyonu"],
        "offer": "AI Müşteri Eşleştirme ile satış döngünüzü hızlandırın"
    },
    "kafe/restoran": {
        "ai_gaps": ["müşteri sadakat programı", "sipariş otomasyonu"],
        "offer": "AI Müşteri Sadakat Sistemi ile tekrar ziyaret oranını artırın"
    }
}
```

## DeepSeek Personalization Prompt (Kurumsal Format — 20.06.2026)

```
SYSTEM: Sen bir kurumsal satış danışmanısın. Görevin: bir işletmeyi analiz edip
ona özel, profesyonel bir e-posta taslağı yazmak. E-posta şu formatı takip etmeli:

1. Selamlama — "Sayın [İşletme Adı] yetkilisi,"
2. Kendini tanıtma — "Ben ErgeneAI'den [isim], [sektör] işletmelerine AI çözümleri sunuyorum."
3. Övgü + Sorun tespiti — İşletmenin iyi yönünü takdir et, ardından gözlemlediğin eksikleri belirt
4. Çözüm önerisi — AI Agent sistemimizin bu sorunu nasıl çözeceğini anlat
5. CTA (Call to Action) — Ücretsiz demo teklifi, görüşme talebi
6. Kapanış — Kibar bir kapanış cümlesi

Kurallar:
- Maksimum 200 kelime
- Saygılı ve profesyonel ton
- O işletmenin gerçek durumuna göre kişiselleştir
- Abartma, gerçekçi ol
- İmza ekleme (imza ayrıca eklenecek, sadece mail gövdesi)
- Sadece mail içeriği yaz, başka açıklama ekleme
- Türkçe yaz

USER: Aşağıdaki işletme için kurumsal bir e-posta yaz:

İşletme: {name}
Sektör: {niche}
Google puanı: {rating} / 5 ({reviews} yorum)
Web sitesi: {website veya 'Web sitesi YOK — büyük eksik'}
Tespit edilen dijital eksikler: {ai_gaps}
Ana teklif: {offer}

Bu işletmeye özel, yukarıdaki kurumsal formata uygun bir e-posta yaz.
```

Model: `deepseek-chat`, temperature: 0.7, max_tokens: 500

**NOT:** Bilal 20.06.2026'da düzeltti — mail "kitabın ortasından başlar gibi" olmamalı, kurumsal formatta olmalı (selamlama→tanışma→övgü+sorun→çözüm→CTA→kapanış).

## Kampanya JSON Yapısı

```json
{
  "id": "camp-1781983134-0",
  "name": "Kafeler - AI Tanıtım",
  "niche": "kafe",
  "created_at": "2026-06-20T22:19:59",
  "phase": "hazir|gonderiliyor|tamamlandi|durduruldu",
  "total_leads": 15,
  "sent_count": 0,
  "emails": [
    {
      "lead_id": "lead-xxx",
      "lead_name": "İşletme Adı",
      "score": 90,
      "score_label": "🔥 Sıcak",
      "email": "info@ornek.com",
      "website": "ornek.com",
      "phone": "+90...",
      "niche": "kafe",
      "email_body": "Kişiselleştirilmiş mail içeriği...",
      "status": "hazir|gonderildi|hata|email_yok",
      "sent_at": null
    }
  ]
}
```

## Debugging

### Kampanya oluşmuyor
- `leads.json`'da o niche'te lead var mı? → `GET /leads/scored?niche=guzellik`
- DeepSeek API key çalışıyor mu? → Doğrudan curl testi
- Campaigns dizini var mı? → `mkdir -p /home/hermes/campaigns`

### Mail gitmiyor
- Mail webhook server çalışıyor mu? → `curl -X POST http://127.0.0.1:8877/send-mail -H "Content-Type: application/json" -d '{"toEmail":"test@test.com","subject":"test","body":"test"}'` 
- Lead'de email alanı var mı? → `leads.json` kontrol et
- Brevo SMTP kredileri bitmiş mi? → Brevo dashboard

### Hata durumları
- `email_yok` → Lead'in email alanı boş veya geçersiz (sentry/wix/png adresleri filtrelenir)
- `hata` → Webhook sunucusu dönmedi veya SMTP hatası. Log: `journalctl -u mail-webhook -n 20`

## UI — Mail İçeriği Görüntüleme (Modal Pattern)

Kampanya detay sayfasında her lead için **Mail İçeriği** sütunu → **"👁 Görüntüle"** butonu → Bootstrap modal.

### Backend (Python http.server)

```python
# _campaign_detail_html içinde:
email_data_dict = {}
for e in campaign.get("emails", []):
    email_data_dict[e["lead_id"]] = {
        "name": e.get("lead_name", ""),
        "body": e.get("email_body", "")
    }
emails_json = json.dumps(email_data_dict, ensure_ascii=False)

# HTML template'de:
html = f'''<script>const EMAILS = {emails_json};</script>'''
```

### Frontend (JS + Bootstrap Modal)

```html
<!-- Modal HTML -->
<div class="modal fade" id="emailModal" tabindex="-1">
  <div class="modal-dialog modal-lg modal-dialog-scrollable">
    <div class="modal-content">
      <div class="modal-header">
        <h5 class="modal-title" id="emailModalTitle">Mail İçeriği</h5>
        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
      </div>
      <div class="modal-body" id="emailModalBody"
           style="white-space:pre-wrap;font-family:system-ui;font-size:14px;line-height:1.6;">
      </div>
      <div class="modal-footer">
        <button class="btn btn-secondary" data-bs-dismiss="modal">Kapat</button>
      </div>
    </div>
  </div>
</div>
```

```javascript
// Buton: <button class="btn btn-sm btn-outline-success" onclick="showEmail('{lead_id}')">👁 Görüntüle</button>

function showEmail(leadId) {
    const data = EMAILS[leadId];
    if (!data) return;
    document.getElementById('emailModalTitle').textContent = '📧 ' + data.name;
    document.getElementById('emailModalBody').textContent = data.body;
    new bootstrap.Modal(document.getElementById('emailModal')).show();
}
```

### Teknik Pitfall'lar

1. **F-string + brace nesting hatası:** `{ {{', '.join(data)}} }` → Python set literal olarak yorumlanır, `TypeError: unhashable type: 'set'`. Çözüm: `json.dumps()` kullan.
2. **Bootstrap JS eksik:** Modal çalışmaz. Kontrol: `typeof bootstrap === 'undefined'`. Sayfada `<script src="...bootstrap.bundle.min.js">` olduğundan emin ol.
3. **Modal body'de HTML escape:** `textContent = data.body` kullan (`innerHTML` değil) — DeepSeek'ten gelen metinlerde HTML special char'lar olabilir.
4. **Büyük JSON boyutu:** 15 lead için sorun yok, 200+ lead için sayfa yavaşlayabilir. Lazy loading düşün.

## Genişletme Notları

- Email'dan sonra SMS bildirimi eklemek için: aynı pattern, farklı webhook
- Lead'lere email bulma: email-scraper.py (websitesi tarama) veya manuel (Bilal'in takip formu)
- Kampanya raporlama: her lead'de "açıldı mı" takibi için tracking pixel gerek (şimdilik yok)
- DeepSeek olmayan ortamda fallback template kullanılır (daha az kişisel ama çalışır)
- Büyük kampanyalar için email verilerini lazy load (API'den çek, sayfaya gömme)
