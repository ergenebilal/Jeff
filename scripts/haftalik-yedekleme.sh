#!/bin/bash
# Haftalık yedekleme — Cumartesi 03:00
export HOME=/home/hermes
BACKUP_DIR="$HOME/backups/$(date +%Y-%m-%d)"
mkdir -p "$BACKUP_DIR"

# n8n container'ı bul (eski/yeni container'ları da dene)
CONTAINER=$(docker ps --filter "ancestor=n8nio/n8n:2.22.2" --format "{{.ID}}" | head -1)
[ -z "$CONTAINER" ] && CONTAINER=$(docker ps --filter "name=n8n" --format "{{.ID}}" | head -1)
[ -z "$CONTAINER" ] && CONTAINER=$(docker ps -q | head -1)

if [ -n "$CONTAINER" ]; then
  docker cp "$CONTAINER:/home/node/.n8n/database.sqlite" "$BACKUP_DIR/n8n_db.sqlite" 2>&1 || \
  docker cp "$CONTAINER:/home/node/.n8n/n8n.db" "$BACKUP_DIR/n8n.db" 2>&1
fi

cp "$HOME/.hermes/config.yaml" "$BACKUP_DIR/hermes_config.yaml" 2>&1
cp -r "$HOME/.config/opencode" "$BACKUP_DIR/opencode_config" 2>&1
crontab -l > "$BACKUP_DIR/crontab.txt" 2>&1

# 30 günden eski yedekleri temizle
find "$HOME/backups/" -maxdepth 1 -type d -mtime +30 -exec rm -rf {} \; 2>/dev/null