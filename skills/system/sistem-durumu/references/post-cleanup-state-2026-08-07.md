# Sistem Durumu — 07.08.2026 Derin Temizlik Sonrası

## Temizlik Özeti

| Kategori | Önce | Sonra |
|----------|------|-------|
| Python process | 32 | 17 |
| Cron jobs | 25 | 16 |
| Docker containers | ~20 image | 12 running |
| Disk | 57% | 49% |
| Jeff 3.0 | 7 process | DURDURULDU |
| Systemd services | 11 | 2 (health-mcp + hq) |

## Silinen Process'ler (18)
Jeff 3.0 (7), chat_backend, http.server:8081, mail-webhook-server, campaign-app, finans-app(2), gadgetbridge, hf_server, hf_api_server, browser_worker, token_muhasebe_worker

## Disable Edilen Systemd Servisler (5)
hermes-browser-worker, hermes-token-muhasebe, hermes-hf-api, hermes-gadgetbridge, hermes-figma-mcp

## Silinen Dizinler (14)
jeff_v2_backup_monolithic, jeff_v2_backup_20260712, flight-bot, instagram-pipeline-multi, test-output, brain_eski, trend-watcher, infographic, website, apps, ui-tui, mobile, node_modules(/opt/hermes), video.mp4

## Boşaltılan Cache
- pip: 8.4GB
- HuggingFace models: 4.3GB
- Docker unused: 3.8GB
- **Toplam: ~25GB disk kazanıldı**

## Kalan Çekirdek
- Gateway (8642), Health MCP (8768), HQ (8889)
- AgencyOS Bridge, NotebookLM MCP
- 12 Docker: n8n, crawl4ai, coolify(4), dograh, beszel(2), node, ergeneai-landing, pasarguard
- CRM: 50 lead, 0 outreach
- API: Sadece Apify aktif; Resend, Gemini, Apollo, Hunter EKSIK

## Jeff 3.0 Stabilizasyon
- jeff3_start.sh v2.0: PID dosyaları, double-start koruması, health komutu
- health_monitor.py: max 2 restart, kritik alarm
- autonomy_domains.json v2: 9 domain, 33 kural, 20 insan onaylı
- Supervisor: 7 servis STOPPED, başlatma Bilal onayında
