#!/bin/bash
# Sabah revenue task generator - Block 4
set -e
cd /opt/hermes
python3 -c "
import json, sys
try:
    from brain.revenue_ops import build_revenue_snapshot, rank_revenue_actions
    from brain.task_contract import validate_task_contract

    snap = build_revenue_snapshot()
    result = rank_revenue_actions(snap, gate_enabled=True)

    if result.get('actions'):
        top = result['actions'][0]
        task = {
            'id': f\"revenue-{top.get('name', 'unknown')}\",
            'goal': top.get('description', 'Revenue task'),
            'risk_level': 'medium',
            'approval': 'required',
            'verify': 'check_execution',
            'max_retries': 1,
            'failure_mode': 'log_and_notify',
            'rollback': 'notify_user'
        }
        result['task_contract'] = validate_task_contract(task)

    print(json.dumps(result, indent=2, default=str))
except Exception as e:
    print(json.dumps({'status': 'error', 'error': str(e)}))
"
