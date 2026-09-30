# Jeff (Hermes Agent) — Güncel Sistem Dökümü

**Tarih:** 7 Ağustos 2026 (derin temizlik sonrası)
**Denetleyen:** Hermes (sistem audit'i)
**Sunucu:** 13.140.183.88 — Contabo Cloud VPS
**Hermes:** v0.20.0 (2026.8.3)
**RAM:** 31 GB DDR4
**Disk:** 276 GB SSD (%49 dolu, 135 GB boş) — 07.08 temizlik sonrası
**CPU:** 4 vCPU Intel Xeon Platinum 8168 @ 2.70GHz
**OS:** Ubuntu 22.04.5 LTS

---

## 1. SİSTEM DURUMU (07.08.2026 — Derin Temizlik Sonrası)

| Metrik | Değer |
|--------|-------|
| **RAM** | 31 GB toplam, ~6.3 GB kullanım, ~19 GB free |
| **Disk** | 276 GB, %49 dolu (135 GB boş) — ~20 GB temizlendi |
| **Swap** | 8 GB |
| **Uptime** | 51 gün |
| **Load** | 1.08, 1.21, 1.36 |
| **Python process** | 17 (32'den düştü) |

## 2. HERMES & PYTHON (07.08.2026)

- **Versiyon:** v0.20.0 (2026.8.3)
- **Python:** 3.11.15 (kendi venv'i)
- **Kurulum:** shell installer (`~/.hermes/hermes-agent/`)

## 3. PROVIDER & MODEL

- **Birincil:** opencode-go → deepseek-v4-pro (ücretsiz)
- **Bakiye:** ~$3.77 (son log 26.06, token muhasebe durduruldu)

## 4. DOCKER (12 konteyner)

coolify, coolify-proxy, coolify-db, coolify-redis, coolify-realtime, coolify-sentinel, n8n, crawl4ai, ergeneai-landing, dograh, beszel, beszel-agent

## 5. KRON (16 adet — 07.08 temizlik sonrası)

8 hatalı cron silindi: sop002-haftalik-olcum, sop002-pazartesi-rapor, proaktif-intelligence-ai-sektor, proaktif-mcp-ekosistem, haftalik-lead-taramasi, haftalik-jeff-raporu, goal-scheduler, instagram-gunluk-post. Ayrıca ucuz-bilet-botu silindi.

## 6. PORT HARİTASI (07.08.2026)

| Port | Servis | Durum |
|------|--------|:-----:|
| 22 | SSH | ✅ |
| 80/443 | Traefik (Coolify) | ✅ |
| 3000 | Next.js (build) | ✅ |
| 5432 | PostgreSQL (Coolify) | ✅ |
| 5678 | n8n | ✅ |
| 6001-6002 | Coolify Realtime | ✅ |
| 6379 | Redis (Coolify) | ✅ |
| 8000 | Coolify | ✅ |
| 8090 | Beszel | ✅ |
| 8642 | Hermes API | ✅ |
| 8765 | Webhook | ✅ |
| 8889 | HQ (Kanban) | ✅ |
| 11235 | Crawl4AI | ✅ |
| 34524 | Tailscale | ✅ |
| 50051 | Coolify gRPC | ✅ |

**Kaldırılan portlar (07.08):** 8766, 8768, 8770, 8773, 8774, 8877, 49134 — hepsi durduruldu, systemd servisleri disable edildi.

## 7. ÇALIŞAN SYSTEMD SERVİSLERİ (2 adet)

| Servis | Durum |
|--------|:-----:|
| hermes-health-mcp | ✅ active |
| hermes-hq | ✅ active |

**Durdurulan (07.08):** hermes-browser-worker, hermes-token-muhasebe, hermes-hf-api, hermes-gadgetbridge, hermes-figma-mcp, hf-tools-server, hermes-embedding-daemon

## 8. DURDURULAN SÜREÇLER (07.08.2026)

18 process durduruldu: Jeff 3.0 (7 process), chat_backend, http.server:8081, mail-webhook, campaign-app, finans-app (2 kopya), gadgetbridge, hf_server+hf_api, browser_worker, token_muhasebe_worker. Kaynak: systemd servisleri + supervisor + binary rename.

## 9. TEMİZLENEN DİZİNLER (07.08.2026)

| Ne | Boyut |
|----|-------|
| Pip cache | 8.4 GB |
| HF model cache | 4.3 GB |
| Docker unused images | 3.8 GB |
| __pycache__ (25 dizin) | ~30 MB |
| mobile/ (React Native) | 371 MB |
| node_modules/ (opt) | 475 MB |
| jeff_v2_backup_* (2 adet) | 5.4 MB |

## 10. BİLİNEN SORUNLAR (07.08.2026)

1. **CRM pipeline ölü** — 50 lead var, 0 outreach, 0 email gönderilmiş
2. **Resend API key yok** — email gönderilemiyor
3. **Gemini API key yok** — enrichment yapılamıyor
4. **Agency kimliği bozuk** — "Airgene" / "Kuaför" olarak kayıtlı
5. **Token muhasebe durdu** — son log 26 Haziran
6. **IG pipeline pasif** — içerik üretimi durmuş
**Denetleyen:** Hermes (sistem audit'i)
**Sunucu:** 13.140.183.88 — Contabo Cloud VPS
**Hermes:** v0.19.0 (2026.7.20)
**RAM:** 32 GB DDR4
**Disk:** 280 GB SSD (%54 dolu, 122 GB boş)
**CPU:** 4 vCPU Intel Xeon Platinum 8168 @ 2.70GHz
**OS:** Ubuntu 22.04.5 LTS

---

## 1. SİSTEM DURUMU (01.08.2026)

| Metrik | Değer |
|--------|-------|
| **RAM** | 31 GB toplam, ~24 GB kullanım, ~5.7 GB available |
| **Disk** | 276 GB, %54 dolu (122 GB boş) |
| **Swap** | 8 GB, 562 MB kullanım |
| **Uptime** | 46 gün |
| **Load** | 0.82, 0.81, 1.01 |

## 2. HERMES & PYTHON (01.08.2026)

### Hermes
- **Versiyon:** v0.19.0 (2026.7.20) — up to date
- **Install:** pip, `/home/hermes/.local/lib/python3.12/site-packages`
- **Binary shebang:** `#!/usr/bin/python3.12` (⚠️ ama gateway systemd 3.11 ile çalışır)

### Python Ortamı
| Sürüm | Dosya | Kullanım |
|-------|-------|----------|
| **3.11.15** | `/usr/bin/python3.11` | Gateway systemd, tüm servisler, pip paketleri |
| 3.10.12 | `/usr/bin/python3.10` | Ubuntu 22.04 apt (dokunulmaz) |
| 3.12.13 | `/usr/bin/python3.12` | ⚠️ Mevcut ama aktif değil |

**KRİTİK KURAL:** `hermes --version` 3.12 gösterir ama gateway systemd 3.11 override eder. `hermes update` yapılırsa 3.12 aktifleşebilir → manuel 3.11'e geri döndür. 3.12 venv kurma.

### Gateway
- **systemd:** `hermes-gateway.service`
- **ExecStart:** `/usr/bin/python3.11 -m hermes_cli.main gateway run`
- **RAM:** ~2.4 GB (MemoryMax=5G)
- **`--replace` flag:** KALDIRILDI (kalıcı)
- **`drop_pending_updates`:** False (2 yerde)

### Servisler
| Servis | Durum | Port |
|--------|:-----:|------|
| hermes-gateway | ✅ active | 8642, 8765 |
| hermes-hq | ✅ degraded | 8889 |
| caddy | ❌ masked | — |

## 3. PROVIDER & MODEL (01.08.2026)

| Provider | Model | Maliyet | Not |
|----------|-------|:-------:|-----|
| **opencode-go** | deepseek-v4-flash | **$0** | Ana kanal — tüm profiller ve cron'lar |
| opencode-go | glm-5.2 / qwen3.7-max | $0 | Ağır iş için manuel `--model` override |
| DeepSeek API | deepseek-v4 | ~$0.50 | SADECE fallback |

- Vision: native (deepseek-v4-flash)
- Gemini API: ❌ (Generative Language API erişimi yok)
- Groq API: ❌ (tüm key'ler geçersiz)
- Günlük token maliyeti: $0

## 4. DOCKER CONTAINER'LAR (01.08.2026)

| Container | İmaj | Port | Durum |
|-----------|------|------|:-----:|
| coolify | 4.0.0 | 8000, 8443, 9000 | ✅ |
| coolify-proxy | traefik:v3.6 | 80, 443 | ✅ |
| coolify-db | postgres:15-alpine | 5432 | ✅ |
| coolify-redis | redis:7-alpine | 6379 | ✅ |
| coolify-realtime | 1.0.13 | 6001-6002 | ✅ |
| coolify-sentinel | 0.0.21 | — | ✅ |
| n8n | 2.22.2 | 5678 | ✅ |
| crawl4ai | latest | 11235 | ✅ |
| ergeneai-landing | custom | 80 (int) | ✅ |
| dograh | custom | — | ✅ (dokunulmaz) |
| beszel | latest | 8090 | ✅ |
| beszel-agent | latest | — | ✅ |

**Kaldırılan container'lar:** odysseus, searxng, ragflow-cpu, docker-mysql

## 5. KRON JOB'LAR (01.08.2026 — 21 adet)

### Günlük (5)
| Job | Zaman | Tip | Deliver |
|-----|-------|-----|---------|
| ceo-daily-check | 06:00 | no_agent | origin |
| jeff-sabah-brifingi | 08:30 | no_agent | origin |
| hermes-watchdog | 10:00 | no_agent | origin |
| gunluk-audit-ozeti | 23:59 | no_agent | local |
| google-tokens-watchdog | 60 dk | no_agent | local |

### Haftalık (13)
| Job | Zaman | Tip |
|-----|-------|-----|
| haftalik-dis-dunya-briefi | Pzt/Per 09:00 | LLM |
| haftalik-lead-taramasi | Pzt 10:00 | LLM |
| haftalik-jeff-raporu | Pzt 09:00 | LLM |
| rakip-monitoring | Pzt 10:00 | LLM |
| goal-scheduler | Pzt 07:00 | LLM |
| hizmet-motoru-durum | Pzt 11:00 | no_agent |
| sop002-haftalik-olcum | Pzr 23:59 | LLM |
| sop002-pazartesi-rapor | Pzt 08:30 | LLM |
| proaktif-intelligence-ai-sektor | Pzt 09:00 | LLM |
| proaktif-mcp-ekosistem | Çar 09:00 | LLM |
| token-dashboard-haftalik | Pzt 12:00 | no_agent |
| haftalik-session-prune | Pzt 03:00 | no_agent |
| dental-lead-gen | Sal/Cum 09:00 | LLM |

### Aylık — Kredi Kartı (3)
| Job | Zaman |
|-----|-------|
| kart-hatirlatma-denizbank | Her ay 9'u |
| kart-hatirlatma-yk-hepsiburada | Her ay 23'ü |
| kart-hatirlatma-yk-word-eko | Her ay 25'i |

### 01.08 Temizliği — Silinenler
- `Bilge Haftalık Hafıza Bakımı` — last_status=error
- `Sabah Brifingi — Birleşik Özet` — last_status=error
- `token-dashboard` — duplicate

## 6. PORT HARİTASI (01.08.2026)

| Port | Servis | Durum |
|------|--------|:-----:|
| 22 | SSH | ✅ |
| 80/443 | Traefik (Coolify) | ✅ |
| 3000 | Next.js (build) | ✅ |
| 5432 | PostgreSQL (Coolify) | ✅ |
| 5678 | n8n | ✅ |
| 6001-6002 | Coolify Realtime | ✅ |
| 6379 | Redis (Coolify) | ✅ |
| 8000 | Coolify | ✅ |
| 8090 | Beszel | ✅ |
| 8642 | Hermes API | ✅ |
| 8765 | Webhook | ✅ |
| 8766 | AgentMemory MCP | ❌ KAPALI |
| 8768 | Token Muhasebe | ✅ |
| 8770 | Token Worker | ✅ |
| 8773 | HF-API | ⚠️ Dinliyor ama cevap yok |
| 8877 | Browser Worker | ✅ |
| 8889 | HQ (Kanban) | ✅ degraded |
| 8892 | Dograh AI | ✅ |
| 9000-9001 | MinIO | ✅ |
| 11235 | Crawl4AI | ✅ |
| 34524 | Tailscale | ✅ |
| 49134 | AgentMemory (iii) | ✅ |
| 50051 | Coolify gRPC | ✅ |

## 7. HERMES PROFİLLERİ (6 adet)

| Profil | Amaç | Provider |
|--------|------|----------|
| default | Ana operasyon | opencode-go |
| outreach | Büyüme/lead | opencode-go |
| kodcu | Teslimat/kod | opencode-go |
| analyst | Finans/analiz | opencode-go |
| master | Hafıza/SOP | opencode-go |
| kesif | Discovery | opencode-go |
| scraper | Scraping | opencode-go |

## 8. ÖNEMLİ DİZİNLER

| Dizin | İçerik |
|-------|--------|
| `~/.hermes/` | Hermes ana dizin |
| `~/.hermes/skills/` | 40 skill klasörü |
| `~/.hermes/profiles/` | 6 profil |
| `~/.hermes/plugins/` | 5 plugin |
| `~/.hermes/cron/output/` | Cron log'ları |
| `/home/hermes/jeff_repo/` | Aktif Jeff deposu |
| `~/.mem0/` | Mem0 hafıza |
| `~/.agentmemory/` | AgentMemory |
| `~/.google-workspace-mcp/` | Google OAuth |
| `~/.jcode/` | jcode config |

## 9. BİLİNEN SORUNLAR (01.08.2026)

1. **HQ "degraded"** — embedding daemon kaldırıldığı için (normal, sorun değil)
2. **Python 3.12 kalıntısı** — dosya mevcut ama gateway 3.11 override ediyor
3. **HF-API (8773)** — dinliyor ama HTTP yanıt vermiyor, restart gerekebilir
4. **caddy.service** — maskelendi (Coolify traefik kullanıyor)
5. **DeepSeek bakiye** — $0.50, kritik eşik altı (önemsiz, opencode-go aktif)
