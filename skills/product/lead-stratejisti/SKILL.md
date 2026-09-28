---
name: lead-stratejisti
version: 5.0.0
author: Jeff
description: Otomatik lead bulma (Google Places API + Apify Lead Gen) → web sitesi analizi → ihtiyaç çıkarma → DeepSeek ile kişisel mesaj üretme → CRM'e kaydetme pipeline. Tam otomatik, insan müdahalesiz.
---

# 🎯 Lead Stratejisti — Analiz → PDF → E-posta Pipeline

> Müşteriye gitmeden önce her şey hazır: grafikli PDF sunum, e-posta taslağı, mobil demo sayfası.

## Felsefe (Bu Skill'in Kullanım Kılavuzu)

- Her lead için **tek tıkla** PDF sunum + e-posta + mobil demo üretilir.
- PDF'de **acı noktası** ilk sayfada, grafikle desteklenir.
- Uzun cümleler yok. Görsel anlatım var.
- Müşteri ne alacağını 10 saniyede anlamalı.
- Bilal sadece "gönder" der. Gerisini ben hallederim.

## Lead Analiz Akışı

### 1. Lead Gelir → JSON'a Eklenir
Lead, `~/lead_listesi_hepsi.json` dosyasına eklenir. Minimum alanlar: isim, puan, adres, telefon, website, kategori, durum.

### 2. Otomatik Sınıflandırma (lead-stratejisti.py)

| Klasman | Skor | Kanal | Aksiyon |
|---------|------|-------|---------|
| 🔴 SICAK | ≥8/10 | Yüz yüze | Hemen git, demo göster |
| 🟡 ILIK | 6-7/10 | Telefon/e-posta | Ön görüşme + PDF gönder |
| 🔵 SOĞUK | <6 | Referansla | Case study birikince |

#### Puanlama Tablosu
- Web yok: +3, Sadece IG: +2
- Yorum >200: +2, >100: +1
- Mudanya'da: +2, Bursa içi: +1
- Telefon var: +1
- "web yok" notu: +2

### 3. Eksik Tespiti

Eksikler 3 grupta toplanır:

| Web Durumu | Kaçırılan Müşteri | Kayıp Oranı |
|------------|------------------|-------------|
| Yok | 35% potansiyel müşteri rakibe gider | Yüksek |
| Sadece IG | 30% kurumsal güven kaybı | Orta |
| Var ama randevu yok | 20% mobil ziyaretçi kaçar | Düşük |

#### Evrensel Eksikler (her lead'de olur)
- ❌ WhatsApp işletme botu yok (7/24 cevapsız mesajlar)
- ❌ Müşteri takip sistemi yok (randevu sonrası kayıp)

## PDF Sunum Pipeline — Playwright ile Premium PDF

> ⚠️ **ÖNEMLİ**: WeasyPrint kullanma — çirkin PDF üretir (26KB, düz CSS, kötü font). Playwright kullan (~250-270KB, Plus Jakarta Sans font, gradient, shadow, border-radius, full-bleed cover, print_background=True).

### PDF'de KAZANÇ KAYBI GÖSTERİMİ (Kritik Kural)

Bilal'in net talimatı: **Kazanç kaybı sadece yüzde olarak gösterilir. Asla ₺ tutarı yazma.**

| ❌ Yanlış | ✅ Doğru |
|-----------|----------|
| Aylık ~₺1.400 kayıp | Dijital varlık skoru %15 → %92 |
| Her ay ₺340 kaybediyorsunuz | Potansiyel müşterilerin %35i rakibe gidiyor |
| Size maliyeti ₺X | Eksiklerin toplam etkisi %65 kayıp |

Bar chart'ta: Mevcut %15 vs Çözüm %92 — başka sayı yok. ₺ sembolü geçmez.

### PDF Premium Tasarim (v2.1, 16.06.2026) — Mevcut

Script: `/opt/hermes/scripts/pdf-playwright.py`

**Renk Paleti:**
- Kapak arka plan: koyu yeşil gradient `#022c22 → #064e3b → #065f46 → #0d9488`
- Kapak overlay: radial gradient + pattern dots (opacity .04)
- Vurgu: altın sarısı `#d4a853` / `#fbbf24` (kapak başlık highlight, divider, offer border, gap badge)
- Metin: slate `#1e293b`, ikincil `#64748b`
- Durum renkleri: kırmızı `#dc2626` (kritik), turuncu `#ea580c` (orta), sarı `#ca8a04` (düşük)
- Skor kartı mevcut: kırmızı gradient `#fef2f2 → #fff5f5`, 1px `#fecaca` border
- Skor kartı çözüm: yeşil gradient `#f0fdf4 → #ecfdf5`, 1px `#a7f3d0` border
- Çözüm arka planı: `#f9fffb` + `#d1fae5` border

**Font:** Plus Jakarta Sans (başlıklar 800, 48px kapak), Inter (gövde 400-600, 11-13px) — Google Fonts `@import`

**Sayfa Düzeni (2 sayfa, A4):**

**Sayfa 1 — Kapak (full-bleed 794×1123px):**
- Koyu yeşil gradient + radial overlay + nokta pattern (`background-image: radial-gradient`)
- Badge: "Dijital Dönüşüm Raporu" — `rgba(255,255,255,.08)` arka plan, `backdrop-filter: blur(8px)`, `1px rgba(255,255,255,.12)` border, border-radius 100px
- İşletme adı: 48px/800, altın gradient highlight (`linear-gradient(135deg,#fbbf24,#d4a853)`, `-webkit-background-clip:text`)
- Kategori ikonu: işletme türüne göre (🏥 klinik, 💆 güzellik, 💇 saç ekimi, 🍽️ restoran, 🏢 büro, 🏪 diğer)
- Meta satırları: SVG ikon (map-pin, phone, calendar, star) + adres/telefon/tarih/skor
- Divider: 48px genişlik, 2px, gradient altın→transparent
- Footer: ErgeneAI brand + "Gizli ve Kişiye Özeldir"

**Sayfa 2 — Analiz:**
- **Skor Kartları** — yan yana 2 kart (grid 1fr 1fr, gap 12px):
  - Mevcut: kırmızı ton, `#fef2f2` bg, 42px/800 değer `#dc2626`, altında 4px progress bar (`width:15%`)
  - Çözüm: yeşil ton, `#f0fdf4` bg, 42px/800 değer `#059669`, altında 4px progress bar (`width:92%`)
  - Her kartta `border-radius:14px`, padding:24px, sağ üstte emoji ok (⬅️/➡️)
- **Dijital Boşluk Badge** — full-width, `linear-gradient(135deg,#022c22,#064e3b)`, `border-radius:12px`
  - Sarı ikon daire (`rgba(251,191,36,.15)` bg)
  - "Dijital Boşluk" label, `%X İyileşme Potansiyeli` (altın `#fbbf24`, 26px/800)
  - Açıklama: "Dijital eksikler giderildiğinde ulaşılabilecek seviye"
