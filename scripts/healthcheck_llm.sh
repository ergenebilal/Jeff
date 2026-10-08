#!/bin/bash
# Check the selected primary and standby; credentials remain in private env files.
set -euo pipefail
mkdir -p /home/hermes/logs
exec /home/hermes/.venv/bin/python /home/hermes/scripts/model_health.py \
    --env-file /home/hermes/.hermes/gateway.env \
    --env-file /home/hermes/.hermes/.env \
    --config /home/hermes/.hermes/config.yaml \
    --out /home/hermes/logs/model_health.json
