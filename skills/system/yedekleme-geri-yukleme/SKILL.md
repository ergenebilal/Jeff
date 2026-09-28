---
name: yedekleme-geri-yukleme
description: "Yedek script bakımı, rclone/Drive token, SQLite WAL teşhisi."
---

# Yedekleme & Geri Yükleme Operasyonları

Bu skill, sunucu genelinde yedekleme script'lerinin bakımını, rclone/Drive bağlantı yönetimini ve SQLite WAL modu teşhisini kapsar.
`hermes-operasyon` gateway/provider/config odaklıdır; bu skill **backup/restore** odaklıdır.

## Tetikleme koşulları

- Backup script fail veriyor (container yok, volume yok, token ölü)
- rclone/Drive token expired, refresh çalışmıyor
- SQLite WAL modu uyarıları geliyor
- Yedek doğrulama/checksum sorunu
- Offsite yedek (Drive) çalışmıyor ama local oluşuyor

## 1. Backup Script Bakımı — "Ölü Adım" Deseni

**KURAL:** Backup script'leri zamanla ölü adımlar biriktirir. Her bakım turunda şu üç kontrolü yap:

### Adım A — Container/Volume gerçekliğini doğrula
```bash
# Script'te referans edilen her container için:
docker ps -a | grep -i 'ADI' || echo "Container yok: ADI"

# Script'te referans edilen her volume için:
docker volume ls --format '{{.Name}}' | grep -i 'ADI' || echo "Volume yok: ADI"
```
- **Container yoksa:** Script'teki referansı güncelle (farklı container'a yönlendir) veya o adımı kaldır.
- **Volume yoksa:** `VOLUMES` listesinden çıkar. Olmayan volume fail üretir ve script'i sonlandırır (`set -euo pipefail`).

### Adım B — Dosya adı tutarlılığı
- Dump dosyasının adı, içeriğin kaynağıyla eşleşmeli.
- Örnek: `pg_dump -U coolify coolify` → dosya adı `coolify-*.sql.gz` olmalı, `hmpanel-*.sql.gz` değil.
- **Pitfall:** İçeriği güncelleyip dosya adını unutmak — reader'ın kafası karışır, geri yüklemede yanlış dosya seçilir.

### Adım C — İsteğe bağlı adımları fail-soft yap
- Offsite yükleme (rclone/Drive) **isteğe bağlı** bir adım — local arşiv oluştuysa yedek başarılı sayılır.
- `fail` yerine `WARNINGS` artır + `log "WARN: ..."` yaz. Script `exit 1` yapmaz, local arşiv korunur.
- **Pitfall:** Offsite token ölüyse script fail olur, local arşiv de "başarısız" raporlanır — kullanıcı yanlış bilgilendirir.

## 2. rclone/Drive Token Yaşam Döngüsü

### Token durum tespiti
```bash
rclone lsd gdrive:Jeff-Backup --config /home/hermes/.config/rclone/rclone.conf
```
- `invalid_grant: maybe token expired?` → Token ölü, refresh çalışmaz.
- `couldn't find root directory ID` → Token geçerli ama izin yok (SA paylaşımı eksik olabilir).

### Refresh vs Re-auth
- **Refresh token** yalnızca access token'ı yeniler; refresh token'ın süresi dolmamış olmalı.
- **Tam expiry** durumunda `rclone config reconnect` çalışmaz (backend desteklemez).
- **Headless sunucuda** `rclone authorize` browser açmaz → timeout.

### Service Account (SA) — Kişisel Hesaplarda ÇALIŞMAZ
- SA'lar kendi kişisel Drive'larına yazamaz — sadece **Shared Drive** (Ekip Sürücüsü) üzerine yazabilir.
- **Kişisel Google hesaplarında Shared Drive yoktur** → SA kişisel hesaba yükleyemez.
- SA yalnızca Google Workspace (kurumsal) hesaplarda çalışır — orada "domain-wide delegation" ile SA kişisel hesap üzerinden yazabilir.
- **Pitfall:** Kişisel hesap + SA = 403 storageQuotaExceeded. Kullanıcı "ekip sürücüsü" oluşturma seçeneği göremez (kişisel hesap).
- **PKCS#8:** rclone v1.75.0 PKCS#8'i doğrudan destekler, PKCS#1 dönüşümü gereksiz. Parse hatası alınırsa içerik bozulmuş olmuştur (düzenleme/sed sonrası), format değil.

