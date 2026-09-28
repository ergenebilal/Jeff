#!/bin/bash
# Port 80 kontrol — nginx 80'i kaptıysa temizle ve traefik'i yeniden başlat
if ss -tlnp | grep -q ':80\s'; then
    OWNER=$(ss -tlnp | grep ':80\s' | grep -oP '"([^"]+)"' | head -1 | tr -d '"')
    if [ "$OWNER" != "traefik" ] && [ -n "$OWNER" ]; then
        echo "[$(date)] PORT80_SAVCI: $OWNER 80'i caldi, temizleniyor..."
        sudo fuser -k 80/tcp 2>/dev/null
        sleep 2
        sudo docker restart coolify-proxy 2>/dev/null
    fi
fi
