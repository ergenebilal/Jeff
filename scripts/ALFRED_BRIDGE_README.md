# Jeff <-> Alfred Bridge — Kurulum ve Kullanim

## Mimari

```
Jeff (Ubuntu 13.140.183.88)          Alfred (Windows 100.89.26.86)
─────────────────────────────        ─────────────────────────────
alfred_instant_bridge.py             alfred_daemon.py
  dispatch_task_to_alfred()   ──HTTP POST :7788/task──>  HTTP Server
  check_alfred_responses()    <─HTTP POST :7789/response─ send_response_to_jeff()

alfred_response_receiver.py          Outbox polling (fallback)
  POST /response  (port 7789)        ~/.hermes/alfred_bridge/outbox/
  Inbox'a kaydeder
```

## Transport Onceligi

1. HTTP (primary): Alfred online ise direkt HTTP POST
2. Dosya (fallback): Alfred offline ise outbox/ klasorune yazar, Alfred baslatilinca alir

## Jeff Tarafi Kurulum (Ubuntu — TAMAMLANDI)

Response receiver systemd servisi zaten aktif:

```bash
sudo systemctl status alfred-response-receiver
# Active: active (running)
```

## Alfred Tarafi Kurulum (Windows)

### 1. Dosyayi kopyala

`alfred_daemon.py` dosyasini Windows makinesine kopyala:
```
Hedef: C:\Users\<kullanici>\.hermes\alfred_bridge\ (veya istedigin yer)
```

### 2. Ortam degiskenlerini ayarla (opsiyonel)

```cmd
set TELEGRAM_BOT_TOKEN=<token>
set TELEGRAM_CHAT_ID=<chat_id>
set JEFF_HOST=13.140.183.88
```

### 3. Daemon'u baslatma

```cmd
python alfred_daemon.py
```

Arkaplanda calistirmak icin:
```cmd
pythonw alfred_daemon.py
```

Windows baslangicindan itibaren otomatik calistirmak icin Task Scheduler'a ekle:
- Program: `python`
- Arguman: `C:\path\to\alfred_daemon.py`
- Baslatma: "Oturum acildiginda"

### 4. Saglik kontrolu

```cmd
curl http://localhost:7788/health
# {"status": "ok", "agent": "alfred_daemon", "version": "2.0"}
```

## Test

Jeff tarafindan:
```bash
python3 ~/.hermes/scripts/test_alfred_bridge.py
```

## Desteklenen Gorev Tipleri

| Tip | Aciklama |
|-----|----------|
| PING | Baglanti testi — PONG doner |
| SCREENSHOT | Ekran goruntusu alir, inbox'a kaydeder |
| WHATSAPP_SEND | WhatsApp mesaji (placeholder — pyautogui ile genisletilebilir) |
| WHATSAPP_DRAFT | WHATSAPP_SEND ile ayni (v1 uyumlulugu) |
| TELEGRAM_REPORT | Telegram bot ile Jeff'e rapor gonderir |

## Gorev Gonderimi (Jeff'ten)

```python
from alfred_instant_bridge import dispatch_task_to_alfred, check_alfred_responses

# Gorev gonder
task_id = dispatch_task_to_alfred("PING", {"msg": "test"})

# Yanit kontrol
responses = check_alfred_responses()
```

## Portlar

| Port | Taraf | Aciklama |
|------|-------|----------|
| 7788 | Alfred (Windows) | Gorev alma HTTP server |
| 7789 | Jeff (Ubuntu) | Yanit alma HTTP server |

## Log Konumlari

- Jeff receiver: `journalctl -u alfred-response-receiver -f`
- Alfred daemon: stdout (calistirma terminali)
- Inbox: `~/.hermes/alfred_bridge/inbox/`
- Outbox: `~/.hermes/alfred_bridge/outbox/`