### OAuth Token'ı Yenileme — KİŞİSEL HESAPLAR İÇİN DOĞRU YOL
- Sunucuda display yoksa `rclone authorize` browser açmaz → timeout.
- **Çözüm (tek çalışan yöntem):** Kullanıcı local terminalinden `rclone authorize "drive"` çalıştırır, browser'da Google'a girer, dönen token JSON'u sunucudaki config'e yapıştırır.
- **Token formatı:** `token = {"access_token":...,"token_type":...,"refresh_token":...,"expiry":...}` — tek satır, JSON objesi.
- **Yapıştırma sonrası doğrulama:** `rclone lsd gdrive:Jeff-Backup` çalıştır. Boş dönerse token geçerli ama klasör paylaşılmamış demek — 2-3 dakika bekleyip tekrar dene.
- **Windows'ta rclone kurulumu:** `winget install Rclone.Rclone` → PATH güncellenir, **PowerShell kapatılıp açılmalı** (aksi takdirde `rclone` bulunamaz).
- **Pitfall:** Kullanıcı dönen URL'yi manuel kopyalayabilir — rclone "Waiting for code" durumdayken **browser'da açması ve izin vermesi** gerek, manuel kopyalama çalışmaz. Ama token JSON'u sunucudaki `rclone.conf`'a elle yapıştırılabilir (tek satır `token = {...}`).
- **Neden SA değil:** Kişisel Google hesaplarında Shared Drive olmadığından SA yükleme yapamaz. OAuth renewal kişisel hesaplar için tek kalıcı çözüm.

### Ölü remote'u temizle
- Token'ı ölmüş ve `service_account_file = n` gibi sahte satır içeren remote'u `rclone.conf`'dan sil.
- **Her zaman önce yedek al:** `cp rclone.conf rclone.conf.bak-$(date +%Y%m%d_%H%M%S)`
- Silmeden önce hiçbir script'in o remote'u kullanmadığını doğrula.

## 3. SQLite WAL Modu — Teşhis

**KURAL:** SQLite WAL modu **normaldir**, sorun değildir. `state.db-wal` dosyası olması sorun değil; checkpoint çalışıyorsa veri bütünlüğü korunur.

### Sağlık kontrolü
```python
import sqlite3
conn = sqlite3.connect('/home/hermes/.hermes/state.db')
c = conn.cursor()
c.execute('PRAGMA journal_mode;')  # 'wal' dönmeli
c.execute('PRAGMA wal_checkpoint(FULL);')  # (0, N, N) = başarılı
conn.close()
```
- `(0, 194, 194)` → 0 hata, 194 sayfa WAL'dan main DB'ye yazıldı. **Sağlıklı.**
- `(0, 0, 0)` → WAL boş, yazılacak şey yok. **Sağlıklı.**
- `(1, ...)` → Checkpoint başarısız, başka bir process DB'ye yazıyor olabilir.

### Log tuzağı
- WAL uyarıları `logs/*.log` dosyalarında **bulunmayabilir** — gateway log'ları ayrı dosyada veya journal'da olabilir.
- `grep -i "wal" /home/hermes/logs/*.log` sonuç vermiyorsa, sorun yok demek değil; farklı log kaynağı ara.
- **Journal kontrolü:** `sudo journalctl -u hermes-gateway --since "HH:MM" | grep -i wal`

### WAL'ı "sorun" sayma
- WAL modu, concurrent read/write performansını artırır. Postgres'e geçiş gerektirmez.
- `state.db` 233 MB + WAL 4 MB → normal boyut. Postgres'e taşıma gereksiz maliyet.

## 4. Yedek Doğrulama

- **Checksum:** `sha256sum` ile her dosya için checksum üret, `CHECKSUMS.sha256` dosyasına yaz.
- **Geri yükleme testi:** Yedekten bir dosya çıkar, hash'ı orijinal ile karşılaştır.
- **Log saklama:** Her backup log'unu `/opt/backups/logs/` altında sakla, retention policy uygula.

## Pitfalls özeti

- [ ] Backup script'lerinde container/volume referanslarını güncel tut — olmayan adım fail üretir
- [ ] Dump dosya adı = içerik kaynağı (coolify-db → coolify-*.sql.gz)
- [ ] Offsite yükleme fail-soft olmalı — local arşiv oluştuysa script başarılı sayılır
- [ ] rclone token ölüyse refresh çalışmaz — SA headless kalıcı çözüm
- [ ] SA JSON gelene kadar rclone adımını WARN yap, fail etme
- [ ] SQLite WAL modu normaldir — checkpoint (0, N, N) = sağlıklı
- [ ] WAL uyarısı loglarda görünmüyorsa sorun yok demek değil, farklı kaynak ara
- [ ] rclone.conf düzenlemeden önce yedek al
- [ ] Ölü remote'u silmeden önce hiçbir script kullanmadığını doğrula

## Destek dosyaları

- `references/backup-script-anatomy.md` — comprehensive backup script'inin adım adım anatomisi ve sık karşılaşılan ölü adım desenleri
- `references/system-verification-workflow.md` — bakım/değişiklik sonrası kapsamlı sistem sağlık kontrolü (10 madde, github copilot pattern)