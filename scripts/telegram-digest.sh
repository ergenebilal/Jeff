#!/usr/bin/env bash
# telegram-digest.sh — Reades approval-queue.md and prints Telegram digest (no_agent cron)
set -euo pipefail
Q=/opt/hermes/trend-watcher/approval-queue.md
[ -f "$Q" ] || exit 0

T=$(mktemp); trap 'rm -f "$T"' EXIT
declare -a ALL_IDS=() DISPLAY_IDS=()

ID=""; BAS=""; KAT=""; SIN=""; GUV=""; ZAM=""; OZ=""; DUR=""; OLU=""; ENTRY=0
save() { echo "ID=$ID|BASLIK=$BAS|KATEGORI=$KAT|SINYAL=$SIN|GUVEN=$GUV|ZAMAN=$ZAM|OZET=$OZ|OLUSTURULMA=$OLU" >> "$T"; }
reset() { ID=""; BAS=""; KAT=""; SIN=""; GUV=""; ZAM=""; OZ=""; DUR=""; OLU=""; }

while IFS= read -r L; do
  if [[ "$L" =~ ^[[:space:]]*-[[:space:]]*id:[[:space:]]([a-f0-9-]+) ]]; then
    [ "$ENTRY" -eq 1 ] && [ "$DUR" = "bekliyor" ] && save
    reset; ID="${BASH_REMATCH[1]}"; ENTRY=1
  elif [ "$ENTRY" -eq 1 ]; then
    [[ "$L" =~ ^[[:space:]]*baslik:[[:space:]]*(.*) ]]       && BAS="${BASH_REMATCH[1]}" || true
    [[ "$L" =~ ^[[:space:]]*kategori:[[:space:]]*(.*) ]]     && KAT="${BASH_REMATCH[1]}" || true
    [[ "$L" =~ ^[[:space:]]*sinyal:[[:space:]]*(.*) ]]      && SIN="${BASH_REMATCH[1]}" || true
    [[ "$L" =~ ^[[:space:]]*jeff_guveni:[[:space:]]*(.*) ]] && GUV="${BASH_REMATCH[1]}" || true
    [[ "$L" =~ ^[[:space:]]*zaman_maliyeti:[[:space:]]*(.*) ]] && ZAM="${BASH_REMATCH[1]}" || true
    [[ "$L" =~ ^[[:space:]]*ozet_tek_satir:[[:space:]]*(.*) ]] && OZ="${BASH_REMATCH[1]}" || true
    [[ "$L" =~ ^[[:space:]]*durum:[[:space:]]*(.*) ]]        && DUR="${BASH_REMATCH[1]}" || true
    [[ "$L" =~ ^[[:space:]]*olusturulma:[[:space:]]*(.*) ]]  && OLU="${BASH_REMATCH[1]}" || true
  fi
done < "$Q"; [ "$ENTRY" -eq 1 ] && [ "$DUR" = "bekliyor" ] && save

# Filter by time window (08:00-22:00), max 5 items — store display IDs
while IFS='|' read -ra F; do
  I=""; U=""
  for G in "${F[@]}"; do case "$G" in ID=*) I="${G#ID=}" ;; OLUSTURULMA=*) U="${G#OLUSTURULMA=}" ;; esac; done
  ALL_IDS+=("$I")
  CH=$(echo "$U" | grep -oP '\b\d{2}(?=:\d{2}$)' 2>/dev/null || echo "99")
  CH=$((10#$CH))
  [ "$CH" -ge 8 ] && [ "$CH" -lt 22 ] && [ ${#DISPLAY_IDS[@]} -lt 5 ] && DISPLAY_IDS+=("$I")
done < "$T"

# Mark ALL bekliyor items as pending_notified
for I in "${ALL_IDS[@]}"; do
  sed -i "/^  - id: $I$/,/^  - id: /s/    durum: bekliyor/    durum: pending_notified/" "$Q"
done

[ ${#DISPLAY_IDS[@]} -eq 0 ] && exit 0
echo "🔥 **Jeff Approval Queue** — ${#DISPLAY_IDS[@]} madde bekliyor"
echo ""

# Re-read temp file for display matching display IDs
while IFS='|' read -ra F; do
  I=""; BAS=""; KAT=""; SIN=""; GUV=""; ZAM=""; OZ=""
  for G in "${F[@]}"; do
    case "$G" in ID=*) I="${G#ID=}" ;; BASLIK=*) BAS="${G#BASLIK=}" ;; KATEGORI=*) KAT="${G#KATEGORI=}" ;;
                  SINYAL=*) SIN="${G#SINYAL=}" ;; GUVEN=*) GUV="${G#GUVEN=}" ;;
                  ZAMAN=*) ZAM="${G#ZAMAN=}" ;; OZET=*) OZ="${G#OZET=}" ;; esac
  done
  # Skip if not in display list
  FOUND=0
  for DI in "${DISPLAY_IDS[@]}"; do [ "$DI" = "$I" ] && FOUND=1 && break; done
  [ "$FOUND" -eq 0 ] && continue

  case "$KAT" in mcp) BAD="🔴 [MCP]" ;; github-repo) BAD="🔴 [github-repo]" ;; model-tooling) BAD="🔴 [model-tooling]" ;; *) BAD="🔴 [$KAT]" ;; esac
  echo "$BAD $BAS ($SIN | güven: $GUV | $ZAM)"
  echo "Özet: $OZ"
  echo "Onayla: /approve $I   Reddet: /reject $I   Ertele: /snooze $I"
  echo ""
done < "$T"
