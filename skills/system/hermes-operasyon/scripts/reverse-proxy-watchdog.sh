#!/usr/bin/env bash
# reverse-proxy-watchdog.sh — 5dk cron ile çalışan otonom reverse-proxy sağlık kontrolü
# Kurulum: crontab -e → */5 * * * * /home/hermes/.hermes/scripts/reverse-proxy-watchdog.sh
# L3 Ders (07.09.2026): Kullanıcı fark etmeden önce fark et, otonom geri başlat, alarm ver.

set -u

LOG=/home/hermes/.hermes/logs/reverse-proxy-watchdog.log
ALERT_FLAG=/home/hermes/.hermes/state/reverse-proxy-alert.flag
mkdir -p "$(dirname "$LOG")" "$(dirname "$ALERT_FLAG")"

log() { echo "[$(date -Iseconds)] $*" | tee -a "$LOG" ; }

FAIL=0
ACTIONS=""

# 1) Port 80 + 443 dinliyor mu?
if ! ss -tln | grep -qE ":(80|443)\b"; then
  log "FAIL: port 80/443 dinlemiyor"
  FAIL=1
fi

# 2) Traefik container ayakta mı?
if ! docker ps --format '{{.Names}}' | grep -q '^coolify-proxy$'; then
  log "FAIL: coolify-proxy container yok, başlatılıyor"
  docker start coolify-proxy >> "$LOG" 2>&1 || (
    cd /data/coolify/proxy 2>/dev/null && docker compose up -d >> "$LOG" 2>&1
  )
  ACTIONS="${ACTIONS} coolify-proxy restart"
  FAIL=1
fi

# 3) n8n container ayakta mı?
if ! docker ps --format '{{.Names}}' | grep -q '^n8n$'; then
  log "FAIL: n8n container yok, başlatılıyor"
  docker start n8n >> "$LOG" 2>&1
  ACTIONS="${ACTIONS} n8n restart"
  FAIL=1
fi

# 4) Dışarıdan HTTP 200/302 mi?
ESGRUP=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://esgrupmetal.com/ 2>/dev/null)
N8N_SITE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 https://n8n.aiergene.xyz/healthz 2>/dev/null)

if [[ "$ESGRUP" != "200" && "$ESGRUP" != "301" && "$ESGRUP" != "302" ]]; then
  log "FAIL: esgrupmetal.com HTTP $ESGRUP"
  FAIL=1
fi

if [[ "$N8N_SITE" != "200" ]]; then
  log "FAIL: n8n.aiergene.xyz HTTP $N8N_SITE"
  FAIL=1
fi

# 5) Sonuç
if [[ $FAIL -eq 0 ]]; then
  rm -f "$ALERT_FLAG"
  log "OK: tüm kontroller geçti (esgrup=$ESGRUP n8n=$N8N_SITE)"
  exit 0
else
  log "ACTION: yeniden başlatıldı:$ACTIONS"
  # Spam önleme: sadece alert flag yoksa yaz
  if [[ ! -f "$ALERT_FLAG" ]]; then
    cat > "$ALERT_FLAG" <<EOF
TIMESTAMP=$(date -Iseconds)
ACTIONS=$ACTIONS
ESGRUP=$ESGRUP
N8N=$N8N_SITE
EOF
    log "ALERT: alert flag konuldu, Hermes bir sonraki tick'inde Telegram'a bildirecek"
  fi
  exit 1
fi
