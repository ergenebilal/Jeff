#!/usr/bin/env bash
# 🔔 JEFF PROAKTİF BİLDİRİM — CLEANUP
# Auto-Maintenance & Clean-up Listener (DRY-RUN — asla silmez, sadece raporlar)
# Jeff OS v1.1 Proactive — OPS worker
# Çalıştır: bash /home/hermes/scripts/jeff-proactive-cleanup.sh [--json]

set -euo pipefail

# ── Ayarlar ──────────────────────────────────────────────────────────
DISK_WARN_PCT=80        # % üzeri uyarı
DISK_CRIT_PCT=90        # % üzeri kritik
LOG_AGE_DAYS=30         # bu günden eski = aday
BACKUP_MAX_AGE_DAYS=7   # backup bu günden eskiyse bayat
TMP_DIRS=("/tmp" "$HOME/.hermes/cron/output")
BACKUP_DIR="/opt/backups/data"
BACKUP_PATTERN="*.tar.gz"

OUTPUT_JSON=false
[[ "${1:-}" == "--json" ]] && OUTPUT_JSON=true

TS="$(date '+%Y-%m-%d %H:%M:%S %Z')"
HOST="$(hostname 2>/dev/null || echo unknown)"

# ── Yardımcılar ──────────────────────────────────────────────────────
human_age() {
  # $1 = epoch seconds
  local now epoch diff d h
  now=$(date +%s)
  epoch="$1"
  diff=$(( now - epoch ))
  d=$(( diff / 86400 ))
  h=$(( (diff % 86400) / 3600 ))
  if   (( d > 0 )); then echo "${d}g ${h}s önce"
  elif (( h > 0 )); then echo "${h}s önce"
  else echo "$(( diff / 60 ))dk önce"
  fi
}

bytes_human() {
  # $1 = bytes  → human
  numfmt --to=iec --suffix=B "$1" 2>/dev/null || echo "${1}B"
}

# ── Rapor toplanır ───────────────────────────────────────────────────
TMP_REPORT="$(mktemp)"

cleanup_tmp() { rm -f "$TMP_REPORT"; }
trap cleanup_tmp EXIT

echo "🔔 JEFF PROAKTİF BİLDİRİM — CLEANUP" >> "$TMP_REPORT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$TMP_REPORT"
echo "Tarih : $TS" >> "$TMP_REPORT"
echo "Host  : $HOST" >> "$TMP_REPORT"
echo "Mod   : DRY-RUN (silme yapılmaz)" >> "$TMP_REPORT"
echo "" >> "$TMP_REPORT"

# ═══════════════════════════════════════════════════════════════════════
# 1) DİSK DOLULUĞU — df
# ═══════════════════════════════════════════════════════════════════════
echo "━━━ [1/4] DİSK DOLULUĞU (df -h) ━━━" >> "$TMP_REPORT"

DF_RAW="$(df -h 2>&1)"
echo "$DF_RAW" >> "$TMP_REPORT"
echo "" >> "$TMP_REPORT"

# df -P ile parse (POSIX)
DISK_STATUS="OK"
DISK_ALERTS=()

while IFS= read -r line; do
  # header atla
  [[ "$line" == Filesystem* ]] && continue
  # son % kolonunu al
  pct="$(echo "$line" | awk '{for(i=1;i<=NF;i++) if($i ~ /%$/) {gsub(/%/,"",$i); print $i; exit}}')"
  mnt="$(echo "$line" | awk '{print $NF}')"
  fs="$(echo "$line" | awk '{print $1}')"
  [[ -z "$pct" ]] && continue
  if (( pct >= DISK_CRIT_PCT )); then
    DISK_STATUS="KRİTİK"
    DISK_ALERTS+=("  🔴 KRİTİK  $fs → $mnt %$pct dolu (eşik %$DISK_CRIT_PCT)")
  elif (( pct >= DISK_WARN_PCT )); then
    [[ "$DISK_STATUS" != "KRİTİK" ]] && DISK_STATUS="UYARI"
    DISK_ALERTS+=("  🟡 UYARI   $fs → $mnt %$pct dolu (eşik %$DISK_WARN_PCT)")
  fi
done <<< "$(df -P 2>/dev/null || df -h 2>/dev/null)"

