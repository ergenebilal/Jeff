#!/bin/bash
# Saatlik KPI snapshot - Block 3
set -e
cd /opt/hermes
python3 -c "
import json, sys
from pathlib import Path
log_path = Path.home() / '.hermes' / 'logs' / 'closed_loop.jsonl'
if not log_path.exists():
    print(json.dumps({'status': 'no_data', 'file': str(log_path)}))
    sys.exit(0)
try:
    from brain.kpi_scorecard import build_kpi_scorecard
    result = build_kpi_scorecard([log_path])
    print(json.dumps(result, indent=2, default=str))
except Exception as e:
    print(json.dumps({'status': 'error', 'error': str(e)}))
"
