#!/usr/bin/env bash
# Hermes Watchdog v2.1 — Otonom Çözüm (düzeltilmiş)
# Sorunları tespit eder, otomatik çözer. Sessiz çalışır.
# v2.1 FIX: FastAPI zaten çalışıyorsa yeniden başlatma; arka plan detach; exec bit.
set -euo pipefail

FIXED=0

# 1. Gateway PID temizliği — ölü PID'yi kaldır, gerekirse yeniden başlat
if [ -f ~/.hermes/gateway.pid ]; then
  GWPID=$(cat ~/.hermes/gateway.pid 2>/dev/null || echo "")
  if [ -n "$GWPID" ] && ! kill -0 "$GWPID" 2>/dev/null; then
    rm -f ~/.hermes/gateway.pid
    FIXED=$((FIXED+1))
  fi
fi

# 2. Disk temizliği — %85'i aşarsa temizle
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
  find /tmp -type f -mtime +7 -delete 2>/dev/null || true
  find ~/.cache/pip -type f -mtime +30 -delete 2>/dev/null || true
  journalctl --vacuum-time=7d 2>/dev/null || true
  FIXED=$((FIXED+1))
fi

# 3. RAM temizliği — 500MB altındaysa cache temizle
MEM_AVAIL=$(free -m | awk '/^Mem:/{print $7}')
if [ "$MEM_AVAIL" -lt 500 ]; then
  sync
  echo 3 > /proc/sys/vm/drop_caches 2>/dev/null || true
  FIXED=$((FIXED+1))
fi

# 4. Port 8099 (FastAPI) — yalnızca GERÇEKTEN down ise başlat.
#    Sağlık kontrolü: port dinleniyorsa sağlıklı kabul et (api /health bazen yanıt vermiyor).
if ! ss -tln 2>/dev/null | grep -q ":8099 "; then
  cd /opt/hermes/jeff_v2
  # Tam detach: stdin kapat, çıktıyı log dosyasına, setsid ile ayrı oturum
  setsid nohup python3 api_server.py > /opt/backups/logs/api_server.log 2>&1 < /dev/null &
  disown || true
  sleep 2
  FIXED=$((FIXED+1))
fi

# Her şey temiz — sessiz kal (empty stdout = no delivery)
exit 0
