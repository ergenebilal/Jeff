# AgencyOS Canlandırma Prosedürü

AgencyOS dashboard "stale" durumuna düştüğünde veya ilk kurulumdan sonra izlenecek adımlar.

## Durum Tespiti

```json
mcp_agencyos_get_memory_dashboard  → liveStatus: "stale" | "live"
mcp_agencyos_get_setup_status      → percentage, eksik adımlar
mcp_agencyos_health_check_apis     → hangi API'ler eksik
```

## Canlandırma Adımları (sırayla)

### 1. Strategy Snapshot Doldur

```json
mcp_agencyos_update_strategy({
  northStar: "Hedef cümlesi",
  currentFocus: "Şu an neye odaklanılıyor",
  audience: "Hedef kitle açıklaması",
  doList: ["Yapılacak 1", "Yapılacak 2"],
  dontDoList: ["Yasak 1", "Yasak 2"],
  voiceRules: "Marka sesi/tonu açıklaması"
})
```

### 2. Marka Kimliği Güncelle

```json
mcp_agencyos_update_agency_identity({
  agencyName: "Marka Adı",
  agencyDescription: "Açıklama",
  primaryNiche: "Ana sektör",
  valueProposition: "Değer önerisi",
  soul: "Marka sesi/kişiliği"
})
```

### 3. Win, Decision, Insight Ekle (dashboard'u besle)

```json
mcp_agencyos_update_strategy({
  appendWin: {win: "Başarı açıklaması", metric: "Ölçülebilir sonuç"},
  appendDecision: {decision: "Karar", rationale: "Gerekçesi"},
  appendCustomerInsight: {insight: "İçgörü", source: "Kaynak"}
})
```

### 4. Eksik API Key'leri Bağla

```json
mcp_agencyos_set_user_secret({key: "GEMINI_API_KEY", value: "..."})
```

Kritik key'ler: GEMINI_API_KEY (ücretsiz, embedding için), APIFY_API_TOKEN (scraping).

### 5. Doğrula

```json
mcp_agencyos_get_memory_dashboard  → liveStatus: "live"
mcp_agencyos_get_setup_status      → 6/6 (%100)
```

## Mevcut Durum (10.08.2026)

| Alan | Değer |
|------|-------|
| Marka | ErgeneAI |
| Niş | Dental & Sağlık |
| Hedef | ₺50.000 MRR |
| North Star | Bilal'in aylık gelirini ₺50.000 MRR seviyesine çıkarmak |
| Kitle | Bursa/Mudanya küçük işletmeleri (diş, kuaför, otel, restoran) |
| Lead | 50 (100% skorlanmış) |
| Outreach | 4 aktif |
| API | Gemini ✅ · Apify ✅ |
| Setup | 6/6 (%100) |
| Klinika | İlk demo: Devadent (kag-msn7zc9b-fh48cy, kod: 959VX) |
| Dashboard | http://localhost:3091/#map (Tailscale) |
| Cron | 16 adet (13 no_agent, 3 agent) — detay: `references/cron-optimizasyonu-10-08.md` |

## Notlar

- AgencyOS = web dashboard. Hermes/Jeff 3.0 = asıl işletim sistemi.
- Dashboard görsel takip için, Hermes otonom operasyon için.
- Mert'in "Agentic OS" videosundaki sistemin bizdeki karşılığı AgencyOS.
- Gemini key olmadan embedding çalışmaz → JARVIS ses özelliği çalışmaz.
- Klinika = Mert'in "$5K dijital çalışan" modelinin birebir uygulaması.
- İlk Klinika demo akışı: `references/klinika-demo-flow.md`
