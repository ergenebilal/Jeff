#!/bin/bash
# Port 80 Watchdog — eğer nginx veya başka bir process 80'i kaparsa, traefik'i koru
while true; do
    if ss -tlnp | grep -q ':80\s'; then
        WHO=$(ss -tlnp | grep ':80\s' | grep -oP 'users:\(\(\K[^"]+')
        if echo "$WHO" | grep -qv "traefik"; then
            logger "PORT80_WATCHDOG: $WHO 80'i kapti, temizleniyor..."
            fuser -k 80/tcp 2>/dev/null
            sleep 2
            docker restart coolify-proxy 2>/dev/null
        fi
    fi
    sleep 300
done
