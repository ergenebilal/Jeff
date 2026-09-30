# 🏭 Jeff 2.0 — Tam Envanter Raporu
**Tarih:** 23 Temmuz 2026 — 22:40 UTC+3
**Kapsam:** Hermes Agent + Jeff 2.0 + Hizmet Motoru + Worker'lar
**Maliyet:** ~$0.00/ay (tüm worker'lar opencode-go üzerinde)

---

## 1. 🏗️ Jeff 2.0 — Otonom İşletim Sistemi

### 1.1. Dizin Yapısı

```
/home/hermes/jeff2/
├── SOUL.md                    (v2.1 — Anayasa, 1849 byte)
├── README.md                  (Hızlı başlangıç)
├── departments/               (5 departman charter'ı)
│   ├── BUYUME_YONETICISI.md        [Büyüme]
│   ├── URUN_VE_ICERIK_YONETICISI.md [Ürün & İçerik]
│   ├── TESLIMAT_VE_SISTEM_YONETICISI.md [Teslimat & Sistem]
│   ├── FINANS_VE_RISK_YONETICISI.md [Finans & Risk]
│   └── HAFIZA_VE_OGRENME_YONETICISI.md [Hafıza & Öğrenme]
├── engines/                   (4 gelir motoru)
│   ├── HIZMET_MOTORU.md
│   ├── FIRSAT_DENEY_MOTORU.md
│   ├── ICERIK_VE_TALEP_MOTORU.md
│   └── DIJITAL_URUN_MOTORU.md
├── governance/                (Verifier kapısı)
│   └── WORKER_RELABEL.md
├── workers/                   (Worker atama planı)
│   └── WORKER_RELABEL.md
├── reports/                   (Rapor şablonları + üretilen raporlar)
│   ├── GUNLUK_RAPOR.md        (şablon)
│   ├── HAFTALIK_RAPOR.md      (şablon)
│   ├── AYLIK_RAPOR.md         (şablon)
│   └── HAFTALIK_RAPOR_20260723.md (✅ ilk rapor)
└── hq/                        (Hizmet Motoru — canlı sistem)
    ├── hizmet_motoru_cron.py         (günlük tarama cron'u)
    ├── app.py                        (ana uygulama)
    ├── lead_enrich.py                (lead zenginleştirme)
    ├── lead_merge.py                 (lead birleştirme)
    ├── feed.jsonl                    (pipeline — 206 lead)
    ├── tasks.jsonl                   (21 task kaydı)
    ├── task_queue.jsonl              (iş kuyruğu)
    ├── emirler.jsonl                 (2 emir kaydı)
    ├── api_call_log.jsonl            (API çağrı logları)
    ├── ledger.jsonl                  (muhasebe kaydı)
    ├── decisions.jsonl               (karar günlüğü)
    ├── lessons_registry.jsonl        (öğrenilen dersler)
    ├── circuit_breaker_state.jsonl   (devre kesici durumu)
    ├── auto_remediate_log.jsonl      (otomatik düzeltme)
    ├── retry_log.jsonl               (tekrar deneme logları)
    ├── subagent_results.jsonl        (subagent sonuçları)
    ├── personal_update_log.jsonl     (güncelleme logu)
    ├── charters/                     (bakan charter'ları)
    │   ├── hirsli.md    [Büyüme Bakanı]
    │   ├── estetik.md   [İçerik Bakanı]
    │   ├── pragmatik.md [Sistem Bakanı]
    │   ├── maliyetci.md [Hazine Bakanı]
    │   ├── bilge.md     [Arşiv Bakanı]
    │   ├── protokol.md  [Protokol]
    │   └── subagent_sop.md (çalışma SOP'u)
    ├── static/                       (27 spec belgesi)
    │   ├── HERMES_ENVANTER_RAPORU.md
    │   ├── HERMES_KOD_MIMARISI.md
    │   ├── JEFF_AMELIYAT_ENVANTERI.md
    │   ├── SPEC_*.md (24 adet — bakınız bölüm 8)
    ├── sops/                         (Standart Operasyon Prosedürleri)
    │   ├── lead-enrichment-pipeline.md
    │   └── whatsapp-telefon-outreach.md
    ├── templates/
    │   └── dashboard.html
    └── static/ (devam)
        ├── memory_archive.md
        └── KARAR_EMAIL_ENRICHMENT.md
```

### 1.2. 5 Departman

| Departman | Yönetici | İşçi Sayısı | Hedef |
|-----------|----------|-------------|-------|
| **Büyüme** | outreach | 6 | Lead akışı, outbound/inbound, fırsat keşfi |
| **Ürün ve İçerik** | — | 4 | Dijital ürün, görsel+metin, içerik takvimi |
| **Teslimat ve Sistem** | kodcu | 3 | Kod, deploy, altyapı, otomasyon |
| **Finans ve Risk** | analyst | 3 | Marj, maliyet, risk, token limit |
| **Hafıza ve Öğrenme** | master | 3 | SOP, içgörü, desen kaydı, arşiv |

> Tüm departman charter'ları yazılmış ve board'da **done** durumunda.

### 1.3. 4 Gelir Motoru

| Motor | Durum | Worker | Üretim |
|-------|-------|--------|--------|
| **Hizmet Motoru** | ✅ Aktif (cron: günlük 08:00) | kodcu | 206 lead pipeline |
| **Fırsat Deney Motoru** | ✅ İlk task tamam | kesif | Hipotez + deney tasarımı hazır |
| **İçerik ve Talep Motoru** | ✅ İlk task tamam | master | 10+ post konsepti hazır |
| **Dijital Ürün Motoru** | 🔄 İlk task running | master | Worker çalışıyor, sonuç bekleniyor |

### 1.4. Kabine (Hizmet Motoru Subagent'ları)

| Bakan | Charter | Görev |
|-------|---------|-------|
| **Hırslı** 📈 | `charters/hirsli.md` | Büyüme Bakanı — lead avcısı, fırsat kovalyıcı |
| **Estetik** 🎨 | `charters/estetik.md` | İçerik Bakanı — görsel + metin üretimi |
| **Pragmatik** ⚙️ | `charters/pragmatik.md` | Sistem Bakanı — altyapı, cron, deploy |
| **Maliyetçi** 💰 | `charters/maliyetci.md` | Hazine Bakanı — token, maliyet, marj |
| **Bilge** 🧠 | `charters/bilge.md` | Arşiv Bakanı — hafıza, SOP, öğrenme |

---

## 2. 🤖 Hermes Agent — Sistem Yapısı

### 2.1. Temel Konfigürasyon

| Parametre | Değer |
|-----------|-------|
| **Sürüm** | v0.12.0+ (Nous Research) |
| **Host** | Ubuntu 22.04 @ 13.140.183.88 |
| **Python** | 3.10.12 (sistem) / 3.11 + 3.12 (gateway'ler) |
| **Config** | `/home/hermes/.hermes/config.yaml` (16KB, 693 satır) |
| **Provider** | OpenCode Zen (deepseek-v4-flash) |
| **Maliyet** | $0.00/ay (ücretsiz opencode-go endpoint) |

### 2.2. Gateway (Çalışma Süreçleri)

| Process | PID | Başlangıç | Çalışma Süresi |
|---------|-----|-----------|----------------|
| **Gateway (python3.11)** | 2770144 | 16 Temmuz | 7 gündür aktif |
| **Gateway (python3.12)** | yeni session | 22:32 | Bu oturumda başlatıldı |

> Config'de `dispatch_in_gateway: true` → dispatcher gateway içinde çalışır, ayrı process gerekmez.

### 2.3. Worker Profilleri (6 adet)

| Profil | state.db | Görev | Son Aktivite |
|--------|----------|-------|-------------|
| **master** | 4.8 MB | Strateji, kalite, self-improvement | 23.07.2026 |
| **kesif** | 3.9 MB | Araştırma, fırsat keşfi | 23.07.2026 |
| **outreach** | 3.2 MB | Lead tarama, outbound | 23.07.2026 |
| **analyst** | 3.4 MB | Token, maliyet, rapor | 23.07.2026 |
| **scraper** | 2.2 MB | Web scraping, lead toplama | 23.07.2026 |
| **kodcu** | 1.1 MB | Kod, deploy, altyapı | 23.07.2026 |
| **Toplam** | **18.7 MB** | | |

> Tüm profiller `opencode-go` provider'ını kullanır. Her profil kendi state.db'sinde session geçmişini tutar.

### 2.4. Veritabanları

| Dosya | Boyut | İçerik |
|-------|-------|--------|
| `kanban.db` (ana) | 168 KB | Ana board task'leri (13 task, tümü done) |
| `kanban/boards/jeff/kanban.db` | — | Jeff board task'leri (19 task) |
| `state.db` | 361 MB | Hermes ana durum veritabanı |
| `personal_memory.yaml` | 2.2 KB | Kullanıcı profili ve tercihler |
| `sessions.db` | — | Session geçmişi (FTS5 indeksli) |
| `auth.json` | 5.5 KB | Platform auth token'ları |

---

## 3. 📋 Kanban Board Durumu

### 3.1. Jeff Board (19 Task)

| Task | Worker | Durum |
|------|--------|-------|
| **Gelir Motorları** | | |
| Hizmet Motoru | outreach | ✅ done |
| Fırsat Deney Motoru | kesif | ✅ done |
| İçerik ve Talep Motoru | master | ✅ done |
| Dijital Ürün Motoru | — | 🔄 ready |
| **Motor İlk Task'leri** | | |
| Hizmet Motoru Cron Aktivasyonu | kodcu | ✅ done |
| Fırsat Havuzu + Deney Tasarımı | kesif | ✅ done |
| İçerik Araştırma + Fikir Havuzu | kesif | ✅ done |
| İlk Dijital Ürün Konsepti | master | 🔄 **running** |
| **Departmanlar** | | |
| Büyüme Departmanı | outreach | ✅ done |
| Ürün ve İçerik Departmanı | default | ✅ done |
| Teslimat ve Sistem Departmanı | kodcu | ✅ done |
| Finans ve Risk Departmanı | analyst | ✅ done |
| Hafıza ve Öğrenme Departmanı | master | ✅ done |
| **Rutin Task'ler** | | |
| Haftalık Lead Taraması | outreach | ✅ done |
| Token Muhasebesi Raporu | analyst | ✅ done |
| Skill Library Auditi | master | ✅ done |
| Mudanya Yeni Niş Araştırması | kesif | ✅ done |
| Lead Scraping — Bursa Kobi | scraper | ✅ done |
| Haftalık Self-Improvement Review | master | ✅ done |

```
Özet: 17 done · 1 running · 1 ready
```

### 3.2. Ana Board (13 Task)

- 13 task, tümü **done** durumunda
- Assignee'ler: default (7), izci (2), worker (3), finder (1)
- Zombi/blocked task'ler temizlenmiştir

---

## 4. ⏰ Otomasyon & Cron'lar

### 4.1. Crontab (Sistem)

| Zaman | Görev | Süre |
|-------|-------|------|
| `0 2 * * *` | n8n SQLite backup | Her gün 02:00 |
| `*/10 * * * *` | Google token refresh | 10 dakikada bir |
| ~~`0 8 * * *`~~ | **Hizmet Motoru cron** | Her gün 08:00 |

### 4.2. Hermes Cron'ları (Agent)

| Zaman | Görev | Worker | Skill |
|-------|-------|--------|-------|
| Her Pazartesi 09:00 | **Haftalık Jeff Raporu** | master | gsd |
| Her Pazartesi 10:00 | **Haftalık Lead Taraması** | outreach | lead-stratejisti |
| Her Pazartesi 12:00 | **Token Dashboard** | no-agent script | — |

### 4.3. Hermes Script'leri (116 Adet)

Kritik olanlar:

| Script | Görev |
|--------|-------|
| `token-dashboard.sh` | Haftalık token + worker metrik raporu (no-agent) |
| `hizmet_motoru_cron.py` | Günlük pipeline taraması |
| `kanban_zombie_check.py` | Zombie task temizliği |
| `lead-analyzer.py` | Lead analizi ve skorlama |
| `lead-stratejisti.py` | Lead stratejisi |
| `jeff_self_improve.py` | Self-improvement döngüsü |
| `jeff_guardian.py` | Sistem gözetimi |
| `jeff_briefing.py` | Günlük brifing |
| `semantic_memory.py` | Semantik hafıza yönetimi |
| `consolidate_memory.py` | Memory konsolidasyonu |
| `token_guard.py` | Token limit koruması |
| `sales-pipeline.py` | Satış pipeline yönetimi |
| `brain-state-wrapper.sh` | Beyin durumu yönetimi |
| `gateway-healthcheck.sh` | Gateway sağlık kontrolü |
| `hermes-watchdog.sh` | Hermes watchdog |

---

## 5. 📚 Skill Kütüphanesi

### 5.1. Aktif Skill'ler (38 Kategori)

```
agent-orchestration/       — Agent orchestration & handoff
apify-lead-generation/     — Apify ile lead toplama
autonomous-ai-agents/      — Otonom AI agent geliştirme
business/                  — İş geliştirme
creative/                  — Yaratıcı içerik
data-science/              — Veri bilimi
devops/                    — DevOps (n8n-ops, docker, setup, ai-coding-agents)
dijital-urun-gelistirme/   — Dijital ürün geliştirme
email/                     — Email stratejileri
gemini-vision/             — Gemini Vision entegrasyonu
github/                    — GitHub workflow
google-drive-backup/       — Drive yedekleme
gsd/                       — Get-Shit-Done metodolojisi
hermes-autonomy-framework/ — Hermes otonomi çerçevesi
jeff/                      — Jeff orchestration
marketing/                 — Pazarlama
media/                     — Medya üretimi
mlops/                     — MLOps
monitoring/                — Monitoring
note-taking/               — Not alma
orchestration/             — Orchestration
product/                   — Ürün geliştirme
productivity/              — Verimlilik
quality-control/           — Kalite kontrol
research/                  — Araştırma
research-and-web/          — Web araştırması
self/                      — Self skill'leri
self-improvement/          — Kendini geliştirme
skill-authoring/           — Skill yazarlığı
social-media/              — Sosyal medya
system/                    — Sistem yönetimi
thinking-and-docs/         — Düşünme ve dokümantasyon
voice/                     — Ses
web/                       — Web
health-fitness-coach/      — Sağlık
hedef-akisi-protokolu/     — Hedef akışı
smart-home/                — Akıllı ev
apple/                     — Apple ekosistemi
```

### 5.2. Arşiv Skill'ler (12 Adet)

| Skill | Arşiv Tarihi |
|-------|-------------|
| 30x-growth-marketing-panel | 23.07.2026 |
| canva-api | 29.06.2026 |
| devops-gumroad | 23.07.2026 |
| devops-mcp-servers | 23.07.2026 |
| devops-social-media-automation | 23.07.2026 |
| event-notifier | 29.06.2026 |
| instagram-automation | 29.06.2026 |
| platform-audit | 29.06.2026 |
| satis-ve-positioning | 29.06.2026 |
| video-production | 29.06.2026 |
| yerel-isletme-web | 29.06.2026 |

### 5.3. Skill Bundle'lar (4 Adet)

| Bundle | İçerik |
|--------|--------|
| `dev-ops.yaml` | DevOps skill'leri |
| `content-production.yaml` | İçerik üretimi |
| `lead-campaign.yaml` | Lead kampanyaları |
| `system-ops.yaml` | Sistem operasyonları |

---

## 6. 🔌 MCP Sunucular & Entegrasyonlar

### 6.1. MCP Sunucuları

| Entegrasyon | Kullanım |
|-------------|----------|
| **AgencyOS** | CRM, lead yönetimi, pipeline, autopilot |
| **Google Workspace** | Drive, Gmail, Calendar, Docs, Sheets, Slides, Chat |
| **n8n** | Workflow otomasyonu (node'lar, workflow'lar) |
| **NotebookLM** | Araştırma, notebook, podcast, video |
| **Crawl4AI** | Web scraping, içerik çekme |
| **Playwright** | Browser otomasyonu |
| **X API** | Twitter/X içerik ve arama |
| **Fal.ai** | Görsel üretim (FLUX, Stable Diffusion) |
| **Figma** | Tasarım dosyası okuma |
| **Google Analytics** | Web analitiği |
| **Google Maps** | Maps API dokümantasyonu |
| **Context7** | Dokümantasyon sorgulama |
| **AgentMemory** | Hafıza yönetimi (actions, signals, sessions) |

### 6.2. Plugin'ler (6 Adet)

| Plugin | Durum |
|--------|-------|
| `mem0-selfhosted` | ✅ Yüklü |
| `agentmemory` | ✅ Yüklü |
| `yantrikdb` | ✅ Yüklü |

---

## 7. 📊 Hizmet Motoru — Canlı Sistem

### 7.1. Pipeline Durumu

| Metrik | Değer |
|--------|-------|
| **Toplam lead kaydı** | 206 |
| **Kritik lead** | 0 |
| **Task kaydı** | 21 |
| **Emir kaydı** | 2 |
| **API çağrı log'u** | Var |
| **Otomatik düzeltme** | Aktif |
| **Devre kesici** | 3 bakan için closed |

### 7.2. Devre Kesici (Circuit Breaker) Durumu

| Bakan | Durum | Hata Sayısı |
|-------|-------|-------------|
| Hafıza | ✅ Kapalı | 0 |
| Hunter | ✅ Kapalı | 0 |
| WhatsApp | ✅ Kapalı | 0 |

### 7.3. Öğrenilen Dersler (Lessons Registry)

| Konu | Durum | Özet |
|------|-------|------|
| feed format | ✅ active | Feed mesajları max 200 karakter, emoji+sonuç |
| hafıza birleştirme | ✅ resolved | %95 → %58, haftalık bakım gerekli |
| buyume cb open | ✅ active | Büyüme circuit breaker 5dk bloke |

---

## 8. 📄 HQ Spec'leri (27 Adet)

| Spec | İçerik |
|------|--------|
| `SPEC_PRAGMATIK_GERCEK_SUBAGENT.md` | Sistem Bakanı subagent tasarımı |
| `SPEC_BILGE_HAFTALIK_HAFIZA_BAKIMI.md` | Hafıza bakım prosedürü |
| `SPEC_BAKANLAR_GERCEK_SUBAGENT.md` | Bakan subagent'ları |
| `SPEC_DIS_ENTEGRASYON_HAZIRLIK.md` | Dış entegrasyon hazırlığı |
| `SPEC_CAPRAZ_KONTROL_OTOMASYONU.md` | Çapraz kontrol otomasyonu |
| `SPEC_SELF_IMPROVEMENT_LOOP.md` | Self-improvement döngüsü |
| `SPEC_KPI_ALARM_ESIK_SERTLESTIRME.md` | KPI alarm eşikleri |
| `SPEC_KARAR_GUNLUGU.md` | Karar günlüğü standardı |
| `SPEC_KABINE_STABILIZASYONU.md` | Kabine stabilizasyonu |
| `SPEC_AGENTMEMORY_CONSOLIDATION_RECOVERY.md` | Memory kurtarma |
| `SPEC_MALIYETCI_GERCEK_SUBAGENT.md` | Maliyetçi subagent |
| `SPEC_OLCEK_VE_GUVENILIRLIK.md` | Ölçek ve güvenilirlik |
| `SPEC_KISISEL_SOSYAL_HAFIZA.md` | Kişisel sosyal hafıza |
| `SPEC_KABINE_CONTEXT_KERNEL.md` | Kabine context kernel |
| `SPEC_ESTETIK_GERCEK_SUBAGENT.md` | Estetik subagent |
| `SPEC_BILGE_GERCEK_SUBAGENT.md` | Bilge subagent |
| `SPEC_SOP_UYUM_COST_LOGGING.md` | SOP uyum ve maliyet log |
| `SPEC_MEMORY_HIJYENI_CHARTER_SENKRONIZASYONU.md` | Memory hijyeni |
| `SPEC_LESSON_PIPELINE_OTOMASYONU.md` | Lesson pipeline |
| `SPEC_PROAKTIF_KARAR_MEKANIZMASI.md` | Proaktif karar mekanizması |
| `SPEC_0500_BRIFING_OTOMASYONU.md` | 05:00 brifing otomasyonu |
| `SPEC_AGENTMEMORY_OTOMATIK_KAYIT.md` | Otomatik memory kaydı |
| `HERMES_ENVANTER_RAPORU.md` | Önceki envanter raporu |
| `HERMES_KOD_MIMARISI.md` | Kod mimarisi dokümanı |
| `JEFF_AMELIYAT_ENVANTERI.md` | Ameliyat envanteri |
| `KARAR_EMAIL_ENRICHMENT.md` | Email enrichment kararı |
| `memory_archive.md` | Memory arşivi |

---

## 9. 🔐 Auth & Bağlantılar

| Bağlantı | Durum |
|----------|-------|
| **Telegram Gateway** | ✅ Bağlı |
| **CLI Gateway** | ✅ Çalışıyor |
| **API Server** | ✅ Bağlı |
| **Google Workspace** | ✅ OAuth token mevcut (auto-refresh) |
| **n8n** | ✅ Docker'da çalışıyor (günlük backup) |
| **NotebookLM** | ⚠️ Auth gerekiyor |
| **AgencyOS** | ✅ API token mevcut |
| **OpenCode** | ✅ Ücretsiz endpoint kullanımda |
| **Playwright** | ✅ Browser headless çalışıyor |
| **AgentMemory** | ✅ Node process çalışıyor (212 saat) |

---

## 10. 💰 Maliyet Özeti

| Kalem | Değer |
|-------|-------|
| **AI Maliyeti (son 24h)** | ~$0.00 |
| **AI Maliyeti (son 7g)** | ~$0.001 |
| **Worker Maliyeti (6 profil)** | $0.00 (opencode-go) |
| **Gateway Maliyeti** | $0.00 (VPS) |
| **Storage** | ~$0.00 (VPS dahil) |
| **Apify** | Kullanıcının BYOK hesabı |
| **Aylık Toplam** | **~$0.00** |

---

## 11. ⚡ Hızlı Özet Tablosu

| Kategori | Adet | Detay |
|----------|------|-------|
| **Jeff departman** | 5 | Tümü done |
| **Gelir motoru** | 4 | 3 done, 1 running |
| **Jeff task** | 19 | 17 done · 1 running · 1 ready |
| **Ana board task** | 13 | 13 done |
| **Worker profil** | 6 | master, kesif, outreach, analyst, scraper, kodcu |
| **Worker state** | 18.7 MB | Toplam session geçmişi |
| **Cron (sistem)** | 3 | n8n backup, google token, hizmet motoru |
| **Cron (hermes)** | 3 | rapor, lead tarama, dashboard |
| **Skill (aktif)** | 38 kategori | ~80+ bireysel skill |
| **Skill (arşiv)** | 12 | Zamanla arşivlenmiş |
| **Script** | 116 | Hermes scripts/ dizininde |
| **HQ spec** | 27 | Sistem dokümantasyonu |
| **Pipeline** | 206 lead | Hizmet Motoru üzerinde |
| **MCP entegrasyon** | 14+ | AgencyOS, Google, n8n, NotebookLM vb. |
| **Maliyet** | ~$0.00/ay | opencode-go + VPS |
| **Gateway uptime** | 7+ gün | Kesintisiz çalışma |

---

## 12. 🔮 Sıradaki Adımlar

| # | Aksiyon | Worker | Öncelik |
|---|---------|--------|---------|
| 1 | Dijital Ürün Konsepti tamamlansın | master | 🔴 Şu an running |
| 2 | İlk gelir sinyali (Hizmet Motoru üzerinden) | outreach | 🔴 Kritik |
| 3 | Lead pipeline 50+ hedef | outreach | 🟡 Yüksek |
| 4 | Self-improvement döngüsü (haftalık) | master | 🟢 Rutin |
| 5 | Token dashboard (Pazartesi) | no-agent | 🟢 Rutin |
| 6 | Lead tarama (Pazartesi) | outreach | 🟢 Rutin |
| 7 | Jeff raporu (Pazartesi) | master | 🟢 Rutin |

---

*Rapor otomatik oluşturulmuştur. Son güncelleme: 23.07.2026 22:40 UTC+3*
