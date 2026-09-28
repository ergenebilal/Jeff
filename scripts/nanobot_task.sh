#!/usr/bin/env bash
# execute_nanobot_task — Hermes → Nanobot (HKUDS) wrapper
# Kullanım: nanobot_task.sh "PROMPT" [session-id] [timeout-sec]
# Çıktı: Nanobot cevabı stdout, exit code korunur
set -euo pipefail
PROMPT="${1:?prompt required}"
SESSION="${2:-swarm-$(date +%s)-$$}"
TIMEOUT="${3:-60}"
exec timeout "$TIMEOUT" nanobot agent --message "$PROMPT" --session "$SESSION"
