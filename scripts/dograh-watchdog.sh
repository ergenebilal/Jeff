#!/bin/bash
# Dograh Watchdog — her 5 dk'da bir sağlık kontrolü
DOGRAH_URL="http://localhost:8890/health"

if curl -sf "$DOGRAH_URL" > /dev/null 2>&1; then
    # Çalışıyor, ses çıkarma
    exit 0
else
    echo "⚠️ Dograh düştü, yeniden başlatılıyor..."
    cd /home/hermes/dograh && docker compose up -d 2>&1
    echo "✅ Dograh restart edildi."
fi
