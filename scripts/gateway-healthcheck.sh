#!/bin/bash
# ============================================================
# Hermes Gateway Healthcheck — yarı-ölü durumları tespit edip
# otomatik restart yapar.
#
# Her 5 dk'da bir cron'dan çalışır:
# */5 * * * * /home/hermes/.hermes/scripts/gateway-healthcheck.sh
# ============================================================
set -euo pipefail

LOG_FILE="/home/hermes/logs/gateway-healthcheck.log"
PID_FILE="/tmp/hermes-gateway-healthcheck.pid"
MAX_RUNTIME=120  # max 2 dk çalışsın
RESTART_STAMP="/tmp/hermes-gateway-last-restart"
RESTART_COOLDOWN=600  # 10 dk içinde ikinci restart YOK (flap koruması)

# Önceki instance varsa bekleme süresini aşmış mı kontrol et
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if kill -0 "$OLD_PID" 2>/dev/null; then
        OLD_RUNTIME=$(( $(date +%s) - $(stat -c %Y "$PID_FILE" 2>/dev/null || date +%s) ))
        if [ "$OLD_RUNTIME" -lt "$MAX_RUNTIME" ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Önceki healthcheck hala çalışıyor (PID: $OLD_PID, ${OLD_RUNTIME}s). Çıkılıyor."
            exit 0
        else
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Önceki healthcheck takılı kalmış (PID: $OLD_PID, ${OLD_RUNTIME}s). Öldürülüyor."
            kill -9 "$OLD_PID" 2>/dev/null || true
        fi
    fi
fi
echo $$ > "$PID_FILE"
trap 'rm -f "$PID_FILE"' EXIT

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# Flap korumalı restart: son COOLDOWN süresinde restart edildiyse atla.
# DÖNÜŞ: 0 = restart edildi, 1 = atlandı (cooldown)
do_restart() {
    local reason="$1"
    local now
    now=$(date +%s)
    if [ -f "$RESTART_STAMP" ]; then
        local last
        last=$(cat "$RESTART_STAMP" 2>/dev/null || echo 0)
        if [ $(( now - last )) -lt "$RESTART_COOLDOWN" ]; then
            log "FLAP KORUMASI: $reason — ancak son restart $(( now - last ))sn önce. Atlanıyor."
            return 1
        fi
    fi
    log "$reason Restart ediliyor..."
    # NOT: servis restart yetkisi sudo gerektirir (hermes'te NOPASSWD var).
    # sudo'suz restart "Interactive authentication required" ile ölür ve
    # gateway yarı-ölü kalır — eski kopma döngüsünün ikinci sebebi buydu.
    sudo -n systemctl restart hermes-gateway.service
    date +%s > "$RESTART_STAMP"
    log "Restart edildi."
    return 0
}

# === 1. Systemd servis durumunu kontrol et ===
# NOT: activating/deactivating/reloading GEÇİCİ durumlardır (restart drain
# 180sn sürebilir). Bunları "ölü" sanıp restart etmek flap döngüsü yaratır.
SERVICE_STATUS=$(systemctl is-active hermes-gateway.service 2>/dev/null || echo "unknown")
case "$SERVICE_STATUS" in
    active)
        : ;; # aşağıdaki kontrollere devam
    activating|deactivating|reloading)
        log "Servis geçici durumda ($SERVICE_STATUS) — muhtemelen restart drain. Bekleniyor, çıkılıyor."
        exit 0
        ;;
    *)
        # failed/inactive/unknown: hemen restart ETME — yarış durumuna karşı
        # 30sn bekle, tekrar kontrol et.
        log "Servis aktif değil ($SERVICE_STATUS). 30sn beklenip tekrar kontrol edilecek..."
        sleep 30
        SERVICE_STATUS2=$(systemctl is-active hermes-gateway.service 2>/dev/null || echo "unknown")
        case "$SERVICE_STATUS2" in
            active|activating|deactivating|reloading)
                log "Servis toparlandı ($SERVICE_STATUS2). Çıkılıyor."
                exit 0
                ;;
        esac
        do_restart "SERVIS HALA AKTIF DEGIL ($SERVICE_STATUS2)."
        exit 0
        ;;
