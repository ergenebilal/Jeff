#!/bin/bash
# Jeff Self-Audit — son 2 saatte output üretilmiş mi kontrol eder
# Cron tarafından çağrılır (no_agent mode)

OUTPUT_DIR="/home/hermes/hermes_data/outputs"
AUDIT_LOG="/home/hermes/hermes_data/logs/self-audit.log"
NOW=$(date +%s)

mkdir -p "$(dirname "$AUDIT_LOG")"
mkdir -p "$OUTPUT_DIR"

# Son 2 saatte değişen dosyaları bul
RECENT=$(find "$OUTPUT_DIR" -type f -mmin -120 2>/dev/null | wc -l)

if [ "$RECENT" -eq 0 ]; then
    echo "[$NOW] ⚠️ UYARI: Son 2 saatte hiç dosya üretilmedi. Pasif dönem. $(date)" >> "$AUDIT_LOG"
    echo "UYARI: Son 2 saatte üretim yok"
else
    echo "[$NOW] ✅ Aktif: $RECENT dosya değişmiş. $(date)" >> "$AUDIT_LOG"
fi
