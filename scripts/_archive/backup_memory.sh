#!/bin/bash
# ErgeneAI Bellek Yedekleme (gzip ile sıkıştırılmış)
set -e
BACKUP_DIR="/home/hermes/backups"
cd "$BACKUP_DIR"

# state.db'yi gzip ile sıkıştır, direkt kaynağı sıkıştırma
cp /home/hermes/.hermes/state.db "./state_$(date +%Y%m%d_%H%M).db"
gzip -f "./state_$(date +%Y%m%d_%H%M).db"

cp /home/hermes/.hermes/config.yaml ./config.yaml 2>/dev/null || true

git add .
git commit -m "backup $(date '+%Y-%m-%d %H:%M')" || true
git push origin main 2>&1

# 7 günden eski snapshot'ları temizle
find . -name "state_*.db.gz" -mtime +7 -delete 2>/dev/null || true
find . -name "state_*.db" -mtime +7 -delete 2>/dev/null || true

ORIG_SIZE=$(ls -lh /home/hermes/.hermes/state.db | awk '{print $5}')
GZ_SIZE=$(ls -lh ./state_$(date +%Y%m%d_%H%M).db.gz 2>/dev/null | awk '{print $5}')
echo "$(date '+%H:%M:%S') ✅ Yedeklendi (orijinal: ${ORIG_SIZE} → sıkıştırılmış: ${GZ_SIZE})"
