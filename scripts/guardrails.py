#!/usr/bin/env python3
"""Jeff Guardrails System — Formal execution guard layer.

Automatically wraps tool calls with:
- TokenGuard: budget threshold check (warning at $0.50, stop at $0.10)
- LoopGuard: same-tool-loop detection (2 failures → stop, analyze)
- DecisionGuard: high-impact operations → require assessment
"""

import sys, os, json, time
from pathlib import Path

sys.path.insert(0, os.path.expanduser('~/.hermes'))
STATE_FILE = Path.home() / '.hermes' / 'guardrails_state.json'

class Guardrails:
    def __init__(self):
        self.state = self._load_state()
    
    def _load_state(self):
        if STATE_FILE.exists():
            try: return json.loads(STATE_FILE.read_text())
            except: pass
        return {'tool_history': [], 'sessions': [], 'warnings': []}
    
    def _save(self):
        STATE_FILE.write_text(json.dumps(self.state, indent=2))
    
    def check_token(self):
        """Check budget and return status."""
        try:
            from brain.accounting import get_budget_left
            budget = get_budget_left()
            if budget is None: return 'unknown', 0
            if budget < 0.10: 
                self._log_warning(f'CRITICAL: Budget ${budget:.2f} — stop high-cost ops')
                return 'critical', budget
            if budget < 0.50:
                self._log_warning(f'WARNING: Budget ${budget:.2f} — approaching limit')
                return 'warning', budget
            return 'ok', budget
        except:
            return 'unknown', 0
    
    def check_tool_loop(self, tool_name, success):
        """Track tool success/failure, detect loops."""
        history = self.state['tool_history']
        history.append({'tool': tool_name, 'success': success, 'time': time.time()})
        # Keep last 20
        if len(history) > 20:
            self.state['tool_history'] = history[-20:]
        
        # Check: same tool failed 2+ times in last 5 calls
        recent = [h for h in self.state['tool_history'][-5:] if h['tool'] == tool_name]
        failures = sum(1 for h in recent if not h['success'])
        if failures >= 2 and not success:
            self._log_warning(f'TOOL LOOP: {tool_name} failed {failures}/5 — stop and diagnose')
            self._save()
            return 'loop_detected'
        
        self._save()
        return 'ok'
    
    def check_decision(self, action_type, value):
        """Check if a decision needs escalation."""
        high_risk = ['payment', 'delete', 'mass_email', 'system_change', 'config_override']
        if action_type in high_risk and value > 0:
            return 'needs_review'
        return 'ok'
    
    def _log_warning(self, msg):
        self.state['warnings'].append({'msg': msg, 'time': time.time()})
        self._save()
    
    def status_report(self):
        """Return current guardrails status."""
        budget_status, budget_val = self.check_token()
        warnings = self.state['warnings'][-5:] if self.state['warnings'] else []
        return {
            'status': budget_status,
            'budget': budget_val,
            'active_warnings': len(warnings),
            'recent_warnings': [w['msg'] for w in warnings]
        }

if __name__ == '__main__':
    g = Guardrails()
    print(json.dumps(g.status_report(), indent=2))
