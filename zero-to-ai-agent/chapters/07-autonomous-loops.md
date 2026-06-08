# Chapter 7: Autonomous Loops — Set It and Forget It

## Concept

An **autonomous loop** is a self-sustaining system that:
1. Gathers data
2. Processes it with AI
3. Takes action
4. Reports results
5. Repeats on schedule

No human in the loop. Just you receiving the output.

## The Passive Income Loop

This is the loop I run daily. It takes ZERO active effort:

```
┌─────────────────────────────────────────────────────┐
│  06:00  Twitter scan → find "need automation" posts  │
│  07:00  Reddit scan → find business problems         │
│  08:00  AI ranking → score all opportunities         │
│  09:00  Lead enrichment → find contact info          │
│  10:00  Draft outreach → personalized email/Twitter DM│
│  11:00  Content → generate industry-specific posts   │
│  12:00  Report → Telegram summary of everything       │
└─────────────────────────────────────────────────────┘
```

## Implementation: The Autonomous Agent Loop

```bash
cat > ~/.hermes/scripts/autonomous_loop.py << 'PYEOF'
#!/usr/bin/env python3
"""
Autonomous agent loop runner.
Runs at 06:00 daily, orchestrates all passive income tasks.
"""

import json
import subprocess
from datetime import datetime

def run_agent(prompt):
    """Run Hermes with a prompt and return output"""
    result = subprocess.run(
        ["hermes", "run", prompt],
        capture_output=True, text=True, timeout=120
    )
    return result.stdout

def autonomous_loop():
    phase = 1
    results = {}
    
    # Phase 1: Collect
    print("[Phase 1/5] Scanning for opportunities...")
    scan = run_agent("Scan Twitter and Reddit for 'need automation' posts. Return raw data.")
    results["scan"] = scan
    
    # Phase 2: Rank
    print("[Phase 2/5] Ranking opportunities...")
    rank = run_agent(f"Rank these opportunities by buying signal: {scan[:2000]}")
    results["rank"] = rank
    
    # Phase 3: Enrich
    print("[Phase 3/5] Enriching lead data...")
    enrich = run_agent(f"Find contact info for top 3 opportunities: {rank[:1000]}")
    results["enrich"] = enrich
    
    # Phase 4: Report
    print("[Phase 4/5] Generating report...")
    report = run_agent(f"Create a Telegram-ready summary: {json.dumps(results)[:3000]}")
    results["report"] = report
    
    # Phase 5: Notify
    print("[Phase 5/5] Sending notification...")
    run_agent(f"Send this to Telegram: {report}")
    
    print(f"[Done] {datetime.now().isoformat()}")
    return results

if __name__ == "__main__":
    autonomous_loop()
PYEOF

chmod +x ~/.hermes/scripts/autonomous_loop.py
```

## Progressive Autonomy

Don't go full autonomous on day one. Scale progressively:

**Level 1: Manual (Week 1)**
→ You read all outputs, approve all actions

**Level 2: Semi-Autonomous (Week 2)**
→ Agent acts on clear patterns, alerts you on uncertainty

**Level 3: Full Autonomous (Week 3+)**
→ Agent runs entire loop, you get daily summary only

## The 99/1 Principle

I operate on the 99/1 rule:
- **99%**: Agent decides, explores, builds, tests — on its own
- **1%**: Only you approve payments, account changes, irreversible actions

This is the sweet spot. Maximum leverage with minimum risk.

## Safety Checks

Autonomous loops need safety rails:

```bash
cat > ~/.hermes/skills/safety-rail/SKILL.md << 'SKILLEOF'
---
name: safety-rail
version: 1.0
---

## Safety Rules (NON-NEGOTIABLE)

1. Never execute: rm -rf, > /dev/sda, ddl operations
2. Never spend money without approval
3. Never modify production databases
4. Never send messages without content validation
5. Every action must be logged
6. If uncertain, report to user and STOP

## Shutdown Conditions
- 3 consecutive errors → pause all loops → alert user
- Disk < 5% → emergency shutdown
- RAM > 90% → pause non-critical processes
SKILLEOF
```

## Verification

```bash
# Test the loop
python3 ~/.hermes/scripts/autonomous_loop.py

# Monitor progress
hermes cron list
```

## Pro Tip

Start with a 1-hour loop, not 24. Run it for 2 days, review output, refine. Then extend to 12 hours. Then daily. The fastest way to break an autonomous system is to deploy it without testing.

## Next Steps

Chapter 8 covers real production deployment — reverse proxies, SSL, database connections, and making all this survive server reboots.
