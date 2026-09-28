#!/bin/bash
set -e
# JEFF PROACTIVE SCOUT — Income & Opportunity Scout
LEAD_MAIN="/home/hermes/lead_pipeline_aktif.json"
POOL_DIS="/home/hermes/pool_dis_top10.json"
POOL_GUZ="/home/hermes/pool_guzellik_ulaşılabilir.json"
STATE_FILE="/home/hermes/state/scout-state.json"
LOG_FILE="/home/hermes/logs/jeff-scout.log"
mkdir -p "$(dirname "$STATE_FILE")" "$(dirname "$LOG_FILE")"
get_cnt(){ [ -f "$1" ] || { echo 0; return; }; jq -r "$2" "$1" 2>/dev/null || echo 0; }
LEAD_TOTAL=$(get_cnt "$LEAD_MAIN" '.toplam_lead // (.leads|length) // 0')
POOL_DIS_CNT=$(get_cnt "$POOL_DIS" 'length // 0')
POOL_GUZ_CNT=$(get_cnt "$POOL_GUZ" 'length // 0')
TOTAL_POOL=$((POOL_DIS_CNT+POOL_GUZ_CNT))
PRIORITY_CNT=$(get_cnt "$LEAD_MAIN" '[.leads[]|select(.oncelik=="oncelikli")]|length')
NEW_CNT=$(get_cnt "$LEAD_MAIN" '[.leads[]|select(.durum=="new")]|length')
PREV_TOTAL=0; PREV_POOL=0
[ -f "$STATE_FILE" ] && PREV_TOTAL=$(jq -r '.lead_total//0' "$STATE_FILE" 2>/dev/null || echo 0)
[ -f "$STATE_FILE" ] && PREV_POOL=$(jq -r '.pool_total//0' "$STATE_FILE" 2>/dev/null || echo 0)
NEW_LEAD=$((LEAD_TOTAL-PREV_TOTAL)); [ "$NEW_LEAD" -lt 0 ] && NEW_LEAD=0
NEW_POOL=$((TOTAL_POOL-PREV_POOL)); [ "$NEW_POOL" -lt 0 ] && NEW_POOL=0
NEW_ALL=$((NEW_LEAD+NEW_POOL))
N8N_STATUS=$(docker inspect n8n --format '{{.State.Status}}' 2>/dev/null || echo unknown)
N8N_FAIL=0; N8N_MSG="UP ($N8N_STATUS)"
[ "$N8N_STATUS" != "running" ] && N8N_FAIL=1 && N8N_MSG="DOWN ($N8N_STATUS)"
if ! curl -sf --max-time 5 https://n8n.aiergene.xyz/healthz >/dev/null 2>&1; then
  curl -sf --max-time 5 http://127.0.0.1:5678/healthz >/dev/null 2>&1 || { N8N_FAIL=1; N8N_MSG="$N8N_MSG + healthz FAIL"; }
fi
DISK_PCT=$(df / | awk 'NR==2{gsub(/%/,"",$5);print $5}')
DISK_AVAIL=$(df -h / | awk 'NR==2{print $4}')
MEM_KB=$(awk '/MemTotal/{print $2}' /proc/meminfo)
RSS_KB=$(ps -eo rss --no-headers | awk '{s+=$1}END{print s+0}')
RSS_MB=$((RSS_KB/1024)); RSS_PCT=$((RSS_KB*100/MEM_KB))
INFRA=""; [ "$DISK_PCT" -ge 85 ] && INFRA="Disk ${DISK_PCT}% dolu! "
[ "$RSS_PCT" -ge 90 ] && INFRA="${INFRA}RAM ${RSS_PCT}% (RSS ${RSS_MB}MB)! "
TRIGGER=0; REASON=""
[ "$NEW_ALL" -gt 0 ] && TRIGGER=1 && REASON="Yeni lead: +${NEW_LEAD} pipeline, +${NEW_POOL} pool"
[ "$N8N_FAIL" -eq 1 ] && TRIGGER=1 && REASON="${REASON:+$REASON; }n8n FAIL ($N8N_MSG)"
[ -n "$INFRA" ] && TRIGGER=1 && REASON="${REASON:+$REASON; }$INFRA"
jq -n --argjson lt "$LEAD_TOTAL" --argjson pt "$TOTAL_POOL" --argjson ts "$(date +%s)" '{lead_total:$lt,pool_total:$pt,updated_at:$ts}' >"$STATE_FILE.tmp" && mv "$STATE_FILE.tmp" "$STATE_FILE"
[ "$TRIGGER" -eq 0 ] && exit 0
TS=$(date '+%d.%m.%Y %H:%M')
POT=$(jq '[.leads[]|select(.durum=="new")]|map(.potansiyel_gelir//10000)|add//0' "$LEAD_MAIN" 2>/dev/null || echo "?")
EXTRA=""; [ -n "$INFRA" ] && EXTRA="Infra uyari var. "
[ "$N8N_FAIL" -eq 1 ] && EXTRA="${EXTRA}n8n kesintisi lead akisini durdurur. "
[ "$NEW_ALL" -gt 0 ] && EXTRA="${EXTRA}Yeni leadler temas bekliyor - gecikme kayip demek."
AKSI=""; [ "$N8N_FAIL" -eq 1 ] && AKSI="n8n docker status kontrol edildi. "
ONERI=""; [ "$NEW_ALL" -gt 0 ] && ONERI="-> ${NEW_LEAD} yeni leade 24s icinde ulas (oncelikliden basla). "
[ "$N8N_FAIL" -eq 1 ] && ONERI="${ONERI}-> n8n kontrol: docker restart n8n + healthz. "
[ -n "$INFRA" ] && ONERI="${ONERI}-> Disk/RAM temizligi yap. "
cat <<EOF
🔔 JEFF PROAKTİF BİLDİRİM — SCOUT ($TS)

▸ Olay: ${REASON}
  • Pipeline: ${LEAD_TOTAL} lead (${NEW_CNT} new, ${PRIORITY_CNT} oncelikli) — onceki: ${PREV_TOTAL} → +${NEW_LEAD}
  • Pool: ${TOTAL_POOL} (dis:${POOL_DIS_CNT} + guzellik:${POOL_GUZ_CNT}) onceki: ${PREV_POOL} → +${NEW_POOL}
  • n8n: ${N8N_MSG}
  • Infra: Disk ${DISK_PCT}% (${DISK_AVAIL} bos) | RAM ${RSS_PCT}% RSS=${RSS_MB}MB / $((MEM_KB/1024))MB

▸ Analiz: Potansiyel (new): ~${POT} TL. ${EXTRA}

▸ Otonom Aksiyon: State guncellendi (${STATE_FILE}). ${AKSI}Log yazildi.

▸ Onerilen Insan Aksiyonu: ${ONERI}-> lead_pipeline_aktif.json dan siradaki 3 leadi ara.
EOF
echo "$(date '+%F %T') SCOUT trigger: $REASON | lead=${LEAD_TOTAL} pool=${TOTAL_POOL} n8n=${N8N_STATUS} disk=${DISK_PCT}% ram=${RSS_PCT}%" >>"$LOG_FILE"
