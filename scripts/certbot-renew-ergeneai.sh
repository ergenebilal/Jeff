#!/bin/bash
# ergeneai.com SSL sertifikası yenileme — 60 günde bir çalışır

CERTBOT=/home/hermes/.local/bin/certbot
DOMAINS="ergeneai.com,www.ergeneai.com"
WEBROOT=/opt/hmpanel/nginx/acme
CONFIG_DIR=/home/hermes/certbot/config
WORK_DIR=/home/hermes/certbot/work
LOG_DIR=/home/hermes/certbot/logs
DEST_DIR=/opt/hmpanel/nginx/ssl/ergeneai

# Sertifikayı yenile (yenileme gerekmiyorsa sessizce çıkar)
sudo chown -R hermes:hermes "$WEBROOT" 2>/dev/null
$CERTBOT renew --config-dir "$CONFIG_DIR" --work-dir "$WORK_DIR" --logs-dir "$LOG_DIR" --quiet 2>&1
RENEW_RESULT=$?
sudo chown -R bilaladmin:bilaladmin "$WEBROOT" 2>/dev/null

# Yenilendiyse hmpanel nginx'e kopyala ve reload et
if [ $RENEW_RESULT -eq 0 ]; then
    # Yeni sertifikaları kontrol et
    if [ -f "$CONFIG_DIR/live/ergeneai.com/fullchain.pem" ]; then
        sudo cp "$CONFIG_DIR/live/ergeneai.com/fullchain.pem" "$DEST_DIR/"
        sudo cp "$CONFIG_DIR/live/ergeneai.com/privkey.pem" "$DEST_DIR/"
        sudo chown -R bilaladmin:bilaladmin "$DEST_DIR"
        docker exec hmpanel-nginx nginx -s reload 2>/dev/null
        echo "[$(date)] ergeneai.com SSL renewed & reloaded"
    fi
fi
