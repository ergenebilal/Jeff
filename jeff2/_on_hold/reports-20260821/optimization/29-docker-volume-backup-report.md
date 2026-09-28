# 29-Docker-Volume-Backup-Report.md
**Tarih:** 2026-08-17 15:15 UTC+3

## İlk Test Sonuçları (2026-08-17 15:11)

| Volume | Boyut | Durum |
|--------|-------|-------|
| hmpanel_pgdata | 25 MB | ✅ |
| coolify-db | 26 MB | ✅ |
| hmpanel_redisdata | 4 KB | ✅ |
| hmpanel_uploads | 4 KB | ✅ |
| hmpanel_logs | 4 KB | ✅ |
| n8n-data (SQLite) | 2.7 MB | ✅ |
| **Toplam** | **~58 MB** | |

## Otomasyon
- Script: /opt/backups/scripts/jeff-comprehensive-backup.sh
- Cron: 0 4 * * *
- Include: pg_dump + 5 volume + n8n SQLite + config + memory

## Saklama Politikası
- 30 gün yerel saklama (RETENTION_DAYS=30)
- Dış yedek aktif olmadığında sadece yerel
