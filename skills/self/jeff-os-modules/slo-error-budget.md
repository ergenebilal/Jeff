# Jeff OS SLO + Error Budget System

> Based on Google SRE Error Budget Policy + GPT 5.6 Sol recommendations.
> Core principle: "Error budget tükendiğinde yeni özellik durur."

---

## 1. Service Level Objectives (SLOs)

### SLO Table

| SLO | Target | Error Budget | Window |
|-----|--------|-------------|--------|
| Lead capture success | ≥99% | 1% allowance | Monthly |
| Daily briefing on time | ≥95% | 5% allowance (≤1.5 missed/month) | Monthly |
| Task success rate (P0/P1) | ≥90% | 10% allowance | Monthly |
| GATE compliance | ≥95% | 5% allowance | Monthly |
| MTTR (mean time to recovery) | <60 min | 60 min ceiling | Rolling 7-day |
| Cost per successful task | Tracked + benchmarked | N/A (cost is a metric, not a budget gate) | Weekly |

### SLO Definitions

**Lead capture success** — Every lead touchpoint (Apify scraping, Google Places API, form submission) completes without error. Failure = lost lead, broken pipeline, or data corruption.

**Daily briefing on time** — The 08:00 daily digest cron fires and delivers a coherent briefing before 08:30 local time. Failure = cron missed, crash, or incomplete output.

**Task success rate (P0/P1)** — Tasks classified P0 (revenue, security, data loss risk) or P1 (customer-facing, time-sensitive) complete without requiring human recovery. Failure = task crashed, returned garbage, or required manual fixup.

**GATE compliance** — All deployed artifacts pass through the quality gate checklist (product-quality-gates skill). No section, skill, or module ships without passing GATE. Failure = shortcut taken, gate skipped, or post-deploy regression.

**MTTR** — From detection of an SLO violation or critical alarm to remediation. Measured as (resolution_time - detection_time). Detection = alert fired or human noticed; resolution = service restored + incident closed.

---

## 2. Error Budget Policy

### Budget Calculation

```
Error Budget = 100% - SLO Target

Example (Lead Capture @ 99%):
  Budget = 100% - 99% = 1% allowance
  In a month with 3000 lead events: 30 events can fail before budget exhausted
```

### Budget States

| State | Condition | Policy |
|-------|-----------|--------|
| **GREEN** | >50% budget remaining | Full feature velocity. New skills, MCP, sections allowed |
| **YELLOW** | 25-50% budget remaining | Caution. No new MCP servers. New skills need justification |
| **RED** | <25% budget remaining | Warning. Only bug fixes and reliability work |
| **EXHAUSTED** | 0% budget remaining | **FEATURE FREEZE.** No new sections, no new MCP, no new skills. Only reliability work |

### Feature Freeze Rules (Budget Exhausted)

When ANY SLO's error budget reaches 0%:

1. **STOP** — No new features, skills, MCP servers, or sections added to Jeff OS
2. **RELIABILITY ONLY** — Work is restricted to:
   - Fixing the SLO that caused the freeze
   - Reducing MTTR
   - Improving monitoring/alerting
   - Hardening existing skills and MCP connections
   - Reducing toil (manual steps that can be automated)
3. **FREEZE LIFTS** when the affected SLO shows ≥50% budget remaining after fixes
4. **FREEZE LOG** — Every freeze is logged with: start date, SLO breached, duration, root cause, fix applied, budget restored date

### Budget Reset

- **Monthly reset** on the 1st of each month at 00:00 UTC
- Previous month's budget is archived (not deleted)
- If 3 consecutive months show RED/EXHAUSTED for the same SLO, the SLO target must be formally reviewed and either:
  - Tightened (if root cause was one-time)
  - Relaxed (if the target was unrealistic given current infrastructure)
  - Documented as accepted risk (signed off by Bilal)

---

## 3. Monitoring Queries & Data Sources

### Per-SLO Measurement

#### Lead Capture Success (≥99%)

