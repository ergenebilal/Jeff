#!/usr/bin/env bash
# n8n MCP watchdog — no gateway restart, just DB + live probe
set -euo pipefail
PID=$(pgrep -f "node /usr/local/bin/n8n" | head -n1 || true)
if [[ -z "$PID" ]]; then echo "ALERT n8n MCP: process not running"; exit 1; fi
DB="/proc/$PID/root/home/node/.n8n/database.sqlite"
if [[ ! -f "$DB" ]]; then echo "ALERT n8n MCP: DB not found PID $PID"; exit 1; fi
ENABLED=$(sqlite3 "$DB" "SELECT value FROM settings WHERE key='mcp.access.enabled';" 2>/dev/null || echo "")
if [[ "$ENABLED" != "true" ]]; then
  sqlite3 "$DB" "INSERT OR REPLACE INTO settings(key,value,loadOnStartup) VALUES('mcp.access.enabled','true',1);" 2>/dev/null || true
  echo "ALERT n8n MCP: MCP was disabled — re-enabled, will take effect after n8n restart. Triggering graceful reload via kill."
  kill "$PID" 2>/dev/null || true
  exit 1
fi
HERMES_TOKEN=$(python3 -c "import yaml; c=yaml.safe_load(open('/home/hermes/.hermes/config.yaml')); print(c['mcp_servers']['n8n']['headers']['Authorization'].replace('Bearer ','').strip())" 2>/dev/null || echo "")
if [[ -z "$HERMES_TOKEN" ]]; then echo "ALERT n8n MCP: hermes token empty"; exit 1; fi
if ! sqlite3 "$DB" "SELECT apiKey FROM user_api_keys WHERE audience='mcp-server-api';" 2>/dev/null | grep -qF "$HERMES_TOKEN"; then
  echo "ALERT n8n MCP: JWT drift detected"
  exit 1
fi
RESP=$(curl -sk -H "Authorization: Bearer $HERMES_TOKEN" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -X POST -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"watchdog","version":"1.0.0"}}}' http://127.0.0.1:5678/mcp-server/http 2>&1 | head -c 800 || true)
if echo "$RESP" | grep -q "protocolVersion"; then exit 0; fi
if echo "$RESP" | grep -q "MCP access is disabled"; then echo "ALERT n8n MCP: still disabled after DB fix"; exit 1; fi
echo "ALERT n8n MCP probe failed: ${RESP:0:300}"
exit 1
