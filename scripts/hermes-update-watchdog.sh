#!/bin/bash
# Hermes güncelleme dedektörü — sadece algılama yapar, kararı agent'a bırakır
# Çıktı: güncelleme varsa changelog + metadata, yoksa boş

STATE_FILE="/home/hermes/.hermes/data/hermes-latest-version.txt"
REPO="NousResearch/hermes-agent"
INSTALL_DIR="/opt/hermes"

# Mevcut commit
CURRENT_COMMIT=""
if [ -d "$INSTALL_DIR" ]; then
    CURRENT_COMMIT=$(cd "$INSTALL_DIR" && git rev-parse --short HEAD 2>/dev/null)
fi
CURRENT_VERSION=$(cd "$INSTALL_DIR" && git describe --tags 2>/dev/null || echo "unknown")

# GitHub API'den güncel durum
LATEST=$(curl -sf "https://api.github.com/repos/$REPO/releases/latest" 2>/dev/null | python3 -c "
import json,sys
try:
    d=json.load(sys.stdin)
    tag=d.get('tag_name','') or d.get('name','')
    body=d.get('body','')[:2000]
    print(f'{tag}|{body}')
except: print('|')
" 2>/dev/null)

LATEST_TAG="${LATEST%%|*}"
LATEST_BODY="${LATEST#*|}"
LATEST_COMMIT=$(curl -sf "https://api.github.com/repos/$REPO/commits/main" 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('sha','')[:12])" 2>/dev/null)
LATEST_DATE=$(curl -sf "https://api.github.com/repos/$REPO/commits/main" 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('commit',{}).get('author',{}).get('date','')[:10])" 2>/dev/null)

# Önceki durum
PREVIOUS=""
[ -f "$STATE_FILE" ] && PREVIOUS=$(cat "$STATE_FILE")
CURRENT="${LATEST_TAG}|${LATEST_COMMIT}|${LATEST_DATE}"

# İlk çalıştırmaysa kaydet, çık
[ -z "$PREVIOUS" ] && { echo "$CURRENT" > "$STATE_FILE"; exit 0; }

# Değişiklik yoksa sessiz
[ "$CURRENT" == "$PREVIOUS" ] && exit 0

# Güncelleme var — durumu kaydet
echo "$CURRENT" > "$STATE_FILE"

# Context olarak agent'a gidecek çıktı:
echo "HERMES_UPDATE_DETECTED=1"
echo "CURRENT_VERSION=$CURRENT_VERSION"
echo "CURRENT_COMMIT=$CURRENT_COMMIT"
echo "LATEST_VERSION=$LATEST_TAG"
echo "LATEST_COMMIT=$LATEST_COMMIT"
echo "LATEST_DATE=$LATEST_DATE"
echo "CHANGELOG_START"
echo "$LATEST_BODY"
echo "CHANGELOG_END"
