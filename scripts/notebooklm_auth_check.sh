#!/bin/bash
# NotebookLM auth health check — weekly
AUTH_FILE="/home/hermes/.notebooklm-mcp-cli/auth.json"
BACKUP="/home/hermes/.hermes/notebooklm-auth-backup.json"

# Auth dosyası var mı?
if [ ! -f "$AUTH_FILE" ]; then
    echo "❌ Auth file missing"
    # Yedek varsa kurtar
    if [ -f "$BACKUP" ]; then
        cp "$BACKUP" "$AUTH_FILE"
        chmod 600 "$AUTH_FILE"
        echo "✅ Restored from backup"
    fi
    exit 1
fi

# 90 günden eskiyse uyar
AGE=$(stat -c %Y "$AUTH_FILE")
NOW=$(date +%s)
DAYS_OLD=$(( (NOW - AGE) / 86400 ))
echo "Auth file age: $DAYS_OLD days"
if [ $DAYS_OLD -gt 60 ]; then
    echo "⚠️ Auth file is $DAYS_OLD days old — may need refresh soon"
fi
echo "✅ Auth health check passed"
