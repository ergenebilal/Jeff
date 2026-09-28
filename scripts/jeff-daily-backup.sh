#!/usr/bin/env bash
# Jeff Daily Auto Backup v1 — her gün 05:00'te çalışır
# Otomatik yedek + GitHub push
set -e

BACKUP_DIR="/home/hermes/backups"
TIMESTAMP=$(date +%Y-%m-%d)
BACKUP_FILE="$BACKUP_DIR/jeff-backup-$TIMESTAMP.zip"

mkdir -p "$BACKUP_DIR"

# 1. Hermes backup
cd /home/hermes/.hermes
# Use faster method: tar with exclude instead of hermes backup
tar czf "$BACKUP_FILE" \
    --exclude="secrets/*" \
    --exclude="*.bak*" \
    --exclude="node_modules" \
    --exclude="__pycache__" \
    --exclude="profiles/*/home" \
    --exclude="profiles/*/checkpoints" \
    --exclude="lsp/node_modules" \
    skills/ scripts/ cron/ config.yaml 2>/dev/null && echo "tar backup OK ($(du -h "$BACKUP_FILE" | cut -f1))" || {
    # fallback: hermes backup
    hermes backup --output "$BACKUP_FILE" 2>/dev/null
}

# 2. Push to GitHub
cd /home/hermes/jeff-backups 2>/dev/null || mkdir -p /home/hermes/jeff-backups && cd /home/hermes/jeff-backups
cp "$BACKUP_DIR/jeff-backup-$TIMESTAMP.zip" ./backup-latest.zip 2>/dev/null
echo "$(date -Iseconds) — auto backup" >> auto-backup-log.txt

# GitHub push only if there's a remote
if git remote -v 2>/dev/null | grep -q origin; then
    git add . && git commit -m "auto backup $TIMESTAMP" --allow-empty 2>/dev/null
    git push origin main 2>/dev/null && echo "GitHub push OK"
else
    echo "No GitHub remote configured — backup saved locally"
fi

# 3. Cleanup: keep last 7 days
find "$BACKUP_DIR" -name "jeff-backup-*" -mtime +7 -delete 2>/dev/null
find "$BACKUP_DIR" -name "jeff-hermes-*" -mtime +7 -delete 2>/dev/null

echo "✅ Backup complete: $TIMESTAMP"
