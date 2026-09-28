#!/bin/bash
export PATH="/home/hermes/.hermes/node/bin:$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"

cd /opt/hermes/trend-watcher

# GitHub elmas taramasi + Hermes Agent repo kontrolu
cat github-prompt.txt | opencode run --agent operator . 2>/dev/null

# Basarili mi kontrol et
if [ -f github-gems.md ] && [ -s github-gems.md ]; then
    LINES=$(wc -l < github-gems.md)
    echo "[OK] GitHub gems guncellendi: $(date) — $LINES satir"
else
    echo "[FAIL] github-gems.md olusturulamadi: $(date)"
fi
