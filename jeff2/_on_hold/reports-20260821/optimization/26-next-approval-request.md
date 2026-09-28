# 26-Next-Approval-Request.md
**Spec:** JEFF-OPT-MASTER-001 Phase 3
**Tarih:** 2026-08-17 15:00 UTC+3
**Operator:** Jeff

---

## İnsan Onayı Gereken İşler

### ACİL (BLOCKED — gelir优zlemine geçmek için gerekli)

| # | İş | Neden Onay Gerekir | Tahmini | Risk |
|---|-----|-------------------|---------|------|
| 1 | rclone kur + Google Drive yapılandır | Yeni servis + external API key | 30 dk | Düşük |
| 2 | PostgreSQL için pg_dump cron ekle | Production volume değişikliği | 15 dk | Düşük |
| 3 | Docker volume yedek scripti yaz + cron ekle | Production script | 1 saat | Orta |
| 4 | UFW'den 8000/8090/8642/6001/6002 ALLOW kurallarını kaldır | Firewall değişikliği — servis erişimi etkilenebilir | 15 dk | Yüksek |
| 5 | Container memory limitleri ekle (n8n: 1G, panel: 512M, postgres: 256M) | Container konfigürasyon değişikliği | 15 dk | Orta |

### YÜKSEK ÖNCELİK

| # | İş | Neden Onay | Tahmini |
|---|-----|-----------|---------|
| 6 | PostgreSQL credential rotation | Güvenlik — compose'da default password riski | 30 dk |
| 7 | DOCKER-USER restore scriptini doldur + crontab @reboot ekle | Persistence eksik | 15 dk |
| 8 | Memory alarm scripti yaz + test et | Yeni izleme altyapısı | 30 dk |
| 9 | Oluşturulan yedekleri Google Drive'a gönder | İlk dış yedek | 1 saat |

### DÜŞÜK ÖNCELİK

| # | İş | Neden Onay | Tahmini |
|---|-----|-----------|---------|
| 10 | host-agent readonly rootfs yap | Container hardening | 5 dk |
| 11 | Cron execution log sistemi kur | Gözlemlenebilirlik | 1 saat |
| 12 | Eski docker-compose yedeklerini temizle | Disk temizliği | 5 dk |

---

## Onay Formatı

Her iş için onay şu şekilde verilmeli:
```
ONAY: [numara] — [evet/hayır]
```

Örnek:
```
ONAY: 1,2,3,4,5 — evet
ONAY: 6,7,8 — hayır (önce test ortamında dene)
```

---

## Sonraki Adım

Onay bekleniyor. Onay geldikten sonra:
1. Onaylanan işler sırayla uygulanacak
2. Her aksiyon sonrası doğrulama testi çalıştırılacak
3. Güncel readiness skoru hesaplanacak
4. Rapor Telegram'a gönderilecek

---

*Bu rapor 26-next-approval-request.md olarak adlandırılmıştır.*
