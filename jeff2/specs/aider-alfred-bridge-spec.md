# Aider ↔ Jeff ↔ Alfred Entegrasyon Köprüsü — Teknik Spec v1.0

## 🎯 Amaç
Jeff (sunucu, 13.140.183.88), Alfred (yerel Windows, Tailscale 100.89.26.86) ve Aider CLI
arasında kesintisiz, çift yönlü görev ve sonuç iletişimi sağlamak.

## 🏗️ Mimari

```
Bilal (A2A / Telegram)
        │
        ▼
   Jeff (Sunucu)
   ├── Aider CLI (http://127.0.0.1:8999/v1 — Antigravity Proxy)
   └── Bridge API (FastAPI, :7700)
              │
              │  HTTP REST (:7700)
              ▼
   Alfred (Windows, 100.89.26.86)
   └── Alfred Bridge Client (polling + webhook)
```

## 📦 Bileşenler

### 1. Jeff Bridge API — `/home/hermes/jeff_repo/jeff2/bridge/jeff_bridge_api.py`
FastAPI servisi, sunucuda `http://127.0.0.1:7700`, dışarıdan `http://13.140.183.88:7700` adresinde.

**Endpoint'ler:**
- `POST /aider/task` — Yeni Aider görevi kuyruğa ekle
  - Body: `{task_id, prompt, files[], priority, source}`
  - Response: `{task_id, status: "queued"}`
- `GET /aider/task/{task_id}` — Görev durumu ve sonucu
  - Response: `{task_id, status, result, error, started_at, finished_at}`
- `POST /alfred/result` — Alfred'den gelen sonuç/onay webhook'u
  - Body: `{task_id, type, result, screenshot_b64?, timestamp}`
- `GET /alfred/tasks` — Alfred'in işlemesi gereken bekleyen görevler (polling)
  - Response: `{tasks: [{task_id, type, payload, created_at}]}`
- `POST /alfred/heartbeat` — Alfred'in canlılık sinyali
  - Body: `{agent: "alfred", status, version, timestamp}`
- `GET /health` — Servis sağlığı
  - Response: `{status: "ok", aider_ready, alfred_online, queued_tasks}`

**Özellikler:**
- SQLite DB: `/home/hermes/jeff_repo/jeff2/bridge/bridge.db` (tasks, alfred_events tabloları)
- Aider görevleri async subprocess ile çalışır (asyncio + subprocess)
- Alfred 60 saniyedir heartbeat göndermemişse `alfred_online: false`
- Tüm olaylar audit log'a yazılır: `/home/hermes/jeff_repo/jeff2/bridge/bridge.log`

### 2. Aider Runner — `/home/hermes/jeff_repo/jeff2/bridge/aider_runner.py`
Görev kuyruğunu işleyen arka plan worker.

**İşleyiş:**
- Her 5 saniyede DB'de `status=queued` görev var mı kontrol et
- Varsa: `aider --model openai/claude-3-5-sonnet-latest --message "{prompt}" {files} --yes --no-auto-commits`
- Env: `OPENAI_API_BASE=http://127.0.0.1:8999/v1`, `OPENAI_API_KEY=antigravity`
- stdout/stderr'i yakala, DB'ye yaz (`status=done` veya `status=error`)
- Timeout: 300 saniye
- Eş zamanlı max 2 görev

### 3. Alfred Bridge Client — `/home/hermes/jeff_repo/jeff2/bridge/alfred_client.py`
Alfred (Windows) tarafında çalışacak Python client scripti.

**İşleyiş:**
- Her 10 saniyede `GET http://13.140.183.88:7700/alfred/tasks` poll et.
- Bekleyen görev varsa işle:
  - `WHATSAPP_DRAFT`: Konsola yaz + dosyaya kaydet (onay sonrası Alfred gönderir)
  - `SCREENSHOT_REQUEST`: Ekran görüntüsü al, base64 encode, `POST /alfred/result`'a gönder
  - `AIDER_RESULT_NOTIFY`: Aider tamamlandı bildirimi — Telegram'a ilet veya log'a yaz
  - `BROWSER_ACTION`: URL aç (webbrowser.open)
- Her 30 saniyede `POST http://13.140.183.88:7700/alfred/heartbeat` gönder
- Bağlantı kesilirse 5 saniye bekle, tekrar dene (sonsuz retry)
- Log: `%USERPROFILE%\.hermes\alfred_bridge.log`

### 4. Systemd Servis — `/etc/systemd/system/jeff-bridge.service`
Jeff Bridge API'yi otomatik başlat/yeniden başlat.

```ini
[Unit]
Description=Jeff-Alfred-Aider Bridge API
After=network.target

[Service]
Type=simple
User=hermes
WorkingDirectory=/home/hermes/jeff_repo/jeff2/bridge
ExecStart=/home/hermes/.venv/bin/python /home/hermes/jeff_repo/jeff2/bridge/jeff_bridge_api.py
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

## 🔐 Güvenlik
- API key header zorunlu: `X-Bridge-Key: cybergene-bridge-2026`
- Dış uç `http://13.140.183.88:7700` için kimlik doğrulama ve ağ erişim kuralları zorunlu.
- Alfred heartbeat olmadan görev gönderme (uyarı ver)

## 📋 Dosya Yapısı
```
/home/hermes/jeff_repo/jeff2/bridge/
├── jeff_bridge_api.py     # FastAPI ana servis
├── aider_runner.py        # Aider task worker
├── alfred_client.py       # Alfred tarafı client (Windows'a kopyalanır)
├── bridge.db              # SQLite görev DB'si
├── bridge.log             # Audit log
└── requirements.txt       # fastapi, uvicorn, aiosqlite
```

## ✅ Başarı Kriterleri
1. `GET /health` → `{"status":"ok","aider_ready":true,"alfred_online":true}`
2. `POST /aider/task` → Aider çalışır, sonuç DB'ye yazılır
3. Alfred client poll eder → görevi alır → heartbeat gönderir
4. Servis crash olursa systemd 5 saniyede yeniden başlatır
5. Tüm olaylar bridge.log'a yazılır (timestamp + task_id + status)
