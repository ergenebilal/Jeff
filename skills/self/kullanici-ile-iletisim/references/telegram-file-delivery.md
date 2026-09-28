# Telegram Dosya Gönderimi

## Bot API ile Dosya Gönderme

Telegram'da dosya göndermek için Bot API `sendDocument` endpoint'i kullanılır.

### Gerekli Bilgiler

1. **Bot Token:** `/home/hermes/.hermes/gateway.env` dosyasından `TELEGRAM_BOT_TOKEN`
2. **Chat ID:** Session key'den çıkarılır: `agent:main:telegram:dm:5506784207` → Chat ID = `5506784207`

### Curl Komutu

```bash
BOT_TOKEN=$(grep TELEGRAM_BOT_TOKEN /home/hermes/.hermes/gateway.env | cut -d= -f2)
CHAT_ID="5506784207"  # veya ilgili chat ID
FILE="/path/to/file.md"

curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendDocument" \
  -F chat_id="${CHAT_ID}" \
  -F document="@${FILE}" \
  -F caption="📊 Dosya açıklaması" | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d.get('ok') else f'ERROR: {d}')"
```

### Chat ID Bulma

- **DM sohbeti:** Session key'den: `agent:main:telegram:dm:CHAT_ID`
- **Grup:** `getUpdates` API ile veya manuel not alma
- **Topic/Thread:** `message_thread_id` parametresi gerekli

### Dikkat Edilecekler

- Dosya boyutu limiti: 50MB (bot API limiti)
- Caption max 1024 karakter
- `@` sembolü dosya yolundan önce gerekli (curl form data için)
- Hata durumunda JSON response'u parse et — `ok: true` ise başarılı

### Otomatik Teslimat

Dosyayı bot ile göndermek yerine, `cronjob` tool'u ile `deliver: origin` kullanarak da gönderilebilir. Ama bu sadece metin mesajları için çalışır — dosya ekleri için Bot API gerekir.
