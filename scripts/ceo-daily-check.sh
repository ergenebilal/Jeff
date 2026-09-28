#!/usr/bin/env bash
# CEO Günlük Stratejik Check — no-agent cron
set -uo pipefail

HOME=/home/hermes
GOAL_MANAGER="$HOME/jeff2/goal_engine/goal_manager.py"
GOAL_METRICS="$HOME/jeff2/goal_engine/goal_metrics.py"

echo "🏛️ **CEO Günlük Rapor** — $(date '+%Y-%m-%d %H:%M')"
echo ""
echo "---"
echo ""

if [ -f "$GOAL_MANAGER" ]; then
  python3 "$GOAL_MANAGER"
else
  echo "⚠️ goal_manager.py bulunamadı"
fi

echo ""
echo "---"
echo ""

if [ -f "$GOAL_METRICS" ]; then
  python3 "$GOAL_METRICS"
else
  echo "⚠️ goal_metrics.py bulunamadı"
fi

echo ""
echo "---"
echo "**Not:** CEO katmanı aktif — tüm worker'lar bağımsız çalışıyor."
