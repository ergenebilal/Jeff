#!/bin/bash
# NotebookLM Health Check — v2 (09.10.2026 kök neden düzeltmesi)
#
# v1 HATASI: MCP'nin GERÇEK oturum deposu kalıcı Chrome profilidir
#   (/home/hermes/chrome_profile_notebooklm — bkz. /home/hermes/nblm/config.json
#    "profile_dir"). Ama v1 bekçisi var olmayan eski yolu kontrol ediyordu:
#   ~/.notebooklm-mcp-cli/profiles/default/cookies.json
#   -> 29.09'dan beri her turda SAHTE "cookie eksik / CRITICAL" alarmı üretti,
#      oysa gerçek oturum canlıydı (tarayıcı ayakta, NotebookLM sekmeleri açık).
#
# v2: gerçek sinyali ölçer:
#   1) Kalıcı Chrome (CDP 18800) ayakta mı? Değilse nlm-chrome'u otonom kaldırır.
#   2) Oturum açık bir NotebookLM/Gemini Notebook sekmesi var mı?
#      (notebook.google.com — Google, NotebookLM'i "Gemini Notebook" olarak
#       yeniden adlandırdı; eski notebooklm.google.com da kabul edilir.)
#   3) Sekme yoksa: tarayıcı ayakta + profil cookie DB taze ise OK say (yanlış alarmı önler).
# Alarm YALNIZCA gerçek kayıpta üretilir.
set -uo pipefail
LOG="$HOME/logs/notebooklm-health.log"
CDP_URL="${NLM_CDP_URL:-http://127.0.0.1:18800}"
PROFILE_DIR="$HOME/chrome_profile_notebooklm"
PROFILE_COOKIES="$PROFILE_DIR/Default/Cookies"
BACKUP_DIR="$HOME/.notebooklm-mcp-cli/profiles/default/backup_ha"
mkdir -p "$(dirname "$LOG")" "$BACKUP_DIR"

TELEGRAM_TOKEN=$(grep TELEGRAM_BOT_TOKEN ~/.hermes/gateway.env 2>/dev/null | cut -d= -f2 | tr -d "\r" | head -1)
CHAT_ID="${TELEGRAM_OWNER_CHAT_ID:-${TELEGRAM_CHAT_ID:-}}"

send_proaktif() {
  local level="$1" msg="$2"
  local body="JEFF PROAKTIF BILDIRIM - NotebookLM [$level] $(date '+%d.%m %H:%M') $msg"
  if [ -n "$TELEGRAM_TOKEN" ] && [ -n "$CHAT_ID" ] && [ "${NLM_DRY_RUN:-0}" != "1" ]; then
    curl -s "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" -d "chat_id=${CHAT_ID}" -d "text=${body}" > /dev/null 2>&1 || true
  fi
  echo "$(date -Iseconds) $level: $msg" >> "$LOG"
}

cdp_ok() { timeout 8 curl -s -o /dev/null -w "%{http_code}" "$CDP_URL/json/version" 2>/dev/null | grep -q 200; }

# 0) Günlük profil cookie yedeği (HA)
if [ -f "$PROFILE_COOKIES" ]; then
  DAY=$(date +%Y%m%d)
  if [ ! -f "$BACKUP_DIR/profile-cookies-$DAY.db" ]; then
    cp "$PROFILE_COOKIES" "$BACKUP_DIR/profile-cookies-$DAY.db" 2>/dev/null || true
    find "$BACKUP_DIR" -name "profile-cookies-*.db" -mtime +14 -delete 2>/dev/null || true
  fi
fi

# 1) Kalıcı Chrome ayakta mı? Değilse otonom kaldır.
if ! cdp_ok; then
  echo "$(date -Iseconds) WARN: CDP yok, nlm-chrome restart deneniyor" >> "$LOG"
  # Otonom onarım yalnız gerçek servis için (test amaçlı özel URL'de tetiklenmez)
  if [ "$CDP_URL" = "http://127.0.0.1:18800" ]; then
    systemctl --user restart nlm-chrome >/dev/null 2>&1 || true
    sleep 12
  fi
  if ! cdp_ok; then
    send_proaktif "CRITICAL L4" "Olay: Kalici NotebookLM tarayicisi (CDP 18800) ayakta DEGIL ve restart basarisiz. Analiz: oturum deposuna erisilemiyor. Oneri: systemctl --user status nlm-chrome"
    exit 1
  fi
  echo "$(date -Iseconds) OTO-ONARIM: nlm-chrome yeniden baslatildi, CDP geri geldi" >> "$LOG"
fi

# 2) Oturum açık NotebookLM/Gemini Notebook sekmesi var mı?
TARGETS=$(timeout 10 curl -s "$CDP_URL/json/list" 2>/dev/null || true)
if printf '%s' "$TARGETS" | grep -qE '"url": "https://(notebooklm|notebook)\.google\.com'; then
  echo "$(date -Iseconds) OK: oturum canli (kalici tarayici + NotebookLM sekmesi)" >> "$LOG"
  exit 0
fi

# 3) Giriş sayfası görülüyorsa oturum düşmüş demektir
if printf '%s' "$TARGETS" | grep -qE 'accounts\.google\.com|/signin'; then
  send_proaktif "CRITICAL L4" "Olay: NotebookLM oturumu DUSTU (giris sayfasi goruldu). Oneri: noVNC ekranindan Google girisi yenile (http://100.124.217.48:6080/vnc.html)."
  exit 1
fi

# 4) Sekme yok ama tarayıcı ayakta: profil cookie DB taze ise oturum muhtemelen canlı
if [ -f "$PROFILE_COOKIES" ]; then
  AGE_D=$(( ( $(date +%s) - $(stat -c %Y "$PROFILE_COOKIES") ) / 86400 ))
  if [ "$AGE_D" -lt 14 ]; then
    echo "$(date -Iseconds) OK: oturum canli (profil cookie DB ${AGE_D} gun taze; sekme gozlenmedi)" >> "$LOG"
    exit 0
  fi
fi

send_proaktif "HIGH L3" "Olay: Tarayici ayakta ama NotebookLM sekmesi ve taze profil cookie DB yok. Oneri: noVNC ekranindan kontrol et (http://100.124.217.48:6080/vnc.html)."
exit 1
