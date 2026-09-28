#!/bin/bash
# RAM Baseline Collector — 24 saat boyunca saatlik ölçüm
LOG="/home/hermes/jeff2/reports/optimization/ram-baseline.log"
mkdir -p "$(dirname "$LOG")"
TIMESTAMP=$(date -Iseconds)
RAM_USED=$(free -m | awk '/Mem:/{print $3}')
RAM_AVAIL=$(free -m | awk '/Mem:/{print $7}')
SWAP_USED=$(free -m | awk '/Swap:/{print $3}')
LOAD=$(uptime | awk -F'load average:' '{print $2}')
DOCKER_TOTAL=$(docker stats --no-stream --format "{{.MemUsage}}" 2>/dev/null | awk -F'/' '{sum += $1} END {print sum}')
PROCS=$(ps aux | wc -l)
echo "$TIMESTAMP | RAM_USED=${RAM_USED}MB | RAM_AVAIL=${RAM_AVAIL}MB | SWAP=${SWAP_USED}MB | LOAD=$LOAD | DOCKER=${DOCKER_TOTAL}MB | PROCS=$PROCS" >> "$LOG"
