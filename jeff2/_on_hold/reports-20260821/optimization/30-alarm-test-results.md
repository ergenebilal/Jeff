# 30-Alarm-Test-Results.md
**Tarih:** 2026-08-17 15:15 UTC+3

## Memory Alarm Test

### Script: /home/hermes/scripts/memory-alarm.sh

### Eşikler
| Seviye | Eşik | Aksiyon |
|--------|------|---------|
| OK | < %85 | Log |
| WARNING | ≥ %85 | Log + çıktı |
| HIGH | ≥ %90 | Log + çıktı |
| CRITICAL | ≥ %95 | Log + çıktı |

### Test Sonucu
```
SEVERITY=OK RAM=77% USED=24823MB TOTAL=32093MB AVAIL=6798MB SWAP=96MB OOM=0
```

- RAM: %77 — OK (eşik altında)
- Swap: 96 MB — OK
- OOM Kill: 0 — OK

### Cron
- Her 5 dakikada bir çalışıyor
- Log: /opt/backups/logs/memory-alarm.log

### Telegram Alarm
- Mevcut durumda sadece log'a yazıyor
- Telegram bildirimi için Hermes cron job tetiklenebilir
- HIGH/CRITICAL durumunda agent otomatik bildirim gönderebilir
