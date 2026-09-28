# Solar Pro 4 Free — Portal Model Profili (08.09.2026)

## Model Bilgisi

| Özellik | Değer |
|---|---|
| Model slug | `upstage/solar-pro4:free` |
| Provider | `nous` (Nous Portal) |
| Portal ücretlendirme | Free tier (Portal pricing'i: 50 RPM, 500K TPM) |
| Çalışma şekli | Portal OAuth + JWT minting otomatik |
| Config yeri | `~/.hermes/config.yaml` → `model.default` + `model.provider` |

## Neden Bu Model?

**Olay:** 08.09.2026'da 6 cron job + vision analyze `opencode-go` provider'ın `x-opencode-session` header zorunluluğu nedeniyle bozuldu.

**Fix seçimi:** `model: upstage/solar-pro4:free`, `provider: nous` — Portal üzerinden çalışan, header sorunu yapmayan combo.

**Alternatifler val mı?**
- `openrouter` provider: çalışabilir, ama model seçimi OpenRouter catalog'ından — free model'lar limited
- `opencode-go`: artık cron/auxiliary için uygun değil (header zorunluluğu)

## Performans Notları

| Kriter | Değerlendirme |
|---|---|
| Türkçe doğallık | İyi — Bilal'ın kanka dopingine uyuyor, doğal Türkçe, jargon dış |
| Hız/latency | İyi — cron job'ları 2-5dk içinde bitiyor |
| Türkçe içerik kalitesi | Kafa çok iyi değil — direkt, anlaşılır, boş chatbot cevabı yok |
| Çok dilli tutarlılık | Turkish prompt'lar Türkçe çıktı veriyor, English prompt'lar Turkish çıktı vermiyor (beklentisiz) |
| Ücretsiz tier stability | Genelde stabil, ama geçici 429 olabilir (saglik-aksam-kontrol'da 08.09.2026) |
| Portal entegrasyonu | Tam — OAuth token ile çalışıyor, /.env dosyaya yazılmıyor, JWT minting otomatik |

## Bilinen Limitationlar

| Limitation | Not |
|---|---|
| Knowledge cutoff: 2026-02 | Şubat 2026'dan sonrası bilinmiyor — web search gerekirse ayrı tool |
| Gerçek zamanlı veri yok | Web search (Firecrawl) ayrı tool, model parçası değil |
| Vision tool'u çalışmıyor | auxiliary.vision.provider hâlâ opencode-go → vision analyze 400 hatası |
| Kodlama/teknik | Sorunsuza değil — bazı hatalar, eksikler olabilir. Test + doğrulama şart |
| Çok dilli | Her dilde eşit kalite garantisi yok — Turkish'de iyi, diğer dillerde denememiş |

## Şu Anki Kullanım

- Main model (chat, analysis): `upstage/solar-pro4:free` + `nous`
- 6 cron job override: aynı combo (cronjob action=update ile)
- Auxiliary task'lar: hala `opencode-go` / `mimo-v2.5` — vulnerability açık

## Öneri

**Model değiştirmeme gerek yok.** Solar Pro 4 Free şu anki ihtiyaçlara yeterli:
- Türkçe doğal
- Hızlı
- Portal entegrasyonu düz
- Cron'lar düz

**İyileştirme önermek:**
1. `fallback_providers: ['upstage/solar-pro4:free']` → config.yaml'da, şu an boş. 429 aldığında otomatik fallback olsun.
2. Auxiliary provider'ları opencode-go'dan çıkmaya değer — vision analyze çalışmıyor şu an.

## Portal'daki Diğer Free Modeller (bilgi limitli)

Portal docs: "hundreds of models... with free options and Portal-only discounts" diyor ama tam liste JS renderer'ı ve auth barrier nedeniyle erişilemedi.

OpenRouter API'sinden çekilen tek free model:
- `inclusionai/ling-3.0-flash-sante:free` — sağlık/medikal MoEs, 5.1B active / 124B total, 262K context

Ama Portal'ın kendi catalog'ında daha fazlası olabilir — `hermes portal info` ve `hermes model` ile picker açılmalı gerçek liste için.
