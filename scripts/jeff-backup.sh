#!/usr/bin/env bash
# Jeff nightly backup. Started by cron at 03:00 (hermes user).
# Consistent copies of every SQLite database, plus the code, configs and units that
# cannot be rebuilt from git. Keeps the last 14 days. Backups may contain secrets,
# so the directory is private (700) and every archive is 600.
set -u
umask 077
DEST=/home/hermes/backups
STAMP=$(date +%Y%m%d-%H%M%S)
WORK=$(mktemp -d "$DEST/.work.XXXXXX" 2>/dev/null) || { mkdir -p "$DEST" && chmod 700 "$DEST" && WORK=$(mktemp -d "$DEST/.work.XXXXXX"); }
ARCHIVE="$DEST/jeff-backup-$STAMP.tar.gz"
LOG=/home/hermes/logs/backup.log
mkdir -p /home/hermes/logs
log() { echo "[$(date '+%F %T')] $*" >> "$LOG"; }
trap 'rm -rf "$WORK"' EXIT

log "backup started"
mkdir -p "$WORK/db" "$WORK/etc"

# 1) SQLite databases: use the online-backup API so a copy is consistent even while in use.
n=0
for db in \
  /home/hermes/cybergene-chat/data/support_chat.db \
  /home/hermes/jeff_repo/jeff2/bridge/bridge.db \
  /home/hermes/.n8n/database.sqlite \
  /opt/hermes/scripts/data/support_chat.db \
  /opt/hermes/jeff_v2/_archive_faz0_20260806/memory_data/jeff_memory_core.sqlite ; do
  [ -f "$db" ] || { log "skip (missing): $db"; continue; }
  out="$WORK/db/$(echo "$db" | sed 's#^/##; s#/#__#g')"
  if sqlite3 "$db" ".backup '$out'" 2>>"$LOG"; then n=$((n+1)); else log "ERROR: could not back up $db"; fi
done
log "databases backed up: $n"

# 2) Configs and units that would be painful to recreate.
cp /etc/nginx/sites-available/cybergene.co "$WORK/etc/" 2>/dev/null
for f in /etc/systemd/system/cybergene-chat.service /etc/systemd/system/jeff-bridge.service /etc/systemd/system/jeff-approval-bot.service /etc/jeff-bridge.env; do
  cp "$f" "$WORK/etc/" 2>/dev/null || log "skip (unreadable): $f"
done
crontab -l > "$WORK/etc/crontab-hermes.txt" 2>/dev/null

# 3) Code and data that live only on this server.
tar -czf "$ARCHIVE.tmp" \
  --exclude='__pycache__' --exclude='*.pyc' --exclude='node_modules' --exclude='venv' --exclude='.venv' \
  -C "$WORK" db etc \
  -C / home/hermes/cybergene-chat opt/hermes home/hermes/pipeline home/hermes/scripts 2>>"$LOG"
rc=$?
if [ $rc -le 1 ] && tar -tzf "$ARCHIVE.tmp" >/dev/null 2>&1; then
  mv "$ARCHIVE.tmp" "$ARCHIVE"; chmod 600 "$ARCHIVE"
  log "OK archive=$ARCHIVE size=$(du -h "$ARCHIVE" | cut -f1)"
else
  rm -f "$ARCHIVE.tmp"; log "ERROR: archive failed or unreadable (tar rc=$rc)"; exit 1
fi

# 4) Retention: keep the 14 newest archives.
ls -1t "$DEST"/jeff-backup-*.tar.gz 2>/dev/null | tail -n +15 | xargs -r rm -f
log "backup finished; archives kept: $(ls -1 "$DEST"/jeff-backup-*.tar.gz | wc -l)"