- **Eksik Kartları** — flex column, gap 8px (table YOK)
  - Her kart: `display:flex`, sol kenar 3px renk kodu, `background:{seviye_bg}`, `border-radius:10px`
  - SVG icon (feather: globe, calendar, search, smartphone, message-circle, users) — 18px, renk kodlu
  - Title (13px/600) + description (11px/#64748b)
  - Sağ taraf: impact badge (Yüksek/Orta/Düşük — `border-radius:6px`, `font-size:10px`, `text-transform:uppercase`)
  - Seviye renkleri: yuksek=`#dc2626` bg=`#fef2f2` border=`#fecaca`; orta=`#ea580c` bg=`#fff7ed` border=`#fed7aa`; dusuk=`#ca8a04` bg=`#fefce8` border=`#fde68a`
- **Çözüm Kartları** — 2×2 grid, gap 10px
  - Her kart: `display:flex`, padding 14px, `#f9fffb` bg, `1px #d1fae5` border, `border-radius:10px`
  - Emoji ikon (🌐🤖📈📊) + title (13px/600 #065f46) + desc (11px #047857)
- **Teklif Kartı** — `2px #d4a853` border, `border-radius:14px`, padding 28px, `box-shadow:0 4px 20px rgba(212,168,83,.08)`
  - "Özel Teklif" tag: `#fffbeb` bg, `1px #fef3c7` border, uppercase
  - İşletme adı + `%X Dijital İyileşme | ilk ay ücretsiz`
  - CTA butonu: `#064e3b` bg, 8px border-radius, "📅 Ücretsiz Keşif Görüşmesi"
- **Footer** — `10px #94a3b8`, ErgeneAI iletişim + ©2026 + gizlilik notu

**Tasarım pitfall'ları:**
- `page.pdf()` çağrısında `print_background=True` eklenmeli (yoksa gradient'ler, pattern'ler ve bg renkleri PDF'te görünmez)
- Google Fonts sayfa içinde `@import` ile çekilmeli — `wait_for_load_state("networkidle")` font'ların yüklenmesini bekler
- İşletme adında `&` karakteri varsa HTML entity `&amp;` kullan
- icon_map SVG'leri feather icons set'inden, 18px viewBox, `currentColor` ile renklendir
- Kategori tespiti: lead JSON'daki `kategori` alanından (küçük harf normalize et)
- Dosya boyutu hedefi: ~250-270 KB (çok düşükse CSS eksik, çok yüksekse resim/gereksiz öğe var)

### WhatsApp Bot Ürünleştirme Stratejisi (16.06.2026)

Meta, 15 Ocak 2026'dan itibaren WhatsApp Business API'de genel amaçlı AI chatbot'ları yasakladı. Etkilenen: ChatGPT tarzı genel asistanlar. **Etkilenmeyen:** İşletmelere özel randevu/müşteri hizmeti botları.

**Strateji:** WhatsApp'ı tek kanal yapma. Ürünü AI İşletme Asistanı olarak konumlandır, kanal bağımsız:

| Kanal | Maliyet | Risk | Öncelik |
|-------|---------|------|---------|
| Web Widget (ergeneai.com) | Sıfır | Yok | Birincil |
| Instagram DM | Sıfır | Düşük | Birincil |
| WhatsApp (Business API) | Var | Orta | Ikincil |
| SMS | Düşük | Yok | Alternatif |

Müşteri WhatsApp isterse kendi Business API hesabını açar, biz AI katmanını bağlarız. Ana ürün WhatsApp değil, web + IG + SMS üçgeni.

Detay: `references/whatsapp-policy-2026.md`

### Canva API Entegrasyonu (Çalışıyor — 16.06.2026)

Canva Connect API ile OAuth + token yönetimi tamamlandı. PDF üretimi için henüz kullanılmıyor (Playwright daha kararlı).

**Durum:** OAuth flow başarılı, access_token + refresh_token alınıyor. API erişimi sınırlı.

**Yapılanlar:**
- OAuth 2.0 authorization_code + PKCE flow tamamlandı
- Access token (4 saat) + refresh token alındı
- Token refresh cron job'u: canva-token-refresh (her 3 saat)
- Token depolama: ~/.hermes/canva_token.json
- PKCE verifier depolama: ~/.hermes/canva_pkce.json

**Çalışan API'ler:**
- GET /rest/v1/users/me -> kullanıcı + takım bilgisi
- GET /rest/v1/assets/{assetId} -> asset metadata
- POST /rest/v1/designs -> yeni tasarım oluşturma
- POST /rest/v1/oauth/token -> token alma/yenileme

**Çalışmayan API'ler:**
- GET /rest/v1/designs -> 403 (design:content:read listing yetkisi vermiyor)
- GET /rest/v1/brand-templates -> 403 Enterprise gerekli (bizde yok)

**Callback Proxy Altyapısı:**
```
Kullanıcı -> ergeneai.com/canva-callback?code=...
    -> Traefik (Docker) -> socat container (host-gateway)
        -> host:8889 (/opt/hermes/hq/server.py)
            -> code /tmp/canva_code.txt'ye yazılır
```
socat container: alpine/socat:latest, --add-host host.docker.internal:host-gateway ile Linux host'a erişir. Traefik label'ları ile HTTPS routing.

**OAuth Flow (PKCE):**
```
# 1. PKCE hazırlık
verifier = secrets.token_urlsafe(64)
challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
# Verifier'ı kaydet: ~/.hermes/canva_pkce.json

# 2. Bilal'e link ver
auth_url = yetkilendirme linki (code_challenge ile)

# 3. Bilal tamam deyince /tmp/canva_code.txt'den code'u oku

# 4. Token al: POST /rest/v1/oauth/token
#    grant_type=authorization_code, code, client_id, client_secret, redirect_uri, code_verifier
```

**Token Yenileme:**
POST /rest/v1/oauth/token
  grant_type=refresh_token
  refresh_token=<REFRESH_TOKEN>
  client_id=OC-AZ6tSp28HQ95
  client_secret=<SECRET>

**Kısıtlar (unutma!):**
- Canva API client_credentials desteklemez — sadece authorization_code veya refresh_token
- Auth code 10 dk geçerli — hızlı işlem yap
- Brand template'ler Enterprise plan gerektirir — PDF'ler için Playwright kullan
- Design listing endpoint'i yok (sadece ID ile sorgulama)
- Canva'dan direkt PDF export için Apps SDK gerek (Connect API değil)

**Tokenlar:** ~/.hermes/canva_token.json (access_token + refresh_token), ~/.hermes/canva_pkce.json (verifier history)

### Kullanım
```bash
# Tüm lead'ler için PDF + e-posta üret (python3 ile, Playwright kullanır)
python3 /opt/hermes/scripts/pdf-playwright.py
```

### HTML → PDF Dönüşümü

Playwright Chromium headless ile A4 PDF export. Modern CSS: Plus Jakarta Sans + Inter font (Google Fonts `@import`), gradient arkaplanlar, gölgeler, border-radius. `page.pdf()`'e `print_background=True` eklenmeli — yoksa gradient/pattern görünmez. Google Fonts `wait_for_load_state("networkidle")` ile yüklenir. Hedef dosya boyutu: ~250-270 KB (çok düşükse CSS eksik, çok yüksekse gereksiz öğe var).

### 📢 Kampanya Yönetim Sistemi (20.06.2026)

Lead analizi + mesaj hazırlıktan sonraki adım: **kampanya oluştur, skorla, kişiselleştir, gönder, takip et.**

Yeni kampanya motoru (`/opt/hermes/campaign_manager.py`) Jeff Web API'ye (port 8892) entegre edildi.

### Kampanya Akışı

```
1. Niche seç → Kampanya oluştur
2. Lead'ler skorlanır (0-100)
3. Her lead için DeepSeek ile kişisel mail yazılır
4. Kampanya "hazir" durumunda bekler
5. "Başlat" → Webhook üzerinden Brevo SMTP ile sırayla gönderilir
6. Durum takibi: gönderildi/hata/email_yok
```

### 🔴 KRİTİK: E-posta Formatı Kuralı (20.06.2026)

Bilal'in net düzeltmesi: **Mail "kitabın ortasından başlar gibi" başlamayacak.** DeepSeek prompt'u kurumsal e-posta formatına uygun yazılmalı:

```
1. ✅ Selamlama — "Sayın [İşletme Adı] yetkilisi,"
2. ✅ Tanışma — "Ben ErgeneAI'den [isim], [sektör] işletmelerine AI çözümleri sunuyorum."
3. ✅ Övgü + Sorun tespiti — İşletmenin iyi yönünü takdir et, ardından eksikleri belirt
4. ✅ Çözüm önerisi — AI Agent sistemimizin bu sorunu nasıl çözeceğini anlat
5. ✅ CTA — Ücretsiz demo teklifi, görüşme talebi
6. ✅ Kapanış — Kibar kapanış cümlesi

Kurallar: max 200 kelime, saygılı/profesyonel ton, kişiselleştirilmiş, abartma yok, imza ayrı ekleneceği için gövde'de imza olmayacak, Türkçe.

**Yanlış (eski):**
> "Leinaada Boutique&Café'nin 4.6 puanı ve 285 yorumu harika bir başlangıç, ancak..."

**Doğru (yeni):**
> "Sayın Leinaada Boutique&Café yetkilisi, Ben ErgeneAI'den Ahmet, kafe ve butik işletmelerine yapay zeka destekli çözümler sunuyorum. Google'daki 4.6 puanınız ve 285 yorumunuz, müşteri memnuniyetinde ne kadar başarılı olduğunuzu gösteriyor. Ancak web sitenizin olmaması..."

DeepSeek system prompt'u bu kuralları içermeli. Eğer kullanıcı tekrar "kitabın ortasından başlıyor" derse, prompt'taki kurumsal format kurallarını gözden geçir.

### Lead Skorlama (0-100)

| Faktör | Puan |
|--------|:----:|
| Base | 30 |
| Website yok | +30 |
| Website var (ama iyi değil) | +15 |
| Rating 4.5+ | +15 |
| 200+ yorum | +10 |
| Niche bonus (klinik/diş +15, güzellik +12, vb.) | +5/+15 |

Skor dilimleri: `≥80 🔥 Sıcak`, `≥60 ⭐ İyi`, `≥40 👀 Orta`, `<40 💤 Soğuk`

### Kişisel Mail Üretimi

Her lead için DeepSeek API'ye özel prompt: işletme adı, sektör, puan/yorum, website, sektöre özel AI ihtiyaçları → kişisel teklif içeren mail. Fallback: template.

### UI (Jeff Web API port 8892)

| Sayfa | URL |
|-------|-----|
| Kampanya Listesi | `GET /campaigns-page` |
| Kampanya Detay | `GET /campaign/{id}/page` |
| Skorlu Lead'ler | `GET /leads/scored?niche=guzellik` |

| API | Açıklama |
|-----|----------|
| `POST /campaign/create` | `{niche, name}` → kampanya oluştur |
| `POST /campaign/{id}/start` | Background email gönderimini başlat |
| `GET /campaign/{id}` | Kampanya özeti |

### Mail İçeriği Görüntüleme (Modal Pattern)

Her lead satırında **"👁 Görüntüle"** butonu → tıklayınca Bootstrap modal'da mail body'si görünür.

**Backend:** JSON email dataları Python `json.dumps()` ile JS objesine gömülür:
```python
email_data_dict = {}
for e in campaign["emails"]:
    email_data_dict[e["lead_id"]] = {
        "name": e.get("lead_name", ""),
        "body": e.get("email_body", "")
    }
emails_json = json.dumps(email_data_dict, ensure_ascii=False)
# HTML içinde: <script>const EMAILS = {emails_json};</script>
```

**Frontend (JS):**
```javascript
function showEmail(leadId) {
    const data = EMAILS[leadId];
    if (!data) return;
    document.getElementById('emailModalTitle').textContent = '📧 ' + data.name;
    document.getElementById('emailModalBody').textContent = data.body;
    new bootstrap.Modal(document.getElementById('emailModal')).show();
}
```

**Bootstrap JS her sayfada ZORUNLU:** Detay sayfasında modal varsa Bootstrap JS bundle yüklenmeli. Ana sayfada var diye detay sayfasında olduğunu varsayma.

### ⚠️ Teknik Pitfall'lar

- **F-string ile JS verisi embedding YASAK:** `{ {{', '.join(data)}} }` gibi nested brace yapma → Python f-string parser `TypeError: unhashable type: 'set'` hatası verir. **Çözüm:** `json.dumps()` ile Python dict'ini JSON string'e çevir, direkt embed et.
- **Bootstrap JS tek sayfada kalma:** Ana sayfaya ekleyip alt sayfalara eklemeyi unutma. Detay sayfasında modal varsa Bootstrap JS orada da olmalı.
- **Modal açmak için vanilla JS kullan:** jQuery `$('#modal').modal('show')` → Bootstrap 5'te çalışmaz. `new bootstrap.Modal(document.getElementById('modal')).show()` kullan.

### Dosyalar

- `/opt/hermes/campaign_manager.py` — Kampanya motoru (scoring, DeepSeek, sending)
- `/opt/hermes/jeff-web-api.py` — Web API + HTML UI (port 8892)
- `/home/hermes/campaigns/` — Kampanya data (.json)
- `/home/hermes/mail-webhook-server.py` — Brevo SMTP webhook (systemd: mail-webhook.service, port 8877)
- `/home/hermes/ergeneai-email-signature.html` — İmza HTML

Detay: `references/campaign-management.md`

---

## E-posta Pipeline (20.06.2026 — Güncelleme)

**İKİ sistem var:**

| Sistem | Durum | Kullanım |
|--------|-------|----------|
| **Brevo SMTP Webhook** (YENİ) | ✅ Kalıcı, systemd | **Toplu kampanya gönderimi** |
| **Gmail SMTP** (emailer.py) | ⚠️ Legacy | Dashboard tekil butonları |

### Brevo SMTP Webhook (Birincil)

`/home/hermes/mail-webhook-server.py` → systemd `mail-webhook.service` → port 8877
```bash
POST http://193.164.4.149:8877/send-mail
{"toEmail": "...", "subject": "...", "body": "<html>..."}
```
Kampanya motoru arka planda her lead'e sırayla istek atar (2sn aralık).

### Legacy Gmail SMTP
Eski sistem (`/home/hermes/ergeneai-dashboard/emailer.py`) hala çalışır. Detay: `references/email-pipeline-smtp.md`

---

## E-posta Pipeline (Gerçek SMTP — 19.06.2026)

E-posta motoru `/home/hermes/ergeneai-dashboard/emailer.py`: Gmail SMTP + smtplib + HTML şablon.

### Kurulum (Tek Seferlik)

1. Kullanıcı: https://myaccount.google.com/apppasswords → "ErgeneAI CRM" için 16 haneli uygulama şifresi oluştur
2. Dashboard'da "E-posta Ayarla" butonu → uygulama şifresini gir → sistem test maili atar
3. API key stored in `~/.hermes/.env` as `GMAIL_EMAIL` + `GMAIL_APP_PASSWORD`

### E-posta Motoru (emailer.py)

```
get_smtp_config()      → ~/.hermes/.env'den Gmail creds oku
save_smtp_config()     → creds'i .env'ye yaz (600 chmod)
send_email(to, subject, html, text) → smtplib.SMTP + STARTTLS
build_email_html(lead, message)     → lead'e özel HTML şablon (yeşil ErgeneAI teması)
send_lead_email(lead, test_mode)    → tek lead'e mesaj gönder + kayıt ekle
send_bulk_emails(niches, max, test) → toplu gönderim (1.5 sn rate limit)
```

### API Endpoint'leri

| Method | Endpoint | İşlev |
|--------|----------|-------|
| POST | `/api/configure-email` | Gmail app password kaydet + test maili gönder |
| POST | `/api/send-email/{id}` | Tek lead'e kişisel e-posta gönder |
| POST | `/api/send-bulk` | Toplu gönderim (niches[], max, test parametreleri) |
| GET | `/api/email-config-status` | E-posta yapılandırma durumu sorgula |

### HTML E-posta Şablonu

```html
<!DOCTYPE html>
<body style="margin:0;padding:0;background:#f4f7f6;">
<table width="560" cellpadding="0" cellspacing="0">
  <tr><td style="background:#198754;padding:24px 32px;">
    <h1 style="color:#ffffff;">ErgeneAI</h1>
  </td></tr>
  <tr><td style="padding:32px;">
    {{kişisel_mesaj_paragrafları}}
  </td></tr>
  <tr><td style="background:#f8faf9;padding:20px;text-align:center;">
    ErgeneAI — İşletmeler İçin AI Çözümleri<br>
  </td></tr>
</table>
</body>
```

### Konu Satırı (İhtiyaca Göre)

| İhtiyaç | Konu |
|---------|------|
| website | "AI Çözüm Önerisi: [işletme]" |
| otomasyon | "AI Otomasyon Teklifi: [işletme]" |
| diğer | "AI Çözüm Önerisi: [işletme]" |

### Gönderim Logiği

- Lead'de `email` alanı yoksa → atlanır (telefon var diye mail gönderilmez)
- Lead'de `emails[]` array'i varsa → daha önce mail gitmiş demektir → atlanır
- Gönderim sonrası lead status'u "new" → "contacted" olur
- Rate limit: 1.5 sn bekleme (Gmail günlük 500, SMTP rate ~1/sn)

### Dashboard UI Pattern'leri

Detay panelinde "E-posta Gönder" butonu:
```html
<button class="btn btn-outline-primary btn-sm flex-fill" onclick="sendSingleEmail()">
  <i class="bi bi-envelope"></i> E-posta Gönder
</button>
```

Navbar'da dropdown menü:
```html
<div class="dropdown">
  <button class="btn btn-outline-primary btn-sm dropdown-toggle" data-bs-toggle="dropdown">
    <i class="bi bi-envelope"></i>
  </button>
  <ul class="dropdown-menu dropdown-menu-end">
    <li><a onclick="openEmailConfig()"><i class="bi bi-gear"></i> E-posta Ayarla</a></li>
    <li><hr></li>
    <li><a onclick="sendBulkTest()"><i class="bi bi-eye"></i> Test Önizleme</a></li>
    <li><a onclick="sendBulkAll()"><i class="bi bi-send"></i> Tümüne Gönder</a></li>
    <li><hr></li>
    <li><a onclick="sendBulkNiche('guzellik')"><i class="bi bi-flower1"></i> Güzellik'e Gönder</a></li>
    <li><a onclick="sendBulkNiche('avukat')"><i class="bi bi-bank"></i> Avukat'a Gönder</a></li>
  </ul>
</div>
```

### E-posta Yapısı (Detay Panelinde Gösterim)

```\nKONU: AI Çözüm Önerisi — [İşletme Adı]\n\nMerhaba [işletme] yetkilisi,\n\nBen ErgeneAI'den Bilal. [işletmenizin AI otomasyon potansiyeli ile ilgili kişiselleştirilmiş giriş metni]\n\n[tespit edilen otomasyon ihtiyaçlarına göre AI çözüm önerileri]\n\n[sektöre özel kapanış ve CTA]\n\nTeşekkürler,\nBilal Ergene\nErgeneAI — İşletmeler İçin AI Çözümleri\n```

### Pitfall'lar

- **Gmail uygulama şifresi:** Normal Gmail şifresi SMTP'de çalışmaz. App Password gerekir (2 adımlı doğrulama açık olmalı)
- **email alanı yoksa:** Lead JSON'ında "email" alanı yoksa gönderim başarısız döner. Telefon varsa da mail atılmaz (eksik data)
- **Rate limit:** Gmail günlük 500 mail, ~1/sn rate. 1.5 sn bekleme ile 32 lead ~48 sn sürer
- **.env güvenliği:** `chmod 600` ile korunmalı, shell expansion sorunu yaşamamak için python3 ile yaz
- **Server restart:** main.py güncellenince uvicorn process kill edilip yeniden başlatılmalı. `lsof -i :port` ile kontrol et
- **Duplicate DOMContentLoaded:** index.html'de birden fazla DOMContentLoaded listener'ı olursa çakışabilir
- **🔴 POZİSYON HATASI:** E-posta/WhatsApp mesajlarında ErgeneAI'yi asla klasik web/SEO ajansı gibi konumlandırma. "Web sitesi yaparız, sosyal medya yönetiriz, SEO yaparız" — bunlar klasik ajans dili. Doğru: "AI otomasyon çözümleri, iş süreçlerinize AI entegrasyonu, akıllı müşteri yönetim sistemleri." İmzada "Dijital Çözümler" yerine "İşletmeler İçin AI Çözümleri" kullan. Her mesajın değer teklifi AI odaklı olmalı, web sitesi odaklı değil. Detay: `references/satis-mesaj-sablonlari.md` başındaki 🔴 KRİTİK bölümü.

## Mobil Demo Sayfası

Her lead için ayrıca mobil uyumlu HTML demo sayfası üretilir. Bilal müşterinin yanında cep telefonundan açar gösterir.

Script: `/opt/hermes/scripts/demo-sayfasi-olustur.py`

```bash
python3 /opt/hermes/scripts/demo-sayfasi-olustur.py
```

## Kanban Entegrasyonu

Tüm ürünler kanban'daki "📁 Çalışmalar" sayfasından erişilir:

| Lead | 📕 PDF | ✉️ E-posta | 📱 Mobil Demo | 📥 İndir (TXT) |
|------|--------|------------|---------------|-----------------|
| Veysel KAYA | ✅ | ✅ | ✅ | ✅ |
| ... | ✅ | ✅ | ✅ | ✅ |

## Dosya Yapısı

```
/opt/hermes/hq/
├── calismalar/      → TXT satış dosyaları (indirilebilir)
├── demo/            → PDF + HTML demo sayfaları
│   ├── veysel-kaya-sac-ekimi.pdf
│   ├── veysel-kaya-sac-ekimi.html
│   └── ...
└── email/           → E-posta taslakları (indirilebilir)
    └── veysel-kaya-sac-ekimi_email.txt
```

## Script Referansları

| Script | İşlev | Çalıştırma |
|--------|-------|-----------|
| `/opt/hermes/scripts/lead-stratejisti.py` | Lead analiz + sıralama + demo metni | `python3` |
| `/opt/hermes/scripts/pdf-playwright.py` | Playwright ile profesyonel PDF + e-posta | `python3` (Chromium) |
| `/opt/hermes/scripts/demo-sayfasi-olustur.py` | Mobil HTML demo sayfası | `python3` |
| `/opt/hermes/hq/server.py` | Kanban sunucusu (8889) | Gateway altında |

### Önemli: Python Sürüm
- Tüm script'ler `python3` (3.10) ile çalışır
- Playwright Chromium headless kullanır (önceden yüklü v1.61.0)
- Yeni paket kurulumu: `pip3 install <paket>` (python3.11'e kurar, gerekiyorsa `python3 -m pip install`)`

## 🔴 KRİTİK — Tam Otomatik Model (19.06.2026 Güncelleme)

> **Bilal (19.06.2026):** "Lead gezmek önceliğimiz değil. İlk pazarlama hamleleri mümkün olduğunca insan müdahalesine gerek kalmadan yapılmalı. Bulduğumuz leadlerin ihtiyaç analizi yapılmalı ve hepsine özel mesaj/mail hazırlanmalı."

**Artık hibrit model yok.** Tüm lead pipeline'ı insansız çalışır:

| Ben (Jeff — %100 otomatik) | Bilal (sadece onay/gönder) |
|---|---|
| Google Places API ile lead bul + CRM'e ekle | İlk e-posta kurulumu için uygulama şifresi sağla (tek seferlik) |
| Web sitesini tara + analiz et (çalışıyor mu, mobil uyumlu mu, SSL var mı) | Dashboard'dan "Tümüne Gönder" butonuna bas (veya cron yapacak) |
| DeepSeek ile ihtiyaç çıkar (web yok, mobil eksik, SEO zayıf) | |
| Kişiye özel mesaj yaz + lead'e kaydet | |
| Önceliklendir (🔴 web yok = acil, 🟡 iyileştirme, ⚪ iyi durumda) | |
| Dashboard'da analiz + mesaj + e-posta gönderme butonu hazır | |
| Gmail SMTP ile otomatik e-posta gönderimi (HTML şablon, kişisel konu) | |

## Pipeline Adımları (Tam Otomatik — 20.06.2026)

Script: `/home/hermes/ergeneai-dashboard/analyzer.py`

Lead kaynağı seçenekleri:
- **Google Places API (New)** — mevcut, çalışıyor
- **Apify Lead Generation** — yeni (Skills Hub), daha geniş kaynak: Google Maps, Instagram, TikTok, Facebook, LinkedIn, YouTube, Google Search. Actor ID'lerinde `/` yerine `~` kullan. Token: `APIFY_TOKEN` in `.env`. Detay: `apify-lead-generation` skill'i.

```
1. Lead tara (Google Places API veya Apify ile) → CRM'e otomatik ekle
   → /api/scrape (POST) {"query": "güzellik salonu", "city": "Mudanya"}
   
2. Lead analiz et (web sitesini tara + ihtiyaç çıkar + mesaj üret)
   → /api/analyze (POST) tüm lead'ler için
   → analyzer.py: check_website() + analyze_lead() + generate_message()
   
3. Dashboard'da göster:
   → Öncelik rozeti (🔴/🟡/⚪) lead kartında
   → Detay panelinde analiz + fırsatlar
   → 💬 Kişisel mesaj + kopyala butonu
   
4. Dashboard'da göster + e-posta gönder:
   → Öncelik rozeti (🔴/🟡/⚪) lead kartında
   → Detay panelinde analiz + fırsatlar + 💬 Kişisel mesaj + 📧 E-posta Gönder butonu
   → Navbar'daki 📧 dropdown menü: tümüne, kategoriye göre toplu gönderim
   
5. (Yeni) Gmail SMTP ile otomatik e-posta gönderimi:
   → emailer.py: smtplib + Gmail App Password + HTML şablon
   → /api/send-email/{id} — tek lead'e kişisel e-posta
   → /api/send-bulk — tüm lead'lere veya kategori filtresiyle toplu gönderim
   → /api/configure-email — Gmail uygulama şifresi kurulumu + test maili
   → Rate limiting: 1.5 sn aralık (Gmail kotası)
   → Gönderim kaydı: lead'e "emails" array'i eklenir, status "contacted" olur
   → Aynı lead'e iki kere mail gitmez (emails array kontrolü)
```

## Web Sitesi Analiz Kriterleri (analyzer.py)

| Kontrol | Puan | Etki |
|---------|:----:|------|
| SSL sertifikası (https) | +20 | Güven |
| Mobil uyumlu (viewport/responsive) | +20 | Mobil trafik |
| Title tag var | +10 | SEO |
| Google Analytics var | +10 | Ölçümleme |
| WhatsApp bağlantısı | +10 | Dönüşüm |
| WordPress/Wix (yönetilebilir) | +15 | Güncelleme |
| Hızlı yükleniyor | +15 | Kullanıcı deneyimi |

**Skor aralıkları:** 0-39 = Web sitesi yok/kötü (🔴), 40-69 = Orta (🟡), 70+ = İyi (⚪)

## İhtiyaç Kategorileri

| İhtiyaç | Tespit | Öncelik |
|---------|--------|---------|
| Web sitesi yok | website alanı boş | 🔴 Yüksek |
| Web sitesi açılmıyor | HTTP error veya timeout | 🔴 Yüksek |
| Web sitesi zayıf | skor < 40 | 🔴 Yüksek |
| Mobil uyum yok | viewport/media query yok | 🟡 Orta |
| SEO yok | Google Analytics yok | 🟡 Orta |
| WhatsApp yok | whatsapp.com/wa.me linki yok | 🟡 Orta |

## Lead Veri Şeması (CRM v3.0)

```json
{
  "id": "lead-1781856582038-5",
  "name": "Gülnur Yürek Güzellik Merkezi",
  "phone": "+90 542 784 98 58",
  "address": "Mudanya/Bursa...",
  "city": "Mudanya",
  "niche": "guzellik",
  "rating": 5.0,
  "reviews": 86,
  "website": "https://...",
  "lat": 40.375,
  "lng": 28.883,
  "status": "new",
  "source": "google-places",
  "notes": "",
  "analysis": {
    "priority": "high",
    "web_score": 0,
    "needs": ["website"],
    "opportunities": ["🚀 Web sitesi yok..."],
    "analyzed_at": "2026-06-19T..."
  },
  "message": "Merhaba [işletme] yetkilisi...",
  "created_at": "...",
  "updated_at": "..."
}
```

## Batch Campaign Script (email-campaign.py) — 19.06.2026

`email-campaign.py` is a CLI batch campaign tool at `/home/hermes/ergeneai-dashboard/email-campaign.py`. It sends niche-filtered HTML emails to all leads that have an email address.

### 🔴 KRİTİK: ErgeneAI Pozisyonu (19.06.2026 Güncelleme)

**ErgeneAI "İşletmeler İçin AI Çözümleri" sunar — AI Personel sistemleri satarız.**

E-posta içeriği yazarken:
- ❌ "Web sitesi yapıyoruz, Google Maps SEO, sosyal medya hizmeti"
- ❌ "Klasik bir ajans değiliz" (negatif vurgu yapma — direkt ne olduğumuzu söyle)
- ❌ "AI Agent" terimi — Türk KOBİ'si anlamaz
- ✅ "AI destekli müşteri takip sistemi, AI çözümler, otomatik süreç yönetimi"
- ✅ "Her işletmeye özel kurgulanabilir AI Personel — sektör sınırlaması yok"
- ✅ "Dijital Çalışan" — 7/24 çalışır, maaş almaz, hastalanmaz

**🔴 TERMİNOLOJİ KURALI (21.06.2026):** "AI Agent" Türkiye'deki küçük işletme sahibine bir şey ifade etmez. Konuşurken, e-postada, PDF'de hep **"AI Personel"** veya **"Dijital Çalışan"** kullan. Bunun yerine geçen ifadeler: "dijital personel", "yapay zeka personel", "dijital ekip arkadaşı". Teknik terim kullanma. Sade anlat: "Maaş almıyor, 7/24 çalışıyor, hasta olmuyor."

Klasik ajans olduğumuzu reddetme. Direkt AI Agent değer teklifiyle gel. Negatif dil yerine pozitif AI odaklı dil kullan.

İmza: "ErgeneAI — İşletmeler İçin AI Çözümleri" (asla "Dijital Çözümler" veya "Dijital Pazarlama")

Konu satırı: `"{isletme} için AI çözüm önerisi"` (asla "dijital çözüm önerisi")

Her mesajda değer teklifi AI Agent odaklı olmalı, web sitesi/SEO odaklı değil.

- `references/ai-agent-strategy.md` — AI Agent kategorileri, fiyatlandırma, positioning evrimi.
- `references/lead-enrichment-validation.md` — Lead enrichment validation test raporu örneği (7 zorunlu alan, enrichment kuralları, sektör test senaryoları).

### CRITICAL Prerequisite: landing_page.body

The script reads `marketing-content/{niche}.json` and requires `landing_page.body` to be a non-null string. **If it's null, the script exits with an error.** Populate it before running:

```python
# Generate niche-specific email body and update the JSON
data = json.load(open(f"marketing-content/{niche}.json"))
data["landing_page"] = {"body": "Şablon metin — {name} yerine isim otomatik gelir"}
json.dump(data, open(f"marketing-content/{niche}.json", "w"), ensure_ascii=False, indent=2)
```

The body text supports `{name}` and `{isim}` placeholders — they're replaced with the lead's short name on send.

### CLI Usage

```bash
cd /home/hermes/ergeneai-dashboard

# Dry-run — shows preview for every lead, NO actual send
python3 email-campaign.py --niche avukat --dry-run

# Real send (requires Gmail app password in .env)
python3 email-campaign.py --niche avukat --send
```

### Output per lead

```
[1/13] Benk Hukuk Bürosu
      📧 info@mehmetbenk.av.tr
      📝 Konu: Benk Hukuk Bürosu için AI çözüm önerisi
      📄 484 karakter
      📋 Önizleme: Benk Hukuk Bürosu Merhaba, ...
```

### HTML Template

Uses `build_html()` in email-campaign.py (not emailer.py's `build_email_html()`):
- ErgeneAI green header (`#198754`)
- White body with personalized paragraphs
- Footer with ErgeneAI tagline
- Table-based layout (email-client safe)

### Send Behavior

- 1.5 second sleep between sends (Gmail rate limit protection)
- Sends to all leads in the niche that have an `email` field
- Leads without email are listed as "⏭️ atlanacak"
- No status update on leads.json (unlike emailer.py's send_lead_email)
- No duplicate-send check (unlike emailer.py's emails[] array)

### Pitfalls

1. **landing_page.body must exist** — if null, script exits immediately with an error
2. **Invalid emails in data** — some scraped emails are sentry/noreply trap addresses (e.g., `605a7baede844d278b89dc95ae0a9123@sentry-next.wixpress.com`). The script sends to them anyway; these will bounce silently
3. **Lead name contains " | "** — `short_name()` splits on ` | ` and takes the first part. E.g., "Bursa Avukat | Av. Eda Beyazıt" → "Bursa Avukat"
4. **No emails[] tracking** — unlike the dashboard bulk send, this script doesn't mark leads as "contacted" or add to an emails[] array. Leads can receive the same campaign multiple times
5. **Script location** — email-campaign.py lives in `/home/hermes/ergeneai-dashboard/`, NOT `/home/hermes/scripts/`
6. Only 7/9 niches have landing_page.body populated (avukat, klinik, fitness, emlak, kafe, kuafor, dis). guzellik and restoran have null body — they'll fail if you try to run campaign on them without generating body content first

## Sık Yapılan Hatalar

- ❌ `python3` ile pdf-sunum-olustur çalıştırmak → "No module named weasyprint". Python 3.11 kullan.
- ❌ HTML demo'yu PDF ile karıştırmak. İkisi ayrı: HTML mobil gösterim, PDF e-posta eki.
- ❌ Server'ı restart etmeden yeni dosyaları görmeye çalışmak. `fuser -k 8889/tcp` + yeniden başlat.

### 🔴 Kritik: Canva OAuth Döngüsü

Canva OAuth flow'unda auth code 10 dakika içinde expire olur. Bilal'e her seferinde "yeni linke tıkla, code'u bana ver" demek **döngüye girmek demektir** — Bilal 3 kereden fazla aynı şeyi tekrarlatmaz.

**Doğru yaklaşım:**
1. PKCE code_verifier + code_challenge hazırla (ama linki hemen verme)
2. **Callback mekanizması çalışmalı** — Canva redirect yapınca code server'a otomatik gelsin
3. Bilal'e sadece bir kere link gönder. Çalışmazsa **yöntem değiştir**, aynı yöntemi tekrarlama
4. En kararlı çözüm: Playwright ile HTML→PDF. Canva'ya bağımlı kalma

**Kural:** Aynı OAuth adımını 2 kereden fazla tekrarlama. Başarısız olduysa alternatif yönteme geç (Playwright).

## 🔴 KRİTİK — DM/WhatsApp Pazarlama Kanalı (20.07.2026) — Güncelleme

> **Bilal:** "Pazarlamayı DM ve WhatsApp üzerinden yapacağız asıl olarak. Instagram hesabı ve telefon (WhatsApp) olmayan lead kaydetmenin anlamı yok."

**DM/WhatsApp artık BİRİNCİL pazarlama kanalıdır.** Email ikincildir.

### Lead Hazır Olma Kontrolü

Pipeline'a girmeden önce iki bilgi ZORUNLUDUR:

| Bilgi | Kaynak | Pazarlama Kanalı |
|-------|--------|------------------|
| 📸 **Instagram hesabı** | `web_search("site:instagram.com ...")` | DM gönderimi |
| 📞 **Telefon (WhatsApp)** | Lead verisinden | WhatsApp mesajı |

**Ready = IG var + Telefon var.** Email olmasa da olur (ikincil kanal).

### Pipeline 2-Tab Sistemi (Monitor)

Monitor sayfası iki tab'a ayrılır:

| Tab | İçerik | JS Filtre |
|-----|--------|-----------|
| 🎯 **DM'e Hazır** | Sadece `isReady(l)` lead'ler | `hasIG(l) && hasPhone(l)` |
| 🔍 **Eksik Bilgi** | Kalan lead'ler (IG/telefon eksik) | `!isReady(l)` |

Varsayılan "DM'e Hazır" tab'ı açılır. Eksik Bilgi tab'ında kırmızı uyarı banner'ı gösterilir. Stage ayrımı da var: `New → Pipeline`, `Contacted/Replied/Booked/Won/Lost → İşlenmiş`.

### Instagram Discovery — 4 Strateji (Kanıtlanmış, 20.07.2026)

| Strateji | Yöntem | Başarı Oranı |
|----------|--------|:--------:|
| **site:instagram.com** | `web_search("site:instagram.com \"İşletme\" Şehir")` | ~%70 |
| **Websitesi crawl** | `web_extract(url)` ile sosyal link tara | ~%30 |
| **İsim varyasyonu** | Kısa ad, farklı keyword ile tekrar dene | ~%15 |
| **Google Maps fallback** | İşletme sayfasında sosyal link var mı | ~%5 |

Örnek (20.07.2026 — 40 lead tarandı):
- Saç ekimi/estetik: ~%90 başarı (10/11 bulundu)
- Otel: ~%70 başarı (12/17 bulundu)
- Diş kliniği: ~%40 başarı (2/5 bulundu)

**IG bulunamazsa → pipeline'dan çıkarılır, "Eksik Bilgi" havuzuna alınır.** İleride yeni lead geldiğinde aynı stratejiler tekrar dener.

### Kişiselleştirilmiş DM Metni Hazırlama

Her **Ready** lead için DM yazılır. DM metni iki yerde durur:
1. `/opt/hermes/monitor/solutions/[lead_adi_kisa].txt` — ayrı txt dosyaları
2. Monitor'de lead kartındaki `📝 DM Metni` butonunda

#### DM Formatı (KESİN — 20.07.2026, Bilal Onaylı)

```
İşletme Adı — Şehir
@instagram (varsa)
📞 telefon

Merhabalar, işletme profillerinizi analiz ettik ve size bir kaç önerimiz var.
[2-3 cümle: işletmenin güçlü yanları + sektör gözlemi + eksik tespiti]
[1-2 cümle: çözüm yaklaşımı, nasıl yardımcı olabileceğimiz]
[CTA: konuşmak ister misiniz?]
```

**Kurallar:**
- ❌ Fiyat, ücret, paket, TL, USD, ₺ gibi kelimeler ASLA yazılmaz
- ❌ Uzun metin olmaz (max 5-6 cümle)
- ✅ **Giriş cümlesi değişmez:** "Merhabalar, işletme profillerinizi analiz ettik ve size bir kaç önerimiz var."
- ✅ Lead'in sektörüne/işletmesine özel gözlem (siteden veya IG'den alınan gerçek spesifik detay)
- ✅ Samimi ama profesyonel ton
- ✅ Son cümle soru (konuşmak ister misiniz?)

#### Sektöre Göre DM Odağı

| Sektör | DM'de Vurgulanacak |
|--------|-------------------|
| 🦷 Diş Kliniği | Online randevu eksikliği, IG içerik akışı, Google görünürlük, hasta yorumları |
| 💇 Saç Ekimi | Yabancı hasta çekme, İngilizce içerik, before/after galerisi, WhatsApp iletişim |
| 🏨 Otel | IG görsel içerik kalitesi, online rezervasyon, Google Hotel, yorum yönetimi |

#### Lead Kartı Chip'leri (Monitor)

Her lead kartında 3 chip (renk kodlu, `info-chip` class):

| Chip | Var | Yok |
|------|-----|-----|
| 📸 IG | `chip-ig-yes` (mor `#bc8cff`) | `chip-ig-no` (kırmızı) |
| 📞 Tel | `chip-wa-yes` (yeşil `#3fb950`) | `chip-wa-no` (kırmızı) |
| 📧 Email | `chip-email-yes` (mavi `#58a6ff`) | `chip-email-no` (kırmızı) |

Alt kısımda `📝 DM Metni` butonu (mor, full-width, `class="dm-btn"`, `1px solid var(--purple)`).

#### DM Modal JS API (Monitor'de)

```javascript
const SOLUTIONS = {}; // lead_name → txt string

function showDM(name) {
  const txt = SOLUTIONS[name];
  if (!txt) { alert('Henüz hazır değil.'); return; }
  // dmTitle = name
  // dmSub = ilk 3 satır (ad, IG, tel)
  // dmBody = kalan metin
  // dmOverlay.classList.add('open')
}

function copyDM() {
  // navigator.clipboard.writeText(full) + fallback
  // dmCopied.style.display = 'block' (2sn sonra kaybolur)
}

function closeDM() {
  // dmOverlay.classList.remove('open')
}
```

Modal CSS: `dm-overlay` (fixed, inset 0, bg rgba(0,0,0,.7)), `dm-modal` (max-width 560px, bg card), `dm-body` (user-select:all, pre-wrap). Tek tıkla kopyalama için DM body'e de `onclick="copyDM()"` eklenir.

### SOLUTIONS Klasörü ve Monitor URL

```bash
/opt/hermes/monitor/solutions/    # Her Ready lead için bir .txt
├── devadent.txt
├── kruezi.txt
├── urotas.txt
└── ...
```

Monitor: `http://193.164.4.149:8081` — `lead-monitor.service` (systemd, restart=always).

Ana dosya: `/opt/hermes/monitor/index.html` — 26+ lead gömülü JSON + SOLUTIONS objesi + INSTAGRAM_MAP. Yeni lead eklenince HTML manuel güncellenir (LEADS[] + SOLUTIONS{} + INSTAGRAM_MAP{} birlikte).

---

## Lead Enrichment Validation (7 Zorunlu Alan)

Her lead enrichment sonrası **7 zorunlu alan** kontrol edilmelidir. Bu alanlar pipeline kalite kapısıdır — eksik alan varsa enrichment tamamlanmamış sayılır.

### 7 Zorunlu Alan

| # | Alan | Tip | Açıklama |
|---|------|-----|----------|
| 1 | `provider` | string | enrichment kaynağı: `web_extract` / `hunter_api` / `apollo_api` / `manual` / `skipped` |
| 2 | `lead_id` | string | lead identifier (örn. `lead-test-001`) |
| 3 | `attempt` | int | bu lead için kaçıncı enrichment denemesi |
| 4 | `result` | string | `found` / `not_found` / `skipped` |
| 5 | `email` | string | bulunan email (yoksa `-`) |
| 6 | `cost` | string | tahmini maliyet dolar cinsinden (örn. `$0.00`) |
| 7 | `next_channel` | string | önerilen bir sonraki iletişim kanalı: `email` / `whatsapp` / `phone` / `none` |

### Enrichment Kuralları

| Kural | Açıklama | İhlal Sonucu |
|-------|----------|-------------|
| **Boş Lead Atlanamaz** | Ne email ne telefon ne WhatsApp'ı olmayan lead ZORUNLU taranır. Web_extract ile email ara, bulunamazsa telefon/whatsapp tara. | Lead atlanırsa pipeline'dan geçemez |
| **Kanal Geçişi Meşruiyeti** | Email→WhatsApp/Telefon geçişi ANCAK şu 4 koşulun TAMAMI karşılanırsa meşrudur: (1) Email adresi geçerli değil (bounce), (2) Email'e 3 iş günü yanıt gelmedi, (3) Lead'in websitesinde/whatsapp linki var, (4) Email'de WhatsApp alternatifi belirtildi | Geçiş yapılırsa spam/şikayet riski |
| **Cost Şeffaflığı** | Her enrichment için maliyet belirtilmeli | Raporda maliyet tahmini eksik kalır |
| **Atlanan Lead Loglanır** | `result: skipped` olan lead'ler neden skip edildiği not edilerek kaydedilmeli | Pipeline audit trail'i kaybolur |

### Provider Maliyet Referansı

| Provider | Cost/Lead | Açıklama |
|----------|-----------|----------|
| `web_extract` | $0.00 | Web scraping, ücretsiz, ~%35 başarı oranı |
| `hunter_api` | $0.01 | Hunter.io email API, ~%50+ başarı |
| `apollo_api` | $0.02-0.05 | Apollo.io (free plan sınırlı, paid gerekebilir) |
| `manual` | $0.00 (zaman) | İnsan eliyle araştırma, yüksek doğruluk |

### Enrichment Rapor Örneği

Tam rapor örneği için: `references/lead-enrichment-validation.md`

## ⛔ HEDEFLEME DERSİ — "Dijital Zayıf İşletme" Önermesi ÇÖKTÜ (11.09.2026)

Bursa'da tüketiciye dönük hizmet işletmeleri (emlak, güzellik, kuaför, veteriner) **Instagram'ı ana vitrin olarak kullanıyor**. "Dijital zayıf" diye sınıflandırılan işletmelerin canlı ölçümü: 163.000 / 28.000 / 22.000 / 20.000 / 11.000 / 10.000 / 7.153 takipçi.

**Kural:** `SITE_YOK`, `SOSYAL_MEDYA`, `whatsapp=false` alanları dijital zayıflık KANITI DEĞİL — bunlar false negative üretir. Statik HTML taraması JS widget'larını ve Instagram vitrinini göremiyor.

- "Dijitaliniz yok" içerikli hiçbir teklif, **o işletmenin Instagram'ı okunmadan** gönderilemez (skill: `instagram-public-okuma`).
- **Cicim Güzellik**: 425 Google yorumu / 163K IG takipçisi — "sosyal medya sınıfı" diye işaretlenmişti.

**Ayakta kalan tek hedefleme sinyali — KIRIK ZİNCİR:** İşletmenin kendi müşteri yolunda **nesnel olarak kırık** bir halka. En güçlüsü: Google profili → ölü domain (DNS ile doğrulanır, 2 saniyede işletmeye gösterilir, tartışılamaz).

229 işletmede ölü domain oranı: **6/229 (%2.6)** — vetorka.com (640 yorum), bursagayrimenkulemlak.com (144), ulusotobursa.com (136), gultenaltikardes.com (55), safaksariyildiz.com.tr (20), realtyworldonurgayrimenkul.com (16).

**Uyarı:** Vetorka'nın domain'i ölü ama 7.153 takipçili Instagram'ı var → "siten ölü" acısı orada hafifler. Ölü domain + zayıf IG kesişimi asıl hedef.

## 📜 ONAYLI MASTER PLAN — TEKRAR İCAT ETME (11.09.2026)

Revnue stratejisi sıfırdan yeniden düşünülmez: **`/opt/hermes/revenue-intelligence/PLAN-v1.md`** (1247 satır, Bilal onaylı 09.09.2026) teklifi zaten tanımlar.

> *"Size yapay zekâ satmıyoruz. Dijitalde nerede para kaybettiğinizi buluyor ve bu kayıpları kapatmak için uygulanabilir bir plan sunuyoruz."*

- **Model A:** ücretsiz mini audit → keşif görüşmesi → ücretli uygulama → aylık retainer
- **Mini audit =** 3 kritik bulgu + 1 rakip karşılaştırması + 1 hızlı kazanım + 1 açık soru
- **Fiyat bandı:** Deep Audit 2.500–5.000 TL · Implementation 15.000–50.000 TL · Retainer 5.000–20.000 TL/ay
- **Yasak:** "kesin şu kadar TL kaybediyorsunuz" — kanıt / güçlü çıkarım / senaryo katmanı ayrılır

**Yapılan hata:** ADE muhakemesine teklif olarak "AI/otomasyon" verildi. Bu ÇERÇEVE DEĞİL. Stratejik muhakeme koşturmadan önce PLAN-v1 okunur — yoksa muhakeme yanlış teklifi tartışır ve RESEARCH verdict'i yanıltıcı olur.

**Ders:** Plan onaylıysa eksik olan teklif değil, UYGULAMADIR. 229 hedef tarandı, aylarca analiz yapıldı, 0 mini audit üretildi, 0 mesaj gitti — bu asıl darboğazdı.

## 🔬 NİŞ NORMU KONTROLÜ — "SİTE YOK" ARGÜMANI (11.09.2026)

Bir kusuru satış argümanı yapmadan önce **o nişte ne kadar yaygın** olduğunu say. Yaygın olan şey fark yaratmaz.

Örnek (Bursa veteriner, 20 klinik): site sahibi 9, sitesiz 11 → **"sitesizlik" bu nişte satış argümanı DEĞİL**. Argüman şu: *"siten var ama ölü"* (vetorka.com) veya *"siten var ama tarayıcı uyarı veriyor"* (venaveteriner.com) — çünkü site sahibi rakipler sorunsuz çalışıyor. Fark orada.

Kural: her bulgu için *"rakiplerde nasıl?"* sorusunu yanıtla. Yanıtlanamıyorsa bulgu satışa çıkmaz.

## 🔎 SSL/DOMAIN BULGUSU DOĞRULAMA PROTOKOLÜ (11.09.2026)

Kusur iddiası tek araca dayanamaz. Üçü birlikte koşulur:

```bash
# 1) Bağımsız DNS — yerel resolver yanıltır, İKİ resolver kullan
dig +short @1.1.1.1 <domain> A ; dig +short @8.8.8.8 <domain> SOA   # ikisi de boşsa domain DNS'te YOK
# 2) HTTP katmanı (site var mı, yoksa sadece HTTPS mi kırık)
curl -sS -o /dev/null -w '%{http_code} %{size_download}\n' -m 12 http://<domain>/
curl -sS -o /dev/null -w '%{http_code}\n' -m 12 https://<domain>/   # exit 60 = SSL problemi
# 3) Sertifika kimliği
openssl s_client -connect <domain>:443 -servername <domain> | openssl x509 -noout -subject -issuer
```

**İmzalar:**
- `curl: (6) Could not resolve host` + A/NS/SOA boş → domain DNS'te kayıtlı değil (ölü).
- `subject=CN = *.xyz, O = WakkoServer` → hosting panelinin **varsayılan sahte sertifikası**, alan adına ait değil. Chrome `net::ERR_CERT_AUTHORITY_INVALID` verir.
- **Kontrol grubu şart:** aynı nişteki çalışan bir rakibin sertifikası da kontrol edilir (Google Trust Services imzalı + HTTP 200 çıkıyorsa fark kanıtlanmış olur).
- Port 80'de 200 dönüyorsa site VAR, sadece HTTPS kırık → "siteyi düzelt" değil "sertifikayı düzelt" işi (daha küçük, daha hızlı kazanım).

## 📋 cevap-log.csv FORMATI — ÜZERİNE YAZMA (11.09.2026)

`/home/hermes/fpc/cevap-log.csv` **noktalı virgülle** ayrılmıştır ve BOM (`\ufeff`) ile başlar:
```
id;isletme;nis;grup;telefon;hat;kanal_plan;t0_gonderim;yanit_saati;yanit_dk;sinif;not
```
Python `csv.writer` (virgül) ile yazmak dosyayı bozar. Yeni satır eklerken dosyayı düz metin olarak oku, satırları `;` ile birleştirerek ekle. ID ön ekleri: `E` (emlak/hedef), `V`, `K`, `Y` (kontrol).

## 📦 SOĞUK TEMAS PAKETİ — GÖNDERİMDEN ÖNCE 6 KONTROL (12.09.2026)

Havuzdan hedef seçip mesaj yazarken sırayla uygula. Her biri gerçek bir hatadan çıktı.

1. **Bulgu bayatlar — göndermeden önce aynı gün yeniden doğrula.** Havuz büyüdükçe eski iddialar çöker: "300+ yorumlular arasında en düşük puan" iddiası, havuza 4.2 puanlı yeni bir klinik eklenince geçersizleşti. DNS/SSL/HTTP + benchmark aynı gün koşulur. Kıyası **sıralama** üzerinden değil **ortalama** üzerinden kur ("100+ yorumlu kliniklerin ortalaması 4.55, siz 4.3") — savunması kolay, itiraz edilemez.
2. **Marka kirlenmesi:** kontrol grubundaki ya da mesajı hazır yazılmış bir markanın başka şubesi yeni listeye girmez ("Akademi Kids" vs kontrol "Akademi Hayvan Hastanesi", "Vena Gürsu" vs hedef "Vena Veteriner"). Ölçüm karışır, test sonucu okunamaz.
3. **Kanal = numara tipi.** `05xx` → WhatsApp, `0224` sabit → ARAMA. Paket tablosunda kanal kolonu zorunlu; "mesaj gönderecek" sanılan hedef sabit hat çıkarsa plan çöker.
4. **Müşteri metni çoğul konuşur:** "yaptık / ettik / doğruladık … mısınız". "yaptım/ettim" tek kişilik girişim izlenimi verir. Türkçe karakterler korunur — `Klinigi`, `Baglantiniz gizli degil` gibi ASCII'ye düşmüş metin amatör durur.
5. **Kişisel WhatsApp hız sınırı:** aynı numaradan günde 7+ soğuk mesaj spam işaretine ve numara kısıtına yol açar. 20'lik paketi 3 güne yay (7/gün), hepsini tek günde gönderme.
6. **Mesaj gövdesi yalnız doğrulanmış bulgu taşır:** site yok / DNS ölü / SSL geçersiz / 404 / yorum-puan ortalaması. "Dijitaliniz zayıf" gibi genel suçlama ve fiyat/teklif dili bu aşamada yasak; kapanış tek soru — "Bunun farkında mıydınız? 3 maddelik kısa özetini paylaşabiliriz."

## Referanslar

- `references/whatsapp-policy-2026.md` — WhatsApp Business API politika değişikliği (Ocak 2026)
- `references/canva-api-oauth.md` — Canva Connect API OAuth + PKCE flow, token yönetimi
- `references/satis-mesaj-sablonlari.md` — WhatsApp Business API politika değişikliği (Ocak 2026). WhatsApp bot ürünleştirirken oku.
- `references/automated-analysis-pipeline-2026-06-19.md` — Otomatik lead analiz + kişisel mesaj pipeline'ı implementasyon detayları. Google Places API (New), analyzer.py, frontend analiz gösterme kalıpları.
- `references/email-pipeline-smtp.md` — Gmail SMTP e-posta pipeline'ı implementasyon detayları. emailer.py mimarisi, API endpoint'leri, UI component'leri, hata senaryoları.
