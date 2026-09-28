# 28-Firewall-Remediation-Report.md
**Tarih:** 2026-08-17 15:15 UTC+3

## Yapılan Değişiklikler

### UFW Kuralları Kaldırıldı
- 8642/tcp ALLOW IN → KALDIRILDI ✅
- 8000, 8090, 6001, 6002 için explicit ALLOW kuralı zaten yoktu

### INPUT Chain DROP Rules Eklendi
- port 8000 → DROP ✅
- port 8090 → DROP ✅
- port 8642 → DROP ✅
- port 6001 → DROP ✅
- port 6002 → DROP ✅

### DOCKER-USER Chain
- 7 DROP rules mevcut (8000, 8090, 8642, 6001, 6002, 8765, 8767)
- Sadece FORWARD chain'de etkili

### Dış Erişim Test Sonuçları (Değişiklik Sonrası)
- Port 22: OPEN ✅ (SSH — intended)
- Port 80: OPEN ✅ (HTTP — intended)
- Port 443: OPEN ✅ (HTTPS — intended)
- Port 8642: CLOSED ✅ (INPUT DROP çalıştığını doğruladı)
- Port 8000: OPEN ❌ (Docker proxy socket — INPUT rules yetersiz)
- Port 8090: OPEN ❌ (Docker proxy socket)
- Port 6001: OPEN ❌ (Docker proxy socket)
- Port 6002: OPEN ❌ (Docker proxy socket)

### Kök Neden Analizi
Docker port publishing → docker-proxy süreci 0.0.0.0'da socket açar.
iptables INPUT kuralları zaten dinleyen bir socket'e gelen trafiği engelleyemez.

### Kalıcı Çözüm (Onay Gerekir)
`/etc/docker/daemon.json`'a `"userland-proxy": false` eklensin.
Bu durumda Docker proxy kullanmaz, sadece iptables DNAT kullanır.
DOCKER-USER chain tam etkili olur.

### Persistence
- ✅ Restore script: /home/hermes/scripts/restore-docker-user-rules.sh
- ✅ @reboot crontab eklendi
- ✅ Manuel test başarılı
