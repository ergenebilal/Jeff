#!/usr/bin/env bash
set -euo pipefail

SCRIPT_LIST=(
  /opt/hermes/trend-watcher/approval-queue-builder.py
  /opt/hermes/trend-watcher/learning-updater.py
  /opt/hermes/trend-watcher/jeff-weekly-summary.sh
  /home/hermes/.hermes/scripts/telegram-digest.sh
  /home/hermes/.hermes/scripts/approval-command-handler.py
  /home/hermes/.hermes/scripts/followup-reminder.sh
  /opt/hermes/trend-watcher/monthly-review.sh
)

CURRENT_DATETIME=$(date '+%Y-%m-%d %H:%M')
PASS=0
FAIL=0
RESULTS=()

run_test() {
  local script="$1" name
  name=$(basename "$script")

  if [ ! -r "$script" ]; then
    RESULTS+=("| $name | FAIL | N/A | File not found or not readable |")
    echo "FAIL: $name (file not found)"
    FAIL=$((FAIL + 1))
    return
  fi

  local output rc
  if [ "$name" = "approval-command-handler.py" ]; then
    local queue_id
    queue_id=$(awk -F': ' '/^[[:space:]]*- id:/ {print $2; exit}' /opt/hermes/trend-watcher/approval-queue.md)
    if [ -z "${queue_id:-}" ]; then
      RESULTS+=("| $name | FAIL | N/A | Could not locate approval-queue item id |")
      echo "FAIL: $name (no queue id found)"
      FAIL=$((FAIL + 1))
      return
    fi
    output=$(env -i HOME=/home/hermes PATH=/usr/local/bin:/usr/bin:/bin /bin/sh -c "$script --dry-run approve $queue_id" </dev/null 2>&1) && rc=0 || rc=$?
  else
    output=$(env -i HOME=/home/hermes PATH=/usr/local/bin:/usr/bin:/bin /bin/sh -c "$script" </dev/null 2>&1) && rc=0 || rc=$?
  fi

  if [ "$rc" -eq 0 ]; then
    RESULTS+=("| $name | PASS | 0 | - |")
    echo "PASS: $name"
    PASS=$((PASS + 1))
  else
    local snippet
    snippet=$(echo "$output" | head -c 200 | tr '\n\r' ' ' | sed 's/|/\\|/g')
    RESULTS+=("| $name | FAIL | $rc | ${snippet:-no output} |")
    echo "FAIL: $name (exit code: $rc)"
    [ -n "$output" ] && echo "  Output: $(echo "$output" | head -c 200)"
    FAIL=$((FAIL + 1))
  fi
}

print_report() {
  local total=$((PASS + FAIL))
  echo ""
  echo "## Cron Dry-Run Report -- $CURRENT_DATETIME"
  echo "| Script | Status | Exit Code | Output |"
  echo "|--------|--------|-----------|--------|"
  for row in "${RESULTS[@]}"; do echo "$row"; done
  echo "---"
  echo "PASS: $PASS/$total | FAIL: $FAIL/$total"
}

if [ "${1:-}" = "--all" ]; then
  for s in "${SCRIPT_LIST[@]}"; do run_test "$s"; done
  print_report
elif [ -n "${1:-}" ]; then
  run_test "$1"
else
  echo "Usage: bash $0 <script-path>"
  echo "       bash $0 --all"
  exit 1
fi
