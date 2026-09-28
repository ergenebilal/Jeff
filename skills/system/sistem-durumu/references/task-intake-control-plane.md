# Task Intake Control Plane — Optimization Layer

**Kurulum:** 01.08.2026 (Faz 1-3)
**Versiyon:** v2.0
**Port:** 8774 (internal)
**Process:** `python3.11 /home/hermes/.hermes/optimization/scripts/task_api.py` (background)

---

## Mimari

```
Cron / Telegram / n8n / HQ / Manuel
           │
           ▼
    Task Intake API v2 (127.0.0.1:8774)
           │
    ┌──────┼──────┐
    ▼      ▼      ▼
  Policy  State  Audit
  Guard   Machine (JSONL)
```

## API Endpoint'leri

| Method | Path | İşlev |
|--------|------|-------|
| POST | `/intake` | Görev oluştur (idempotency + digest) |
| POST | `/approve` | Atomik onay (claim + digest check + expiry) |
| POST | `/reject` | Reddet |
| POST | `/execute` | Çalıştır (queued veya approved → running) |
| POST | `/complete` | Doğrula + tamamla (running → verifying → completed) |
| POST | `/fail` | Başarısız (auto-retry → dead_letter) |
| POST | `/worker-lost` | Worker çöküşü (safe retry → dead_letter) |
| GET | `/queue` | Aktif kuyruk |
| GET | `/audit` | Son 100 denetim kaydı |
| GET | `/health` | API sağlık (uptime, version) |
| GET | `/expire` | Süresi dolanları temizle |
| GET | `/task/<id>` | Tekil task sorgulama |
| GET | `/panel` | HTML onay paneli |

## State Machine

```
queued → running → verifying → completed
queued → awaiting_approval → approved → running → ...
awaiting_approval → rejected | expired | cancelled
running → failed | dead_letter | rolled_back | retrying
failed → retrying → running | dead_letter
```

**Yasak geçişler:** completed → running, expired → approved, rejected → executing, approved → ikinci kez approved, dead_letter → otomatik retry

## Dış Etki → Onay Eşlemesi

| external_effect | Onay | Örnek |
|:---------------:|:----:|-------|
| none | ❌ | Araştırma, analiz, enrichment |
| draft | ❌ | CRM taslağı, mesaj taslağı |
| send | ✅ | DM, e-posta gönderimi |
| publish | ✅ | Sosyal medya yayını |
| deploy | ✅ | Deploy işlemi |
| delete | ✅ | Silme işlemi |
| spend | ✅ | Ödeme/harcama |
| credential_change | ✅ | API key/credential değişimi |

## Güvenlik Özellikleri

| Özellik | Açıklama |
|---------|----------|
| **Idempotency** | `idempotency_key` ile çift gönderim engellenir |
| **Task Digest** | SHA256 — onay sonrası içerik değişirse onay geçersiz |
| **Atomic Claim** | Aynı task iki kez onaylanamaz (already_claimed) |
| **Expiry** | 24 saat (varsayılan), süresi dolan otomatik expire |
| **Retry** | Max 3, sonrası dead_letter |
| **Worker Timeout** | 1 safe retry, sonrası dead_letter |

## Audit Formatı

```json
{
  "timestamp": "2026-08-01T20:31:04.309Z",
  "event": "created|approved|rejected|completed|failed|retry|duplicate_attempt|approval_conflict|approval_expired|approval_invalidated|worker_lost|execution_failed",
  "task_id": "task-xxxxxxxxxxxx",
  "detail": {}
}
```

## Pipeline'lar

### Dental Lead Pipeline
Script: `scripts/dental_pipeline.py`
7 aşama: Discovery → Enrichment → ICP → Verifier → CRM Draft → Outreach Draft → Send

```bash
DRY_RUN=true python3.11 scripts/dental_pipeline.py  # Test
DRY_RUN=false python3.11 scripts/dental_pipeline.py # Gerçek
```

## Adaptörler (KAPALI)

| Adaptör | Script | Aktif Etmek |
|---------|--------|------------|
| Telegram | `scripts/telegram_adapter.py` | `TELEGRAM_ADAPTER_ENABLED=true` |
| n8n | `scripts/n8n_adapter.py` | `N8N_ADAPTER_ENABLED=true` |

## Dizin Yapısı

```
~/.hermes/optimization/
├── scripts/
│   ├── task_api.py           # Ana API (background process)
│   ├── task_guard.py         # Policy guard
│   ├── health_check.py       # Sistem sağlık taraması
│   ├── dental_pipeline.py    # Dental pipeline orkestrasyonu
│   ├── telegram_adapter.py   # Telegram → Task Intake
│   ├── n8n_adapter.py        # n8n guard node
│   ├── test_suite.py         # Faz 2 testleri (6 test)
│   └── faz3_test_suite.py    # Faz 3 testleri (15 test)
├── hq/
│   └── approval-panel.html   # Onay paneli
├── tasks/                    # Task state klasörleri
│   ├── queued/
│   ├── awaiting_approval/
│   ├── approved/
│   ├── running/
│   ├── verifying/
│   ├── completed/
│   ├── failed/
│   ├── retrying/
│   ├── dead_letter/
│   ├── rejected/
│   ├── cancelled/
│   └── expired/
├── audit/
│   └── task-audit.jsonl      # Denetim logu
├── config/
│   └── faz3-integration.env.example
├── reports/
│   ├── faz3-integration-map.md
│   ├── faz3-implementation-report.md
│   └── dry-run/
└── runbooks/
    ├── FAZ3-ROLLBACK.md
    ├── DENTAL-PIPELINE-SOP.md
    ├── BACKUP-RESTORE.md
    └── REVENUE-ENGINE.md
```

## Başlatma/Durdurma

```bash
# Başlat
cd ~/.hermes/optimization && python3.11 scripts/task_api.py &

# Durdur
pkill -f "task_api.py"

# Sağlık kontrolü
curl -s http://127.0.0.1:8774/health

# Panel
http://127.0.0.1:8774/panel
```
