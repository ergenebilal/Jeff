#!/bin/bash
export PATH="/home/hermes/.hermes/node/bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"

cd /opt/hermes/trend-watcher

# OpenCode ile trend taraması
cat trend_prompt.txt | opencode run --agent operator . 2>/dev/null

# Başarılı mı kontrol et
if [ -f trend-report.md ] && [ -s trend-report.md ]; then
    LINES=$(wc -l < trend-report.md)
    echo "[OK] Trend report guncellendi: $(date) — $LINES satir"
else
    echo "[FAIL] trend-report.md olusturulamadi: $(date)"
fi
