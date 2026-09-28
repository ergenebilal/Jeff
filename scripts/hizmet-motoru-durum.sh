#!/usr/bin/env bash
# Hizmet Motoru — Haftalık Pipeline Durumu
set -euo pipefail

REPORT="## 🏭 Hizmet Motoru — Haftalık Pipeline Durumu\n"
REPORT+="_$(date '+%Y-%m-%d %H:%M')_\n\n"

# Jeff 2.0 HQ log dosyasını kontrol et
HQ_LOG="/home/hermes/jeff2/hq/hizmet_motoru_cron.py"
if [ -f "$HQ_LOG" ]; then
  REPORT+="✅ Hizmet Motoru scripti mevcut\n"
  # Son çalışma zamanı
  MTIME=$(stat -c %Y "$HQ_LOG" 2>/dev/null || echo "0")
  NOW=$(date +%s)
  AGE=$(( (NOW - MTIME) / 86400 ))
  if [ "$AGE" -gt 7 ]; then
    REPORT+="⚠️ Script $AGE gündür değişmemiş\n"
  fi
else
  REPORT+="❌ Script bulunamadı: $HQ_LOG\n"
fi

# Jeff 2.0 report dizini
REPORT_DIR="/home/hermes/jeff2/reports"
if [ -d "$REPORT_DIR" ]; then
  REPORT_COUNT=$(ls -1 "$REPORT_DIR"/*.md 2>/dev/null | wc -l)
  REPORT+="📊 Rapor sayısı: $REPORT_COUNT\n"
  # Son rapor
  LAST_REPORT=$(ls -t "$REPORT_DIR"/*.md 2>/dev/null | head -1)
  if [ -n "$LAST_REPORT" ]; then
    REPORT+="📄 Son rapor: $(basename "$LAST_REPORT")\n"
  fi
fi

# Lead pipeline durumu
CRM_DB="/home/hermes/.hermes/state.db"
if [ -f "$CRM_DB" ]; then
  LEAD_COUNT=$(sqlite3 "$CRM_DB" "SELECT COUNT(*) FROM outbound_leads WHERE deleted_at IS NULL;" 2>/dev/null || echo "?")
  REPORT+="👥 Pipeline'daki lead sayısı: $LEAD_COUNT\n"
fi

echo -e "$REPORT"
exit 0
