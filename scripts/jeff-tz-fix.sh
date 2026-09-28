#!/usr/bin/env bash
# Jeff Timezone Fix v1.0
# Forces Hermes to read Turkey local time at every context start.
# Output: HERMES_LOCAL_TIME=<epoch> HERMES_TZ=Europe/Istanbul HERMES_DATE_IST=<human>

export HERMES_LOCAL_TIME=$(date +%s)
export HERMES_TZ="Europe/Istanbul"
export HERMES_DATE_IST=$(TZ='Europe/Istanbul' date '+%Y-%m-%d %H:%M:%S %Z')
echo "[CLOCK] Timezone synced: $HERMES_DATE_IST (epoch: $HERMES_LOCAL_TIME)"
