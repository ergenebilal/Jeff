#!/usr/bin/env bash
set -uo pipefail
LOG="/home/hermes/.hermes/logs/gateway_child_sentinel.log"
TS="$(date -Iseconds)"
if ! systemctl is-active --quiet hermes-gateway.service; then
  echo "$TS gateway_inactive_skip" >> "$LOG"
  exit 0
fi
before=$(systemctl --no-pager -l status hermes-gateway.service 2>/dev/null | grep -E "chatterbox|pyright-langserver|python3 -m http.server 8891|/opt/hermes/hq.*server.py 8889" | wc -l | tr -d " ")
/usr/local/sbin/hermes-gateway-cgroup-cleanup.sh >/dev/null 2>&1 || true
after=$(systemctl --no-pager -l status hermes-gateway.service 2>/dev/null | grep -E "chatterbox|pyright-langserver|python3 -m http.server 8891|/opt/hermes/hq.*server.py 8889" | wc -l | tr -d " ")
if [ "${before:-0}" != "0" ] || [ "${after:-0}" != "0" ]; then
  echo "$TS bad_children_before=$before after=$after" >> "$LOG"
fi
exit 0