```
Metric:  (successful_captures / total_captures) × 100
Window:  Monthly (1st to last day)
Data:    Apify run logs, Google Places API responses, scraping skill logs
Query:   grep -c "lead.*captured" logs/leads-*.log / grep -c "lead.*failed" logs/leads-*.log
Source:  Apify actor runs (successful vs error), Playwright scraping outcomes
Alert:   Warning when monthly success < 99.5%, Critical < 99.0%
```

#### Daily Briefing On Time (≥95%)

```
Metric:  briefings_delivered_by_0830 / briefings_expected
Window:  Monthly
Data:    Cron job logs, ntfy delivery confirmations
Query:   Check cron log for digest job completion time; flag if > 08:30
Source:  /home/hermes/.hermes/cron/ logs, daily_digest() tool output
Alert:   Warning if 1+ missed in month, Critical if 2+ missed (5% = 1.5 days)
```

#### Task Success Rate P0/P1 (≥90%)

```
Metric:  (p0_tasks_success + p1_tasks_success) / (p0_tasks_total + p1_tasks_total) × 100
Window:  Monthly
Data:    Task outcome logs, delegate_with_model results, skill execution logs
Query:   Parse task outcomes from session logs; classify by priority
Source:  Hermes session DB, agentmemory action statuses, bridge task results
Alert:   Warning at < 92%, Critical at < 90%
```

#### GATE Compliance (≥95%)

```
Metric:  (artifacts_passing_gate / artifacts_deployed) × 100
Window:  Monthly
Data:    GATE check results (product-quality-gates skill execution log)
Query:   Count gate_pass vs gate_fail entries in skill execution history
Source:  skill_view(product-quality-gates) execution logs, post-deploy checks
Alert:   Warning at < 97%, Critical at < 95%
```

#### MTTR (<60 min)

```
Metric:  Σ(resolution_time - detection_time) / incident_count
Window:  Rolling 7-day
Data:    Incident logs, alarm timestamps, fix timestamps
Query:   For each incident: MTTR = timestamp_of_fix - timestamp_of_alert
Source:  ntfy alerts (detection), session logs (resolution), cron error logs
Alert:   Warning if 7-day MTTR > 45 min, Critical if > 60 min
```

#### Cost Per Successful Task

```
Metric:  total_monthly_cost / total_successful_tasks
Window:  Weekly (for trend), Monthly (for benchmark)
Data:    Langfuse cost analytics, cost_check() tool
Query:   cost_analytics(period="week") aggregated / task_success_count
Source:  Langfuse (per-model cost breakdown), cost_check() snapshots
Alert:   Warning if > 2× baseline, Critical if > 3× baseline
```

### Data Source Registry

| Source | What It Captures | Retention | Access |
|--------|-----------------|-----------|--------|
| Cron logs | Job execution times, success/failure | 30 days | `~/.hermes/cron/` |
| Langfuse | API costs, token usage, model performance | 90 days | `cost_analytics()` tool |
| Session DB | Task outcomes, delegation results | 90 days | `session_search()` |
| agentmemory | Action statuses, decisions, patterns | 90 days | `mcp_agentmemory_*` tools |
| ntfy alerts | Alarm timestamps, severity | 7 days | `/tmp/ntfy.log` |
| GATE results | Quality gate pass/fail per artifact | Permanent | `product-quality-gates` skill |

### Alerting Thresholds

```
BUDGET REMAINING → ACTION

> 50%   → GREEN   → No alerts, normal operations
25-50%  → YELLOW  → ntfy warning: "SLO [name] budget at [X]% — caution"
 0-25%  → RED     → ntfy critical: "SLO [name] budget at [X]% — reliability only"
 0%     → EXHAUSTED → ntfy freeze: "FEATURE FREEZE — SLO [name] exhausted"

Alert delivered via: ntfy.sh (hermes-alerts topic)
Alert checked by:    daily_digest() cron job (08:00 daily)
```

---

## 4. Weekly Dashboard Format