if [[ "$DISK_STATUS" == "OK" ]]; then
  echo "  ✅ Disk durumu: OK — tüm mountlar %$DISK_WARN_PCT altında." >> "$TMP_REPORT"
else
  echo "  Durum: $DISK_STATUS" >> "$TMP_REPORT"
  for a in "${DISK_ALERTS[@]}"; do echo "$a" >> "$TMP_REPORT"; done
  echo "" >> "$TMP_REPORT"
  echo "  → Öneri (dry-run): büyük dosyaları tespit için:" >> "$TMP_REPORT"
  echo "       du -sh /* 2>/dev/null | sort -rh | head -15" >> "$TMP_REPORT"
  echo "       du -sh ~/.cache/* ~/.hermes/* /var/log/* 2>/dev/null | sort -rh | head -15" >> "$TMP_REPORT"
fi
echo "" >> "$TMP_REPORT"

# Ek: inode
echo "  Inode (df -i):" >> "$TMP_REPORT"
df -i 2>/dev/null | head -10 >> "$TMP_REPORT" || echo "  (df -i alınamadı)" >> "$TMP_REPORT"
echo "" >> "$TMP_REPORT"

# ═══════════════════════════════════════════════════════════════════════
# 2) ESKİ LOGLAR — /tmp ve ~/.hermes/cron/output (30+ gün)
# ═══════════════════════════════════════════════════════════════════════
echo "━━━ [2/4] ESKİ LOGLAR (>${LOG_AGE_DAYS} gün) ━━━" >> "$TMP_REPORT"

for DIR in "${TMP_DIRS[@]}"; do
  echo "" >> "$TMP_REPORT"
  echo "  📁 $DIR" >> "$TMP_REPORT"

  if [[ ! -d "$DIR" ]]; then
    echo "     ⚠️  Dizin yok — atlandı." >> "$TMP_REPORT"
    continue
  fi

  # Toplam dosya sayısı
  total_cnt="$( { find "$DIR" -type f 2>/dev/null || true; } | wc -l | tr -d ' ')"
  echo "     Toplam dosya: $total_cnt" >> "$TMP_REPORT"

  # 30+ gün eski dosyalar (dry-run listesi)
  OLD_LIST="$(mktemp)"
  find "$DIR" -type f -mtime +"$LOG_AGE_DAYS" -printf '%T@ %p %s\n' 2>/dev/null | sort -n > "$OLD_LIST" || true
  old_cnt="$(wc -l < "$OLD_LIST" | tr -d ' ')"

  if (( old_cnt == 0 )); then
    echo "     ✅ ${LOG_AGE_DAYS}+ günlük eski dosya yok." >> "$TMP_REPORT"
  else
    old_bytes="$(awk '{sum+=$NF} END{print sum+0}' "$OLD_LIST")"
    old_human="$(bytes_human "$old_bytes")"
    echo "     🟡 ${LOG_AGE_DAYS}+ günlük aday: $old_cnt dosya → $old_human (dry-run, silinmedi)" >> "$TMP_REPORT"
    echo "     İlk 20 aday (en eski → yeni):" >> "$TMP_REPORT"
    head -20 "$OLD_LIST" | while read -r epoch path size; do
      # epoch float olabilir
      epoch_int="${epoch%.*}"
      age="$(human_age "$epoch_int" 2>/dev/null || echo "?")"
      hsize="$(bytes_human "$size" 2>/dev/null || echo "${size}B")"
      printf "       - %s  (%s, %s)  age:%s\n" "$path" "$hsize" "$epoch" "$age" >> "$TMP_REPORT"
    done
    if (( old_cnt > 20 )); then
      echo "       ... ve $(( old_cnt - 20 )) dosya daha (tam liste: find $DIR -type f -mtime +$LOG_AGE_DAYS)" >> "$TMP_REPORT"
    fi
    echo "" >> "$TMP_REPORT"
    echo "     → Temizlemek için (manuel, DRY-RUN sonrası):" >> "$TMP_REPORT"
    echo "       find $DIR -type f -mtime +$LOG_AGE_DAYS -print   # kontrol" >> "$TMP_REPORT"
    echo "       find $DIR -type f -mtime +$LOG_AGE_DAYS -delete  # sil (dikkatli!)" >> "$TMP_REPORT"
  fi
  rm -f "$OLD_LIST"

  # Ayrıca /tmp için 7+ gün uyarısı
  if [[ "$DIR" == "/tmp" ]]; then
    week_cnt="$( { find "$DIR" -type f -mtime +7 2>/dev/null || true; } | wc -l | tr -d ' ')"
    echo "     (bilgi) 7+ günlük dosya: $week_cnt" >> "$TMP_REPORT"
  fi
