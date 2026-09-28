#!/usr/bin/env bash
# followup-reminder.sh — Jeff Outcome Ledger 7+ Gun Takip
# Her gun 09:00'da cron ile calisir.
# outcome-ledger.md'deki durum: testte + bos net_etki olan
# ve 7+ gun once onaylanmis maddeleri stdout'a basar.

set -euo pipefail

INPUT="/opt/hermes/trend-watcher/outcome-ledger.md"
BUGUN=$(date +%s)

[[ ! -f "$INPUT" ]] && exit 0

RESULTS=()
ID=""; DURUM=""; NET=""; TARIH=""; BASLIK=""; KATEGORI=""

flush_entry() {
    [[ -z "$ID" ]] && return
    if [[ "$DURUM" == "testte" && -z "$NET" && -n "$TARIH" && -n "$BASLIK" ]]; then
        tarih_s=$(date -d "$TARIH" +%s 2>/dev/null) || { reset; return; }
        fark=$(( (BUGUN - tarih_s) / 86400 ))
        if [[ $fark -ge 7 ]]; then
            RESULTS+=("$KATEGORI|$BASLIK|$TARIH|$fark")
        fi
    fi
    reset
}

reset() { ID=""; DURUM=""; NET=""; TARIH=""; BASLIK=""; KATEGORI=""; }

while IFS= read -r line || [[ -n "$line" ]]; do
    # Trim leading/trailing whitespace
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"
    # Also strip "- " prefix for YAML list items
    line="${line#- }"
    line="${line#"${line%%[![:space:]]*}"}"

    [[ -z "$line" ]] && continue
    [[ "$line" == \#* || "$line" == \>* || "$line" == \|* ]] && continue

    # Separator -> flush
    if [[ "$line" == "---" ]]; then
        flush_entry
        continue
    fi

    [[ "$line" != *:* ]] && continue

    key="${line%%:*}"
    # Trim key whitespace
    key="${key#"${key%%[![:space:]]*}"}"
    key="${key%"${key##*[![:space:]]}"}"

    val="${line#*:}"
    # Trim leading whitespace
    val="${val#"${val%%[![:space:]]*}"}"
    # Remove surrounding quotes
    val="${val#\"}"
    val="${val%\"}"

    case "$key" in
        id)       ID="$val" ;;
        durum)    DURUM="$val" ;;
        net_etki) NET="$val" ;;
        tarih)    TARIH="$val" ;;
        baslik)   BASLIK="$val" ;;
        kategori) KATEGORI="$val" ;;
    esac
done < "$INPUT"
flush_entry

# Output reminders (silent if none found)
if [[ ${#RESULTS[@]} -gt 0 ]]; then
    printf '📋 **Jeff — 7 Gun Takip**\n'
    for entry in "${RESULTS[@]}"; do
        IFS='|' read -r kat baslik tarih gun <<< "$entry"
        printf '🔴 [%s] %s (%s gun once onaylandi)\nSonuc nasil gitti? (+2/+1/0/-1/-2)\n\n' \
            "$kat" "$baslik" "$gun"
    done
fi
