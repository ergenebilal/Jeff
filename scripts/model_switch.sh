#!/bin/bash
# Compatibility entry point for the selected Jeff routes.
set -euo pipefail
exec bash /home/hermes/scripts/switch-model.sh "${1:-primary}"
