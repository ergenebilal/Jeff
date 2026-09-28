#!/bin/bash
# Haftalık Hermes Session Prune + Optimize
# 30 günden eski sessionları sil, VACUUM yap
# Çıktı: silinen sayısı + kazanç

ONCE=$(du -h ~/.hermes/state.db | cut -f1)

PRUNE_OUT=$(hermes sessions prune --older-than 30 --yes 2>&1)
SILINEN=$(echo "$PRUNE_OUT" | grep -oP 'Pruned \K[0-9]+')
[ -z "$SILINEN" ] && SILINEN=0

OPT_OUT=$(hermes sessions optimize 2>&1)
KAZANC=$(echo "$OPT_OUT" | grep -oP 'reclaimed \K[0-9.]+ MB')
[ -z "$KAZANC" ] && KAZANC="0"

SONRA=$(du -h ~/.hermes/state.db | cut -f1)
SESSION=$(sqlite3 ~/.hermes/state.db "SELECT COUNT(*) FROM sessions;" 2>/dev/null || echo "?")

echo "🧹 Haftalik Session Prune"
echo "Once: $ONCE | Sonra: $SONRA | Session: $SESSION"
echo "Silinen: $SILINEN | Kazanc: ${KAZANC}MB"
