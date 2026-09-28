# rclone / Google Drive Yedekleme Kimliği (hafızadan taşındı 15.09.2026)

- rclone uzak adı: **`gdrive:`** — kendi client_id'siyle çalışır.
- Bilal **kişisel Google hesabı** kullanıyor (Workspace değil) → Shared Drive yok. Servis hesabı yalnızca Shared Drive'a yazabilir; kişisel Drive'a yedek **OAuth token** ile alınır. SA JSON dosyasına dokunulmaz.
- Hedef klasör adı: **Jeff-Backup**. (Dikkat: benzer adlı 4 klasör var — Jeff Backups / Backup / -Backup / Yedek.)
- Google OAuth kapsamları: Drive, Calendar, Docs, Sheets, Gmail gönderme + refresh çalışıyor; **gmail.readonly eksik**.
- **Tarihli risk (14.09.2026 tespiti):** rclone'un ortak client_id'si 2026 içinde kapatılacağını kendi uyarısıyla bildirdi. Bugün çalışıyor ama yıl içinde yedekleme durabilir — kendi client_id'sine geçiş planlanmalı.
- Yedek akışı: her gece 04:00 → `/opt/backups/data/` yerel arşiv + sha256 + Drive yüklemesi. Log: `/opt/backups/logs/backup-<tarih>.log`.
