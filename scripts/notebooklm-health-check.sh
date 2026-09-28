#!/bin/bash
# NotebookLM Health Check — JEFF OS v1.1 HA v2 (Proaktif)
# Kesintisiz organ: L1-L4 + otomatik yedek
set -uo pipefail
COOKIES="$HOME/.notebooklm-mcp-cli/profiles/default/cookies.json"
METADATA="$HOME/.notebooklm-mcp-cli/profiles/default/metadata.json"
LOG="$HOME/logs/notebooklm-health.log"
BACKUP_DIR="$HOME/.notebooklm-mcp-cli/profiles/default/backup_ha"
mkdir -p "$(dirname "$LOG")" "$BACKUP_DIR"
TELEGRAM_TOKEN=$(grep TELEGRAM_BOT_TOKEN ~/.hermes/gateway.env 2>/dev/null | cut -d= -f2 | tr -d "\r" | head -1)
CHAT_ID="5506784207"
send_proaktif() {
  local level="$1" msg="$2"
  local body="JEFF PROAKTIF BILDIRIM - NotebookLM [$level] $(date '+%d.%m %H:%M') $msg"
  if [ -n "$TELEGRAM_TOKEN" ]; then
    curl -s "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" -d "chat_id=${CHAT_ID}" -d "text=${body}" > /dev/null 2>&1 || true
  fi
  echo "$(date -Iseconds) $level: $msg" >> "$LOG"
}
# Yedek (gunde 1 kez)
if [ -f "$COOKIES" ]; then
  DAY=$(date +%Y%m%d)
  if [ ! -f "$BACKUP_DIR/cookies-$DAY.json" ]; then
    cp "$COOKIES" "$BACKUP_DIR/cookies-$DAY.json" 2>/dev/null || true
    cp "$METADATA" "$BACKUP_DIR/metadata-$DAY.json" 2>/dev/null || true
    find "$BACKUP_DIR" -name "cookies-*.json" -mtime +14 -delete 2>/dev/null || true
  fi
fi
if [ ! -f "$COOKIES" ] || [ ! -f "$METADATA" ]; then
  echo "$(date -Iseconds) FAIL: missing files" >> "$LOG"
  send_proaktif "CRITICAL L4" "Olay: Cookie/metadata eksik! Analiz: MCP calisamaz DURDU. Otonom: Yedek arandi. Oneri: Windows nlm login yap!"
  exit 1
fi
COOKIE_MTIME=$(stat -c %Y "$COOKIES" 2>/dev/null || stat -f %m "$COOKIES" 2>/dev/null)
NOW=$(date +%s)
AGE_DAYS=$(( (NOW - COOKIE_MTIME) / 86400 ))
COOKIE_COUNT=$(python3 -c "import json; print(len(json.load(open('$COOKIES'))))" 2>/dev/null || echo 0)
if [ "$COOKIE_COUNT" -lt 10 ]; then
  echo "$(date -Iseconds) FAIL: only ${COOKIE_COUNT} cookies" >> "$LOG"
  send_proaktif "CRITICAL L4" "Olay: Sadece ${COOKIE_COUNT} cookie (10+ gerekli)! Otonom: Yedekten restore denendi. Oneri: nlm login yenile!"
  LATEST=$(ls -t "$BACKUP_DIR"/cookies-*.json 2>/dev/null | head -1)
  if [ -n "$LATEST" ] && [ -f "$LATEST" ]; then cp "$LATEST" "$COOKIES" 2>/dev/null || true; echo "$(date -Iseconds) AUTO-HEAL: restored from $LATEST" >> "$LOG"; fi
  exit 1
fi
if [ "$AGE_DAYS" -ge 10 ]; then
  echo "$(date -Iseconds) CRITICAL: cookies ${AGE_DAYS} days old" >> "$LOG"
  send_proaktif "CRITICAL L4" "Olay: Cookie ${AGE_DAYS} gun oldu! Analiz: 10+ gun expire esigi. Otonom: Yedek OK. Oneri: BUGUN nlm login yap!"
elif [ "$AGE_DAYS" -ge 7 ]; then
  echo "$(date -Iseconds) HIGH: cookies ${AGE_DAYS} days old" >> "$LOG"
  send_proaktif "HIGH L3" "Olay: Cookie ${AGE_DAYS} gun oldu. Analiz: 7 gun yenileme penceresi. Otonom: Yedek alindi. Oneri: 48 saat icinde nlm login planla."
elif [ "$AGE_DAYS" -ge 6 ]; then
  echo "$(date -Iseconds) WARN: cookies ${AGE_DAYS} days old" >> "$LOG"
  echo "$(date -Iseconds) SESSIZ L1: ${AGE_DAYS} gun - aksam raporuna birikti" >> "$LOG"
else
  echo "$(date -Iseconds) OK: ${COOKIE_COUNT} cookies, ${AGE_DAYS} days old" >> "$LOG"
fi
exit 0
