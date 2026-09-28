#!/bin/bash
# NotebookLM Auth Check — HA v3 (14.09.2026 kök neden düzeltmesi)
# v2 hatası: "network_error" içeren HER hata sessizce yutuluyordu; oysa nlm bu mesajı
# ClientAuthenticationError için de basıyordu -> oturum ölüyken bekçi "sorun yok" diyordu.
# v3: önce GERÇEK ağ testi yapılır; ağ varsa ve kimlik reddediliyorsa alarm üretilir.
set -uo pipefail
LOG="$HOME/logs/notebooklm-health.log"
COOKIES="$HOME/.notebooklm-mcp-cli/profiles/default/cookies.json"
mkdir -p "$(dirname "$LOG")"
TELEGRAM_TOKEN=$(grep TELEGRAM_BOT_TOKEN ~/.hermes/gateway.env 2>/dev/null | cut -d= -f2 | tr -d "\r" | head -1)
CHAT_ID="5506784207"
send_proaktif() {
  local level="$1" msg="$2"
  local body="JEFF PROAKTIF BILDIRIM - NotebookLM [$level] $(date '+%d.%m %H:%M') $msg"
  if [ -n "$TELEGRAM_TOKEN" ] && [ "${NLM_DRY_RUN:-0}" != "1" ]; then
    curl -s "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" -d "chat_id=${CHAT_ID}" -d "text=${body}" > /dev/null 2>&1 || true
  fi
  echo "$(date -Iseconds) $level: $msg" >> "$LOG"
}

# 1) MCP süreci
MCP_PID=$(pgrep -f "notebooklm-mcp" 2>/dev/null | head -1)
if [ -z "$MCP_PID" ]; then
  echo "$(date -Iseconds) CRITICAL: MCP dead, auto-restart" >> "$LOG"
  systemctl --user restart hermes-serve 2>> "$LOG" || true
  sleep 8
  MCP_PID2=$(pgrep -f "notebooklm-mcp" 2>/dev/null | head -1)
  if [ -n "$MCP_PID2" ]; then
    send_proaktif "HIGH L3" "Olay: MCP OLDU restart edildi. Analiz: Process yoktu hermes-serve restart ile kalkti PID $MCP_PID2. Otonom: OK. Oneri: Log kontrol et."
    exit 0
  fi
  send_proaktif "CRITICAL L4" "Olay: MCP OLDU restart BASARISIZ! Analiz: MCP gelmedi organ DURDU. Oneri: systemctl --user status hermes-serve kontrol!"
  exit 1
fi

# 2) GERÇEK ağ testi (auth hatası ile ağ hatasını ayır)
NET_OK=0
code=$(timeout 15 curl -s -o /dev/null -w "%{http_code}" https://notebooklm.google.com 2>/dev/null || echo 000)
case "$code" in 2*|3*|4*) NET_OK=1 ;; *) NET_OK=0 ;; esac

# 3) Kimlik doğrulaması (gerçek çağrı)
AUTH_CHECK=$(timeout 40 nlm login --check 2>&1)
AUTH_EXIT=$?
if [ $AUTH_EXIT -eq 0 ]; then
  # oturum canlı: dosya tazeliğini de kaydet (gözlem amaçlı)
  if [ -f "$COOKIES" ]; then
    COUNT=$(python3 -c "import json;print(len(json.load(open('$COOKIES'))))" 2>/dev/null || echo 0)
    AGE_H=$(( ($(date +%s) - $(stat -c %Y "$COOKIES")) / 3600 ))
    echo "$(date -Iseconds) OK: oturum canli ($COUNT cookie, dosya ${AGE_H}sa once guncellendi)" >> "$LOG"
  else
    echo "$(date -Iseconds) OK: oturum canli (cookies.json yok - farkli depo)" >> "$LOG"
  fi
  exit 0
fi

if [ "$NET_OK" -eq 0 ]; then
  echo "$(date -Iseconds) SESSIZ L0: gercek ag sorunu (http=$code) - MCP $MCP_PID yasiyor" >> "$LOG"
  exit 0
fi

# 4) Ağ var + kimlik reddedildi = GERÇEK ARIZA
DETAIL=$(echo "$AUTH_CHECK" | head -1)
# Önce OTOMATİK İYİLEŞTİRME: kalıcı Chrome (CDP) canlıysa oturumu oradan tazele.
CDP_OK=0
if timeout 8 curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:18800/json/version 2>/dev/null | grep -q 200; then CDP_OK=1; fi
if [ "$CDP_OK" -eq 1 ]; then
  echo "$(date -Iseconds) OTO-ONARIM: CDP tarayici canli, oturum tazeleniyor" >> "$LOG"
  if timeout 120 nlm login --provider openclaw --cdp-url http://127.0.0.1:18800 >> "$LOG" 2>&1; then
    if timeout 40 nlm login --check >> "$LOG" 2>&1; then
      send_proaktif "HIGH L3" "Olay: NotebookLM oturumu dusmustu. Analiz: kalici tarayicidan (CDP) otomatik tazelendi. Otonom: COZULDU, mudahale gerekmedi."
      exit 0
    fi
  fi
  send_proaktif "CRITICAL L4" "Olay: oturum dustu ve CDP tazeleme BASARISIZ. Detay: $DETAIL Oneri: noVNC ekranindan Google girisi yenile (http://100.124.217.48:6080/vnc.html)."
  exit 1
fi

DETAIL=$(echo "$AUTH_CHECK" | head -1)
if echo "$AUTH_CHECK" | grep -qiE "expired|stale|401|403|unauthor"; then
  send_proaktif "CRITICAL L4" "Olay: NotebookLM oturumu GECERSIZ (ag saglam, http=$code) ve kalici tarayici KAPALI. Detay: $DETAIL Oneri: systemctl --user start nlm-chrome nlm-vnc nlm-novnc, sonra noVNC'den giris."
else
  send_proaktif "HIGH L3" "Olay: nlm login --check basarisiz (ag saglam). Detay: $DETAIL Oneri: 'nlm doctor' calistir."
fi
exit 1
