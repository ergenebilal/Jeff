#!/bin/bash
# n8n DB erisim wrapper — host volume permission denied icin docker exec/cp uzerinden
# Kullanim: n8n-db.sh "SELECT count(*) FROM workflow_entity;"
set -e
if [ -z "$1" ]; then echo "Usage: n8n-db.sh <SQL>"; exit 1; fi
SQL="$1"
TMP=$(mktemp /tmp/n8n-db-XXXX.sqlite)
docker cp n8n:/home/node/.n8n/database.sqlite "$TMP" 2>/dev/null
if [ ! -f "$TMP" ]; then echo "docker cp basarisiz"; exit 1; fi
sqlite3 "$TMP" "$SQL"
rm -f "$TMP"
