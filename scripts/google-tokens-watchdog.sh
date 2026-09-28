#!/bin/bash
# Google Workspace tokens watchdog + backup
# 1. tokens.json'ı güvenli bir kopyaya yedekler
# 2. Kaybolursa/bozulursa kopyadan restore eder

TOKEN_DIR="$HOME/.google-workspace-mcp"
TOKEN_FILE="$TOKEN_DIR/tokens.json"
BACKUP_DIR="/opt/hermes/google-workspace-backup"
BACKUP_FILE="$BACKUP_DIR/tokens.json"

mkdir -p "$BACKUP_DIR"

# Restore mode: if tokens.json is missing or broken, restore from backup
restore_if_needed() {
    local needs_restore=false

    if [ ! -f "$TOKEN_FILE" ]; then
        echo "⛔ tokens.json kayıp! Restore ediliyor..."
        needs_restore=true
    elif ! python3 -c "import json; d=json.load(open('$TOKEN_FILE')); exit(0 if d.get('refresh_token') else 1)" 2>/dev/null; then
        echo "⛔ tokens.json bozuk/eksik! Restore ediliyor..."
        needs_restore=true
    fi

    if [ "$needs_restore" = true ]; then
        if [ -f "$BACKUP_FILE" ]; then
            cp "$BACKUP_FILE" "$TOKEN_FILE"
            chmod 600 "$TOKEN_FILE"
            echo "✅ tokens.json restore edildi: $BACKUP_FILE → $TOKEN_FILE"
            # MCP'yi yeniden başlat (PID var mı kontrol et)
            MCP_PID=$(pgrep -f "google-workplace-mcp" 2>/dev/null | head -1)
            if [ -n "$MCP_PID" ]; then
                echo "🔄 MCP yeniden başlatılıyor (PID: $MCP_PID)..."
                kill "$MCP_PID" 2>/dev/null
            fi
            return 0
        else
            echo "❌ Yedek dosya da kayıp! Manual OAuth gerek."
            return 1
        fi
    fi
    return 0
}

# Backup mode: copy tokens.json to backup location
do_backup() {
    if [ -f "$TOKEN_FILE" ]; then
        cp "$TOKEN_FILE" "$BACKUP_FILE"
        chmod 600 "$BACKUP_FILE"
        echo "✅ tokens.json yedeklendi → $BACKUP_FILE"
    fi
}

case "${1:-check}" in
    restore)
        restore_if_needed
        ;;
    backup)
        do_backup
        ;;
    check)
        restore_if_needed
        do_backup
        ;;
    *)
        echo "Kullanım: $0 {check|backup|restore}"
        exit 1
        ;;
esac
