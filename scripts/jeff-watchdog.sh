#!/bin/bash
# Jeff Watchdog — no_agent, her 5 dk'da bir çalışır
# Gateway, RAM, Disk kontrolü + otomatik restart

GATEWAY_PID=$(pgrep -f "gateway run" | head -1)
MEM_AVAIL=$(free -m | awk '/^Mem:/{print $7}')
DISK_PCT=$(df / | awk 'NR==2{print $5}' | tr -d '%')
LOG_FILE="/home/hermes/logs/watchdog-jeff.log"
ALERT=""

# Gateway kontrol
if [ -z "$GATEWAY_PID" ]; then
    ALERT="$ALERT GATEWAY_DOWN"
    systemctl start hermes-gateway 2>/dev/null
    sleep 3
    if pgrep -f "gateway run" > /dev/null; then
        ALERT="$ALERT RESTART_OK"
    else
        ALERT="$ALERT RESTART_FAILED"
    fi
fi

# RAM kontrol (500MB altı uyarı)
if [ "$MEM_AVAIL" -lt 300 ]; then
    ALERT="$ALERT LOW_MEM_${MEM_AVAIL}MB"
fi

# Disk kontrol (%85 üstü uyarı)
if [ "$DISK_PCT" -gt 85 ]; then
    ALERT="$ALERT HIGH_DISK_${DISK_PCT}%"
fi

# Log'a yaz
echo "[$(date '+%Y-%m-%d %H:%M:%S')] PID=${GATEWAY_PID:-DOWN} RAM=${MEM_AVAIL}MB DISK=${DISK_PCT}% ${ALERT}" >> "$LOG_FILE"

# Sadece sorun varsa çıktı ver (no_agent sessizdir, sorun çıktısı kullanıcıya gider)
if [ -n "$ALERT" ]; then
    echo "⚠️ JEFF WATCHDOG: $ALERT"
    exit 1
fi
exit 0
