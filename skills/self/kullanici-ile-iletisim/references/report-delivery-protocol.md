# Rapor Teslimat Protokolü

**Kural (17.08.2026 — Bilal kesin talimatı):** Her görevin sonunda tüm raporlar tek dosyada birleştirilip Telegram'a indirilebilir doküman olarak gönderilir.

## Kurallar
- Birden fazla rapor varsa → tek `.md` dosyasına birleştir
- Chat'e yazdırma → dosya olarak `sendDocument` ile gönder
- Caption: kısa özet (kaç rapor, toplam boyut, ana durum)
- Format: Markdown (.md)
- Dosya adı deseni: `<konu>-<tarih>.md`

## Telegram Gönderim Komutu
```bash
BOT_TOKEN=$(grep "TELEGRAM_BOT_TOKEN" ~/.hermes/.env | cut -d'=' -f2- | tr -d '"' | tr -d "'")
CHAT_ID="${TELEGRAM_OWNER_CHAT_ID}"
curl -s -X POST "https://api.telegram.org/bot${BOT_TOKEN}/sendDocument" \
  -F "chat_id=${CHAT_ID}" \
  -F "document=@/path/to/report.md" \
  -F "caption=📋 Kısa özet"
```

## Örnek
Görev sonunda 3 rapor üretildiyse:
1. `phase3-backup-closure.md` — backup kapanış
2. `security-remediation-phase1.md` — güvenlik remediation
3. `port-inventory.md` — port envanteri

→ Tek dosyada birleştir: `jeff-phase3-final-report.md`
→ Telegram'a gönder: `sendDocument`