done
echo "" >> "$TMP_REPORT"

# ═══════════════════════════════════════════════════════════════════════
# 3) BACKUP TAZELİĞİ — /opt/backups/data/*.tar.gz
# ═══════════════════════════════════════════════════════════════════════
echo "━━━ [3/4] BACKUP TAZELİĞİ ($BACKUP_DIR/$BACKUP_PATTERN) ━━━" >> "$TMP_REPORT"

if [[ ! -d "$BACKUP_DIR" ]]; then
  echo "  ⚠️  Backup dizini yok: $BACKUP_DIR" >> "$TMP_REPORT"
  echo "  → Öneri: mkdir -p $BACKUP_DIR && backup job kontrolü yap." >> "$TMP_REPORT"
else
  # nullglob benzeri
  backup_files=()
  while IFS= read -r -d '' f; do backup_files+=("$f"); done < <(find "$BACKUP_DIR" -maxdepth 1 -name "$BACKUP_PATTERN" -type f -print0 2>/dev/null | sort -z)

  if (( ${#backup_files[@]} == 0 )); then
    echo "  🔴 Hiç backup bulunamadı! ($BACKUP_DIR/$BACKUP_PATTERN)" >> "$TMP_REPORT"
    echo "  → Acil: backup job çalışmıyor olabilir." >> "$TMP_REPORT"
  else
    echo "  Toplam backup: ${#backup_files[@]}" >> "$TMP_REPORT"
    echo "" >> "$TMP_REPORT"
    # En yeni backup
    newest="$(find "$BACKUP_DIR" -maxdepth 1 -name "$BACKUP_PATTERN" -type f -printf '%T@ %p\n' 2>/dev/null | sort -rn | head -1)"
    newest_epoch="${newest%% *}"
    newest_path="${newest#* }"
    newest_epoch_int="${newest_epoch%.*}"
    newest_age_days=$(( ($(date +%s) - newest_epoch_int) / 86400 ))
    newest_age_human="$(human_age "$newest_epoch_int")"
    newest_size="$(stat -c%s "$newest_path" 2>/dev/null || echo 0)"
    newest_hsize="$(bytes_human "$newest_size")"

    echo "  En yeni backup:" >> "$TMP_REPORT"
    echo "    $newest_path" >> "$TMP_REPORT"
    echo "    Boyut: $newest_hsize | Yaş: $newest_age_human ($newest_age_days gün)" >> "$TMP_REPORT"

    if (( newest_age_days > BACKUP_MAX_AGE_DAYS )); then
      echo "  🔴 BAYAT — en yeni backup ${BACKUP_MAX_AGE_DAYS} günden eski! Backup job bozulmuş olabilir." >> "$TMP_REPORT"
    elif (( newest_age_days > 1 )); then
      echo "  🟡 UYARI — backup $newest_age_days gündür yenilenmemiş (eşik: ${BACKUP_MAX_AGE_DAYS}g)." >> "$TMP_REPORT"
    else
      echo "  ✅ Taze — backup güncel." >> "$TMP_REPORT"
    fi

    echo "" >> "$TMP_REPORT"
    echo "  Son 5 backup:" >> "$TMP_REPORT"
    find "$BACKUP_DIR" -maxdepth 1 -name "$BACKUP_PATTERN" -type f -printf '%T@ %p %s\n' 2>/dev/null | sort -rn | head -5 | while read -r epoch path size; do
      epoch_int="${epoch%.*}"
      age="$(human_age "$epoch_int" 2>/dev/null || echo "?")"
      hsize="$(bytes_human "$size" 2>/dev/null || echo "${size}B")"
      printf "    - %s  %s  (%s)\n" "$(basename "$path")" "$hsize" "$age" >> "$TMP_REPORT"
    done

    # Toplam boyut
    total_bsize="$( { find "$BACKUP_DIR" -maxdepth 1 -name "$BACKUP_PATTERN" -type f -printf '%s\n' 2>/dev/null || true; } | awk '{s+=$1} END{print s+0}')"
    echo "" >> "$TMP_REPORT"
    echo "  Toplam backup boyutu: $(bytes_human "$total_bsize") (${#backup_files[@]} dosya)" >> "$TMP_REPORT"

    # Eski backup adayları — 30+ gün (dry-run)
    old_bk_cnt="$( { find "$BACKUP_DIR" -maxdepth 1 -name "$BACKUP_PATTERN" -type f -mtime +30 2>/dev/null || true; } | wc -l | tr -d ' ')"
    if (( old_bk_cnt > 0 )); then
      echo "  🟡 30+ günlük backup rotasyon adayı: $old_bk_cnt dosya (dry-run)" >> "$TMP_REPORT"
      find "$BACKUP_DIR" -maxdepth 1 -name "$BACKUP_PATTERN" -type f -mtime +30 -printf '    - %p  %s bytes  %TY-%Tm-%Td\n' 2>/dev/null | head -10 >> "$TMP_REPORT"
      echo "  → Rotasyon önerisi (manuel): en eski yedekleri arşivle/silmeden önce doğrula." >> "$TMP_REPORT"
    else
      echo "  ✅ Rotasyon adayı yok (30+ gün)." >> "$TMP_REPORT"
    fi
  fi
fi
echo "" >> "$TMP_REPORT"

# ═══════════════════════════════════════════════════════════════════════
# 4) DOCKER PRUNE ADAYLARI — images / containers / volumes / networks
# ═══════════════════════════════════════════════════════════════════════
echo "━━━ [4/4] DOCKER PRUNE ADAYLARI (dry-run) ━━━" >> "$TMP_REPORT"

if ! command -v docker &>/dev/null; then
  echo "  ⚠️  docker komutu yok — atlandı." >> "$TMP_REPORT"
else
  if ! docker info &>/dev/null; then
    echo "  ⚠️  docker daemon erişilemiyor — atlandı." >> "$TMP_REPORT"
  else
    echo "" >> "$TMP_REPORT"

    # Dangling images
    echo "  🐳 Dangling images (docker image prune --dry-run):" >> "$TMP_REPORT"
    dangling="$(docker images -f "dangling=true" -q 2>/dev/null | wc -l | tr -d ' ')"
    if [[ "$dangling" == "0" || -z "$dangling" ]]; then
      echo "     ✅ Dangling image yok." >> "$TMP_REPORT"
    else
      echo "     🟡 $dangling dangling image (dry-run):" >> "$TMP_REPORT"
      docker images -f "dangling=true" --format '       - {{.Repository}}:{{.Tag}}  {{.ID}}  {{.Size}}' 2>/dev/null | head -20 >> "$TMP_REPORT"
      # Reclaimable size tahmini
      docker system df 2>/dev/null | sed 's/^/     /' >> "$TMP_REPORT" || true
      echo "     → Temizlemek için: docker image prune -f  (dikkatli!)" >> "$TMP_REPORT"
    fi
    echo "" >> "$TMP_REPORT"

    # Exited / dead containers
    echo "  📦 Exited/dead containers:" >> "$TMP_REPORT"
    exited_cnt="$(docker ps -a --filter status=exited --filter status=dead --filter status=created -q 2>/dev/null | wc -l | tr -d ' ')"
    if [[ "$exited_cnt" == "0" || -z "$exited_cnt" ]]; then
      echo "     ✅ Exited/dead container yok." >> "$TMP_REPORT"
    else
      echo "     🟡 $exited_cnt aday (dry-run):" >> "$TMP_REPORT"
      docker ps -a --filter status=exited --filter status=dead --filter status=created --format '       - {{.ID}}  {{.Image}}  {{.Status}}  {{.Names}}' 2>/dev/null | head -20 >> "$TMP_REPORT"
      echo "     → Temizlemek için: docker container prune -f" >> "$TMP_REPORT"
    fi
    echo "" >> "$TMP_REPORT"

    # Unused volumes
    echo "  💾 Unused volumes (docker volume ls -f dangling=true):" >> "$TMP_REPORT"
    vol_cnt="$(docker volume ls -qf dangling=true 2>/dev/null | wc -l | tr -d ' ')"
    if [[ "$vol_cnt" == "0" || -z "$vol_cnt" ]]; then
      echo "     ✅ Dangling volume yok." >> "$TMP_REPORT"
    else
      echo "     🟡 $vol_cnt dangling volume (dry-run):" >> "$TMP_REPORT"
      docker volume ls -f dangling=true 2>/dev/null | sed 's/^/       /' | head -20 >> "$TMP_REPORT"
      echo "     → Temizlemek için: docker volume prune -f  (VERİ KAYBI RİSKİ — doğrula!)" >> "$TMP_REPORT"
    fi
    echo "" >> "$TMP_REPORT"

    # Unused networks
    echo "  🌐 Unused networks:" >> "$TMP_REPORT"
    # docker network prune --dry-run yok eski sürümlerde, filtre ile
    net_ls="$(docker network ls --filter dangling=true 2>/dev/null | tail -n +2 | wc -l | tr -d ' ' || echo 0)"
    # alternatif: docker network prune --filter label yoksa manuel
    if docker network prune --help 2>&1 | grep -q "dry-run"; then
      docker network prune --dry-run 2>/dev/null | sed 's/^/     /' >> "$TMP_REPORT" || true
    else
      if [[ "$net_ls" == "0" || -z "$net_ls" ]]; then
        echo "     ✅ Prune adayı network yok (veya tespit edilemedi)." >> "$TMP_REPORT"
      else
        docker network ls 2>/dev/null | sed 's/^/     /' >> "$TMP_REPORT"
      fi
      echo "     → Temizlemek için: docker network prune -f" >> "$TMP_REPORT"
    fi
    echo "" >> "$TMP_REPORT"

    # Build cache
    echo "  🔨 Build cache:" >> "$TMP_REPORT"
    if docker builder prune --help 2>&1 | grep -q "dry-run"; then
      docker builder prune --dry-run 2>&1 | sed 's/^/     /' | head -30 >> "$TMP_REPORT" || true
    else
      docker system df 2>/dev/null | sed 's/^/     /' >> "$TMP_REPORT" || true
      echo "     → Temizlemek için: docker builder prune -f" >> "$TMP_REPORT"
    fi
    echo "" >> "$TMP_REPORT"

    # Genel özet
    echo "  📊 docker system df (genel):" >> "$TMP_REPORT"
    docker system df 2>/dev/null | sed 's/^/     /' >> "$TMP_REPORT" || echo "     (alınamadı)" >> "$TMP_REPORT"
    echo "" >> "$TMP_REPORT"
    echo "  ⚠️  Tüm docker prune komutları DRY-RUN — hiçbir şey silinmedi." >> "$TMP_REPORT"
    echo "     Gerçek temizlik için tek tek doğrula ve -f ile çalıştır." >> "$TMP_REPORT"
  fi
fi
echo "" >> "$TMP_REPORT"

# ── Özet ─────────────────────────────────────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$TMP_REPORT"
echo "ÖZET — DRY-RUN, hiçbir dosya/container silinmedi." >> "$TMP_REPORT"
echo "Detaylı komutlar rapor içinde listelendi; temizlik manuel onay gerektirir." >> "$TMP_REPORT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >> "$TMP_REPORT"

# ── Çıktı ────────────────────────────────────────────────────────────
if [[ "$OUTPUT_JSON" == true ]]; then
  # JSON için raporu escape et
  REPORT_TEXT="$(cat "$TMP_REPORT")"
  # jq varsa düzgün escape, yoksa basit
  if command -v jq &>/dev/null; then
    jq -n --arg ts "$TS" --arg host "$HOST" --arg report "$REPORT_TEXT" \
      '{timestamp:$ts, host:$host, title:"🔔 JEFF PROAKTİF BİLDİRİM — CLEANUP", mode:"dry-run", report:$report}'
  else
    cat "$TMP_REPORT"
  fi
else
  cat "$TMP_REPORT"
fi