Generated every Sunday 20:00 by `weekly-review-planning` skill or manual invocation.

```
# Jeff OS Weekly Dashboard — Week of YYYY-MM-DD

## 📊 BUSINESS
| Metric | This Week | Last Week | Trend |
|--------|-----------|-----------|-------|
| Revenue touches (leads contacted) | — | — | ↑↓→ |
| Pipeline value (estimated) | $— | $— | ↑↓→ |
| New leads captured | — | — | ↑↓→ |
| Campaigns active | — | — | ↑↓→ |

## ✅ QUALITY
| Metric | This Week | SLO Target | Status |
|--------|-----------|------------|--------|
| Task success rate (P0/P1) | —% | ≥90% | 🟢🟡🔴 |
| GATE compliance | —% | ≥95% | 🟢🟡🔴 |
| Briefings delivered on time | —/7 | ≥95% | 🟢🟡🔴 |
| Skills deployed without bugs | — | — | ↑↓→ |

## 🛡️ RELIABILITY
| SLO | Current | Target | Budget Remaining | Status |
|-----|---------|--------|-----------------|--------|
| Lead capture | —% | ≥99% | —% | 🟢🟡🔴 |
| Daily briefing | —% | ≥95% | —% | 🟢🟡🔴 |
| Task success P0/P1 | —% | ≥90% | —% | 🟢🟡🔴 |
| GATE compliance | —% | ≥95% | —% | 🟢🟡🔴 |
| MTTR | —min | <60min | — | 🟢🟡🔴 |
| **Feature freeze** | NO/YES | — | — | — |

## 💰 COST
| Metric | This Week | Budget | Status |
|--------|-----------|--------|--------|
| Total API cost | $— | $—/week | 🟢🟡🔴 |
| Cost per successful task | $— | <$— | 🟢🟡🔴 |
| Top model by cost | — | — | — |
| Provider breakdown | deepseek: $—, openai: $—, ... | — | — |

## 🔒 SECURITY
| Check | Status | Action Needed |
|-------|--------|---------------|
| Open secrets in config | 0 | — |
| Unpinned dependencies | 0 | — |
| Expired API tokens | 0 | — |
| MCP servers with weak auth | 0 | — |
| Last security scan | YYYY-MM-DD | — |

## 🔧 TOIL
| Metric | This Week | Target | Status |
|--------|-----------|--------|--------|
| Human minutes spent (manual fixes) | —min | <30min/week | 🟢🟡🔴 |
| Alarm count (all severity) | — | <5/week | 🟢🟡🔴 |
| Repeated manual tasks identified | — | — | — |
| Automation candidates surfaced | — | — | — |

---
Generated by: Jeff OS Weekly Review
Next dashboard: YYYY-MM-DD
```

---

## 5. Implementation Checklist

- [ ] Set up cron job to compute SLO metrics daily (can piggyback on `daily_digest()`)
- [ ] Add SLO tracking fields to agentmemory (create action chain: "SLO-TRACK-{month}")
- [ ] Configure ntfy alerts for budget thresholds (YELLOW/RED/EXHAUSTED)
- [ ] Create `weekly-dashboard` template in Jeff OS modules
- [ ] Add Feature Freeze enforcement check to `jeff-orchestrator` (gate new task acceptance)
- [ ] Archive monthly SLO reports to `~/.hermes/skills/self/jeff-os-modules/slo-history/`
- [ ] Review initial SLO targets after 1 month of data collection

---

## 6. Decision Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-08-24 | Initial SLOs defined | Based on GPT 5.6 recommendations + Google SRE practices |
| | Budget reset: monthly | Matches business cycle; prevents stale budget accumulation |
| | Feature freeze = full halt | Prevents quality spiral; forces reliability investment |
| | Cost tracked but not gated | Cost targets may be unrealistic early; track first, gate later |

---

*This document replaces ad-hoc health monitoring with structured SRE practices. All Jeff OS operations must respect these SLOs and error budgets.*
