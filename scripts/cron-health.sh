#!/bin/bash
# cron-health.sh — Cron job'larinin saglik durumunu raporla
# Her saat calisir. Output: /opt/hermes/trend-watcher/cron-health.md

CRON_DIR="$HOME/.hermes/cron/output"
WATCHER_DIR="/opt/hermes/trend-watcher"
NOW=$(date '+%Y-%m-%d %H:%M')
NOW_EPOCH=$(date +%s)
SEC_24H=$((24 * 3600))

# Izlenecek cron job'lari: job_id|isim
JOBS=(
  "4bee9798057f|Trend Watcher"
  "3eb79f5fdbcb|GitHub Elmas"
  "7d03f012feea|Hermes Watchdog"
  "89377f3b0587|Daily Hermes Intel"
  "665c7b313a70|Cron Health"
  "73ecbfc224f3|Approval Queue Builder"
  "44dd336d39fb|Jeff Approval Digest"
  "bc13d2c29b0f|Approval Timeout Sweep"
  "5c553406b3fd|Followup Reminder"
  "859a7eb55ccf|Jeff Learning Refresh"
  "6ff29287e30d|Jeff Weekly Summary"
  "918de696b340|Jeff Monthly Review"
)

report_file="$WATCHER_DIR/cron-health.md"

cat > "$report_file" << EOF
# Cron Health — $NOW

| Job | Son Basarili | Son Hata | Basari/Hata (24h) | Seviye |
|-----|-------------|----------|-------------------|--------|
EOF

declare -a hata_detaylari

for entry in "${JOBS[@]}"; do
  IFS='|' read -r job_id job_name <<< "$entry"
  job_dir="$CRON_DIR/$job_id"

  basari_say=0
  hata_say=0
  son_basarili=""
  son_hata=""
  son_hata_tip=""

  if [ -d "$job_dir" ]; then
    while IFS= read -r file; do
      fname=$(basename "$file")
      # Dosya adindan timestamp al: 2026-07-01_09-02-24.md
      fdate_raw="${fname%.*}"  # 2026-07-01_09-02-24
      # 09-02-24 -> 09:02:24
      fdate_clean="${fdate_raw//-/:}"
      fdate_clean="${fdate_clean/_/ }"
      # Ilk :'den onceki tireleri koru (tarih), sonrakini cevir
      # Basit yaklasim: 2026-07-01_09-02-24 -> 2026-07-01 09:02:24
      fdate_part1="${fdate_raw%_*}"  # 2026-07-01
      fdate_part2="${fdate_raw#*_}"  # 09-02-24
      fdate_part2="${fdate_part2//-/:}"  # 09:02:24
      fepoch=$(date -d "${fdate_part1} ${fdate_part2}" +%s 2>/dev/null || echo 0)
      [ "$fepoch" -eq 0 ] && continue

      # Son 24 saat kontrolu
      age=$((NOW_EPOCH - fepoch))
      [ "$age" -gt "$SEC_24H" ] && continue

      # Icerigi kontrol et
      content=$(cat "$file" 2>/dev/null)
      # Status satirini kontrol et (no_agent cron'lar icin)
      status_line=$(echo "$content" | grep -i "\*\*Status:\*\*" | head -1)
      if [ -n "$status_line" ] && echo "$status_line" | grep -qi "fail\|error\|timeout"; then
        # no_agent script basarisiz
        hata_say=$((hata_say + 1))
        son_hata="$fdate_part1"
        # Hata tipini belirle
        if echo "$content" | grep -qi "timeout"; then
          son_hata_tip="timeout"
        elif echo "$content" | grep -qi "rate.limit\|429\|kota"; then
          son_hata_tip="rate_limit"
        elif echo "$content" | grep -qi "bos\|empty\|bulunamadi"; then
          son_hata_tip="bos_rapor"
        else
          son_hata_tip="bilinmiyor"
        fi
      else
        basari_say=$((basari_say + 1))
        son_basarili="$fdate_part1"
      fi
    done < <(find "$job_dir" -name "*.md" -o -name "*.json" 2>/dev/null | sort -r)
  fi

  # Seviye belirle
  seviye="iyi"
  if [ "$hata_say" -ge 3 ] && [ "$basari_say" -eq 0 ]; then
    seviye="kritik"
  elif [ "$hata_say" -ge 1 ] && [ "$basari_say" -ge 1 ]; then
    seviye="uyari"
  elif [ "$basari_say" -eq 0 ] && [ "$hata_say" -eq 0 ]; then
    # Output yok — art arda 2 kontrol
    if ls "$job_dir"/*.md "$job_dir"/*.json 2>/dev/null | head -5 | grep -q .; then
      seviye="uyari"
    fi
  fi

  # Hata tipini aciklamaya cevir
  hata_aciklama=""
  case "$son_hata_tip" in
    timeout)    hata_aciklama="OpenCode yanit vermedi, model veya ag sorunu." ;;
    rate_limit) hata_aciklama="GitHub/API limitine takildi, tarama eksik." ;;
    bos_rapor)  hata_aciklama="Model yanit dondurdu ama anlamli icerik yok." ;;
    bilinmiyor) hata_aciklama="Bilinmeyen hata, log kontrol edilmeli." ;;
  esac

  son_basarili_str="${son_basarili:-yok}"
  son_hata_str="${son_hata:-yok}"
  basari_hata="$basari_say / $hata_say"

  # Rapor satiri
  echo "| $job_name | $son_basarili_str | $son_hata_str | $basari_hata | $seviye |" >> "$report_file"

  # Hata detayi varsa biriktir
  if [ "$seviye" != "iyi" ] && [ -n "$son_hata_tip" ]; then
    hata_detaylari+=("- $job_name: $son_hata_str — $hata_aciklama")
  fi
done

# Hata detaylari
if [ ${#hata_detaylari[@]} -gt 0 ]; then
  cat >> "$report_file" << 'EOF'

## Hata Detaylari
EOF
  for detay in "${hata_detaylari[@]}"; do
    echo "$detay" >> "$report_file"
  done
fi

echo "[OK] Cron health raporu yazildi: $report_file"