esac

# === 2. PID canlı mı kontrol et ===
MAIN_PID=$(systemctl show hermes-gateway.service -p MainPID 2>/dev/null | cut -d= -f2)
if [ -z "$MAIN_PID" ] || [ "$MAIN_PID" -le 1 ]; then
    do_restart "PID bulunamadi."
    exit 0
fi

if ! kill -0 "$MAIN_PID" 2>/dev/null; then
    do_restart "PID $MAIN_PID canli degil."
    exit 0
fi

# === 3. "Interpreter shutdown" hatası var mı kontrol et ===
# NOT: pipefail + "| grep -q" kombinasyonu SIGPIPE yarışına girer (grep erken
# çıkınca journalctl 141 ile ölür, koşul tutarsız çalışır). Process substitution
# kullan — karar sadece grep'in çıkışına bağlı.
# Pencere 6 dk: cron 5 dk'da bir koştuğu için her gerçek olay en az bir
# koşuda görülür; 30 dk pencere bayat satırlarla her koşuda restart üretirdi.
if grep -q "cannot schedule new futures after interpreter shutdown" < <(journalctl -u hermes-gateway.service --since "6 min ago" --no-pager 2>/dev/null); then
    do_restart "HATA: 'interpreter shutdown' tespit edildi. Gateway yari-olu durumda."
    exit 0
fi

# === 4. Son aktiviteyi kontrol et ===
# Gateway log'da son 5 dk'da API isteği var mı?
if grep -q "HTTP\|api_call\|conversation\|tool_call" < <(journalctl -u hermes-gateway.service --since "5 min ago" --no-pager 2>/dev/null); then
    log "Saglikli: Son 5 dk'da aktivite var."
    exit 0
fi

# === 5. Gateway API ve Antigravity Proxy yanıt veriyor mu? ===
PROXY_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 --max-time 5 http://127.0.0.1:8999/v1/models 2>/dev/null | tail -c 3 || echo "000")
if [ "$PROXY_CODE" != "200" ]; then
    log "UYARI: Antigravity Proxy (8999) yanıt vermedi (HTTP $PROXY_CODE). 5sn beklenip tekrar denenecek..."
    sleep 5
    PROXY_CODE2=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 --max-time 5 http://127.0.0.1:8999/v1/models 2>/dev/null | tail -c 3 || echo "000")
    if [ "$PROXY_CODE2" != "200" ]; then
        do_restart "HATA: Antigravity Proxy (:8999) yanıt vermiyor (HTTP $PROXY_CODE2)."
        exit 0
    fi
fi

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 --max-time 15 http://localhost:8644/ 2>/dev/null | tail -c 3 || echo "000")
if [ "$HTTP_CODE" = "000" ] || [ -z "$HTTP_CODE" ]; then
    log "UYARI: Gateway API yanit vermedi (HTTP $HTTP_CODE). 30sn beklenip tekrar denenecek..."
    sleep 30
    
    HTTP_CODE2=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 10 --max-time 15 http://localhost:8787/ 2>/dev/null | tail -c 3 || echo "000")
    if [ "$HTTP_CODE2" = "000" ] || [ -z "$HTTP_CODE2" ]; then
        log "HATA: Gateway API hala yanit vermiyor (HTTP $HTTP_CODE2). Gateway 30 dk'dir ayaktaysa restart..."
        UPTIME=$(ps -o etimes= -p "$MAIN_PID" 2>/dev/null || echo "0")
        if [ "${UPTIME:-0}" -gt 1800 ]; then  # 30 dk +
            do_restart "Gateway $UPTIME saniyedir ayakta ama API yanit vermiyor."
        else
            log "Gateway henuz yeni baslamis ($UPTIME sn), bekleniyor."
        fi
    else
        log "API ikinci denemede yanit verdi (HTTP $HTTP_CODE2)."
    fi
else
    # API yanıt veriyor (401 dahil — bu auth gerektiği anlamına gelir, gateway çalışıyor)
    log "Saglikli: API yanit verdi (HTTP $HTTP_CODE)."
fi
