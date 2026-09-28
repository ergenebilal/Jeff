#!/usr/bin/env bash
set -euo pipefail

# Jeff Crash Watchdog — checks if Hermes is responsive, restarts if dead
# Runs every 5 minutes via cron

HEALTH_LOG="/home/hermes/.hermes/logs/crash_watchdog.log"
HERMES_HOME="/home/hermes/.hermes"
DATE_CMD="date +'%Y-%m-%d %H:%M:%S'"

mkdir -p "$(dirname "$HEALTH_LOG")"

# Check 1: Is the Hermes process alive?
HERMES_PID=$(pgrep -f "hermes" 2>/dev/null | head -1 || echo "")

if [ -z "$HERMES_PID" ]; then
    echo "$($DATE_CMD) 🔴 CRITICAL: Hermes process not found. Restarting..." >> "$HEALTH_LOG"
    # Try restart via systemd or direct
    if systemctl is-active --quiet hermes 2>/dev/null; then
        systemctl restart hermes 2>/dev/null && echo "$($DATE_CMD) ✅ Restarted via systemd" >> "$HEALTH_LOG"
    elif command -v hermes &>/dev/null; then
        hermes start --daemon 2>/dev/null && echo "$($DATE_CMD) ✅ Restarted via hermes start" >> "$HEALTH_LOG"
    fi
    exit 0
fi

# Check 2: Is Hermes responding to API calls?
if command -v curl &>/dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 http://localhost:8765/health 2>/dev/null || echo "000")
    if [ "$HTTP_CODE" = "000" ]; then
        echo "$($DATE_CMD) 🟡 WARNING: Hermes PID alive but health endpoint not responding ($HTTP_CODE)" >> "$HEALTH_LOG"
    fi
fi

# Check 3: Token budget tweet
TOKEN_LOG="/home/hermes/.hermes/logs/crash_watchdog.token"
BUDGET=$(python3 -c "import sys; sys.path.insert(0,'/home/hermes/.hermes'); from brain.accounting import get_budget_left; print(get_budget_left() or 0)" 2>/dev/null || echo "unknown")
echo "$($DATE_CMD) 🟢 OK | PID: $HERMES_PID | Budget: \$$BUDGET" >> "$HEALTH_LOG"
