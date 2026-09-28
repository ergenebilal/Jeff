#!/usr/bin/env bash
# Token & Health Dashboard + Worker Metrikleri — no-agent mode
set -uo pipefail

HOME=${HOME:-/home/hermes}
REPORT="💰 **Token & Health Dashboard** — $(date '+%Y-%m-%d %H:%M')\n\n"
ERRORS=0

# 1. opencode-go
OC_TEST=$(curl -sf --max-time 5 https://opencode.ai/zen/go/v1/models 2>/dev/null || echo "FAIL")
if [ "${OC_TEST:0:4}" = "FAIL" ]; then
  REPORT+="❌ opencode-go: ULAŞILAMIYOR\n"
  ERRORS=$((ERRORS+1))
else
  REPORT+="✅ opencode-go: online\n"
fi

# 2. Worker profilleri
REPORT+="\n### Worker Sağlığı\n"
for p in outreach kodcu analyst master kesif scraper; do
  CFG="$HOME/.hermes/profiles/$p/config.yaml"
  if [ -f "$CFG" ]; then
    PROVIDER=$(grep -m1 'provider:' "$CFG" | awk '{print $2}' 2>/dev/null || echo '?')
    REPORT+="✅ $p: $PROVIDER (active)\n"
  else
    REPORT+="❌ $p: config eksik\n"
    ERRORS=$((ERRORS+1))
  fi
done

# 3. Kanban metrikleri
KDB="$HOME/.hermes/kanban/boards/jeff/kanban.db"
if [ -f "$KDB" ]; then
  TOTAL=$(sqlite3 "$KDB" "SELECT COUNT(*) FROM tasks;" 2>/dev/null || echo "0")
  DONE=$(sqlite3 "$KDB" "SELECT COUNT(*) FROM tasks WHERE status='done';" 2>/dev/null || echo "0")
  RUNNING=$(sqlite3 "$KDB" "SELECT COUNT(*) FROM tasks WHERE status='running';" 2>/dev/null || echo "0")
  READY=$(sqlite3 "$KDB" "SELECT COUNT(*) FROM tasks WHERE status='ready';" 2>/dev/null || echo "0")
  REPORT+="\n### Kanban Board (Jeff 2.0)\n"
  REPORT+="| Durum | Sayı |\n|-------|:----:|\n"
  REPORT+="| ✅ Tamamlanan | $DONE |\n| 🔄 Çalışan | $RUNNING |\n| ▶️ Bekleyen | $READY |\n| 📦 Toplam | $TOTAL |\n"
  REPORT+="\n### Worker Performans\n| Worker | Tamamlanan |\n|--------|:----------:|\n"
  for p in outreach kodcu analyst master kesif scraper; do
    C=$(sqlite3 "$KDB" "SELECT COUNT(*) FROM tasks WHERE assignee='$p' AND status='done';" 2>/dev/null || echo "0")
    REPORT+="| $p | $C |\n"
  done
else
  REPORT+="❌ Kanban DB bulunamadi\n"
  ERRORS=$((ERRORS+1))
fi

# 4. Memory
MF="$HOME/.hermes/MEMORY.md"
if [ -f "$MF" ]; then
  SIZE=$(wc -c < "$MF" 2>/dev/null || echo 0)
  LINES=$(wc -l < "$MF" 2>/dev/null || echo 0)
  REPORT+="\n### Memory\n"
  REPORT+="MEMORY.md: $(awk "BEGIN{printf \"%.1f\", $SIZE/1024}")KB / ${LINES} satir\n"
fi

# 5. Maliyet
REPORT+="\n### Maliyet\n| Kaynak | Maliyet |\n|--------|:-------:|\n"
REPORT+="| default profile | \$0 🟢 |\n| 6 worker profil | \$0 🟢 |\n"
REPORT+="| Kanban dispatch | \$0 🟢 |\n| No-agent cron'lar | \$0 🟢 |\n"
REPORT+="| **Toplam** | **\$0** 🟢 |\n"

if [ $ERRORS -gt 0 ]; then
  REPORT+="\n🔴 $ERRORS sorun tespit edildi\n"
fi
echo -e "$REPORT"
exit 0
