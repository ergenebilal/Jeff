#!/bin/bash
LOG="$HERMES_HOME/logs/api_health.log"
ENV_FILE="$HERMES_HOME/.env"

GROQ_KEY=$(awk -F'=' '/^GROQ_API_KEY/{print $2}' "$ENV_FILE")
if [ -z "$GROQ_KEY" ]; then
    echo "[$(date)] ALERT: GROQ_API_KEY not found" >> "$LOG"
    echo "ALERT: GROQ_API_KEY bulunamadi!"
    exit 1
fi

HTTP_CODE=$(curl -s -o /dev/null -w '%{http_code}'     -H "Authorization: Bearer ***     'https://api.groq.com/openai/v1/models' 2>/dev/null)

if [ "$HTTP_CODE" = "200" ]; then
    echo "[$(date)] OK: Groq API valid (HTTP $HTTP_CODE)" >> "$LOG"
    echo "OK: Groq API anahtari gecerli"
    exit 0
elif [ "$HTTP_CODE" = "401" ]; then
    echo "[$(date)] ALERT: Groq API INVALID (HTTP 401)" >> "$LOG"
    echo "ALERT: Groq API Anahtari GECERSIZ! Hemen yenile!"
    exit 1
else
    echo "[$(date)] WARN: HTTP $HTTP_CODE" >> "$LOG"
    echo "WARN: Beklenmeyen HTTP $HTTP_CODE"
    exit 2
fi
