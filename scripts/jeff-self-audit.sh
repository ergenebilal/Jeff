#!/usr/bin/env bash
# Jeff Self-Audit v2.0 — sistem sagligi + performans metrikleri
set -e

LOG="/home/hermes/.hermes/cron/self-audit.log"
METRICS_FILE="/home/hermes/.hermes/data/jeff_metrics.json"
mkdir -p "$(dirname "$LOG")" "$(dirname "$METRICS_FILE")"
echo "=== $(date -Iseconds) ===" >> "$LOG"

ISSUES=0

# 1. Hermes process ayakta mi?
if ! pgrep -x python3 > /dev/null 2>&1; then
    echo "CRITICAL: python3 process not found" >> "$LOG"
    ISSUES=$((ISSUES+1))
fi

# 2. Disk >80%?
DISK_USE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USE" -gt 85 ]; then
    echo "WARN: Disk $DISK_USE% used" >> "$LOG"
    ISSUES=$((ISSUES+1))
fi

# 3. RAM >90%?
RAM_USE=$(free | grep Mem | awk '{print $3/$2 * 100.0}' | cut -d. -f1)
if [ "$RAM_USE" -gt 90 ]; then
    echo "WARN: RAM $RAM_USE% used" >> "$LOG"
    ISSUES=$((ISSUES+1))
fi

# 4. Son haftada cron hatasi var mi?
ERROR_COUNT=$(hermes cron list 2>/dev/null | grep -c "error\|fail" || true)
if [ "$ERROR_COUNT" -gt 0 ]; then
    echo "WARN: $ERROR_COUNT cron errors detected" >> "$LOG"
    ISSUES=$((ISSUES+1))
fi

# 5. TZ dogru mu?
TZ_HOUR=$(TZ='Europe/Istanbul' date '+%H')
if [ "$TZ_HOUR" -lt 0 ] 2>/dev/null || [ "$TZ_HOUR" -gt 23 ] 2>/dev/null; then
    echo "CRITICAL: TZ issue detected" >> "$LOG"
    ISSUES=$((ISSUES+1))
fi

# ----- YENI METRIKLER (Mudahale 7) -----

# 6. Skill guncelleme yasi (gun cinsinden en eski guncellenmemis skill)
OLDEST_SKILL_AGE=$(find /home/hermes/.hermes/skills -name "SKILL.md" -exec stat --format='%Y' {} \; 2>/dev/null | sort | head -1)
if [ -n "$OLDEST_SKILL_AGE" ]; then
    NOW_EPOCH=$(date +%s)
    SKILL_AGE_DAYS=$(( (NOW_EPOCH - OLDEST_SKILL_AGE) / 86400 ))
else
    SKILL_AGE_DAYS=0
fi

# 7. Memory kullanim sayisi (gunluk)
MEMORY_WRITES=$(find /home/hermes/.hermes/logs -name "memory*.log" -newermt "$(date +%Y-%m-%d)" 2>/dev/null | wc -l)
if [ "$MEMORY_WRITES" -eq 0 ]; then
    MEMORY_WRITES=$(grep -c "memory_write\|memory_action\|memory.*add" /home/hermes/.hermes/logs/self_health.jsonl 2>/dev/null || echo 0)
fi

# 8. Proaktif eylem sayisi (gunluk)
PROACTIVE_COUNT=$(grep -c "proactive\|suggest_next\|background_review\|otonom" /home/hermes/.hermes/logs/self_improve_loop.jsonl 2>/dev/null || echo 0)

# 9. Yanlis anlama sayisi (gunluk - "yanlis anladin" veya "hayir" duzeltmeleri)
MISUNDERSTAND_COUNT=$(grep -c "yanlis anladin\|yanlis anladim\|hayir.*oyle degil\|hayır.*öyle değil\|ben.*demedim\|ben.*soylemedim" /home/hermes/.hermes/logs/self_health.jsonl 2>/dev/null || echo 0)

# Metrikleri JSON'a kaydet
cat > "$METRICS_FILE" << METEOF
{
  "timestamp": "$(date -Iseconds)",
  "disk_use_pct": $DISK_USE,
  "ram_use_pct": $RAM_USE,
  "cron_error_count": $ERROR_COUNT,
  "skill_guncelleme_yasi_gun": $SKILL_AGE_DAYS,
  "memory_kullanim_sayisi": $MEMORY_WRITES,
  "proaktif_eylem_sayisi": $PROACTIVE_COUNT,
  "yanlis_anlama_sayisi": $MISUNDERSTAND_COUNT
}
METEOF

echo "Issues found: $ISSUES" >> "$LOG"
echo "Healthy: $([ $ISSUES -eq 0 ] && echo 'YES' || echo 'NO')" >> "$LOG"

# Output only if issues found
if [ $ISSUES -gt 0 ]; then
    echo "WARNING: Jeff Self-Audit: $ISSUES issue(s) found at $(TZ='Europe/Istanbul' date '+%H:%M')"
    tail -5 "$LOG"
fi
