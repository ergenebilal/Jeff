# Comprehensive Backup Script Anatomisi

## Script Yapısı (jeff-comprehensive-backup.sh)

| Adım | İçerik | Fail durumu |
|------|--------|-------------|
| 1/7 | PostgreSQL dump (coolify-db) | `fail` — script'i sonlandırır |
| 2/7 | Docker volume yedekleri (4 volume) | `fail` — script'i sonlandırır |
| 3/7 | Config yedekleri | `fail` — script'i sonlandırır |
| 4/7 | Memory/brain yedekleri | `fail` — script'i sonlandırır |
| 5/7 | Sistem raporu | `fail` — script'i sonlandırır |
| 6/7 | SHA256 checksums | `fail` — script'i sonlandırır |
| 7/7 | Ana arşiv oluşturma | `fail` — script'i sonlandırır |
| 8/8 | Google Drive yükleme | `WARN` — script devam eder |

## SA vs OAuth — Hangisini Kullanmalı?

| Senaryo | Çözüm |
|---------|-------|
| **Kişisel Google hesabı** | SA çalışmaz (Shared Drive yok). OAuth renewal kullan. |
| **Google Workspace (kurumsal)** | SA çalışır (domain-wide delegation ile). |
| **Headless sunucu** | SA tercih edilir (browser gerekmez). Kişisel hesapsa OAuth renewal tek yol. |

### OAuth Renewal Prosedürü (Kişisel Hesap)
1. Kullanıcı local terminalinde `rclone authorize "drive"` çalıştırır
2. Browser açılır → Google'a girer → izin verir
3. rclone token'ı otomatik yakalar → ekrana JSON basar
4. Kullanıcı JSON'u kopyalıp sunucudaki config'e yapıştırır
5. Token formatı: `token = {"access_token":...,"token_type":...,"refresh_token":...,"expiry":...}`

### SA Prosedürü (Workspace)
1. Google Console → IAM → Service Account oluştur
2. JSON key indir
3. SA e-postasına klasörü Editor olarak paylaş
4. `service_account_file = /path/to/sa.json` yaz
5. PKCS#8 direkt çalışır, dönüşüm gerekmez

### 1. Container/Volume Yok
- **Belirti:** `docker exec hmpanel-postgres ...` → "No such container"
- **Kök neden:** Container adı değişmiş veya container artık yok
- **Çözüm:** `docker ps -a` ile gerçek ismi bul, script'i güncelle veya adımı kaldır

### 2. Dosya Adı Tutarsızlığı
- **Belirti:** `pg_dump -U coolify coolify` ama dosya adı `hmpanel-*.sql.gz`
- **Kök neden:** İçeriği güncelleyip dosya adını unutmak
- **Çözüm:** İçerik ve dosya adını eşleştir

### 3. Offsite Token Ölü
- **Belirti:** `invalid_grant: maybe token expired?`
- **Kök neden:** rclone token'ın süresi dolmuş
- **Çözüm:** SA JSON ile değiştir veya adımı `WARN` yap

### 4. Volume Listesi Eski
- **Belirti:** `hmpanel_pgdata` volume'u yok
- **Kök neden:** Volume silinmiş veya adı değişmiş
- **Çözüm:** `docker volume ls` ile gerçek listeyi al, script'i güncelle

## Fail-Soft Deseni

İsteğe bağlı adımlar (offsite yükleme) `fail` yerine `WARNINGS` artırmalı:

```bash
# YANLIŞ — script'i sonlandırır
fail "Google Drive yukleme basarisiz!"

# DOĞRU — script devam eder, local arşiv korunur
WARNINGS=$((WARNINGS + 1))
log "WARN: Google Drive yükleme başarısız (SA JSON bekleniyor)"
```

## Kontrol Listesi (Her Bakım Turunda)

- [ ] Script'teki tüm container'lar var mı? (`docker ps -a`)
- [ ] Script'teki tüm volume'lar var mı? (`docker volume ls`)
- [ ] Dump dosya adı = içerik kaynağı?
- [ ] Offsite adımı fail-soft mu?
- [ ] Token durumu sağlıklı mı?
- [ ] Log dosyaları oluşuyor mu?