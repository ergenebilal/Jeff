#!/usr/bin/env python3
"""Jeff Monitoring Alarm — threshold-based system pulse."""

import sys, os, json
sys.path.insert(0, os.path.expanduser('~/.hermes'))

from brain.monitor import check_health
from brain.accounting import get_budget_left

try:
    from guardrails import Guardrails
    g = Guardrails()
    budget_status, budget = g.check_token()
    warnings = g.status_report()
except Exception:
    budget_status = "unknown"
    budget = 0
    warnings = {"active_warnings": 0, "guard_status": "unknown"}

# Health
try:
    health = check_health()
    health_ok = health.get("status") == "ok"
    mem = health.get("memory", {}).get("available_mb", "?")
except Exception:
    health_ok = False
    mem = "?"
    health = {}

# Budget
try:
    budget_actual = get_budget_left()
except Exception:
    budget_actual = budget

if budget_actual is not None:
    budget_val = budget_actual
else:
    budget_val = budget

# Output
status_icon = "OK" if health_ok and budget_status == "ok" else "!!"
budget_icon = "$" if budget_status == "ok" else "!"

print("Jeff System Pulse")
print("Budget: $" + str(budget_val) + " (" + budget_status + ")")
print("RAM: " + str(mem) + " MB free")
print("Guardrails: " + warnings.get("guard_status", "?") + " | " + str(warnings.get("active_warnings", 0)) + " active")

if budget_status in ("warning", "critical"):
    print("BUDGET WARNING: $" + str(budget_val) + " remaining")
