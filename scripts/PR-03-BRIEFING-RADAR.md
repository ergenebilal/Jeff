# PR-03 — Sourced briefing and clinic radar

## Result

`jeff-morning-brief.py` now reads the canonical Bridge SQLite database and
creates a dry-run report when requested. Missing or corrupt sources are `UNKNOWN
(data unavailable)`, never a fabricated zero. Each metric carries its SQL query
and snapshot timestamp in the report object. The text includes the snapshot and
metric query key. Verified work comes only from `task_records.status='verified'`.
The three priorities come from unresolved tasks and candidate draft review.

`proactive_lead_radar.py` now reads up to ten configured official clinic pages.
It performs only GET requests, verifies domain and source URL, rejects private
network targets, records source and observation, and never sends outreach.
Contacts remain `UNVERIFIED` unless found on the retrieved page. A stable key
from normalized domain, company, and city updates an existing candidate.

## Local operation

```powershell
python scripts/proactive_lead_radar.py --sources scripts/clinic_sources.example.json --db C:\path\to\bridge.db
python scripts/jeff-morning-brief.py --db C:\path\to\bridge.db --dry-run C:\path\to\report.txt
```

The CLI only sends a report when `--send` is supplied. That mode requires
`TELEGRAM_BOT_TOKEN` and `ADMIN_CHAT_ID` from the environment. Delivery writes
a unique daily `report_id` to SQLite before the HTTP request. A repeated ID is
rejected. Messages are divided under Telegram's 4096-character limit. Explicit
HTTP 429 responses get at most three attempts with exponential backoff;
timeouts and ambiguous responses are recorded as `UNKNOWN` without blind
resending. No production delivery was performed in this PR.

## Migration and rollback

Startup adds `clinic_leads` and `report_deliveries` to the same Bridge database.
Existing task and legacy tables are unchanged. Old code can still read this
database. Keep the new tables during rollback for audit and duplicate control.

```powershell
git switch codex/pr-02-task-contract
```

For a live rollback, restore the prior briefing and radar scripts from the
previous deployed revision; retain the SQLite file and disable any new
scheduler entry. Neither script is scheduled or deployed by this PR.

## Test and smoke evidence

`python -m unittest -v scripts.test_executive_briefing` runs real SQLite and
localhost HTTP fixtures. It checks task counts, source dedupe, corrupt data,
message splitting, and duplicate Telegram `report_id` blocking.

The controlled public read on 28 September 2026 used two clinic-owned pages:
`https://dentoniks.com/` and
`https://www.vitabursa.com/tr-TR/iletisim`. One page was readable by the
scanner, producing one `UNVERIFIED`, `NOT_SENT` candidate. The second run
reported `created=0, updated=1`; SQLite still contained one candidate.
The dry-run report at a local temporary path showed `Yeni leadler: 1` and
selected that candidate for draft review. No contact was made and no real
Telegram message was sent.

## Limitations

The scanner skips unavailable pages. `UNVERIFIED` means the contact string was
not visible in the fetched page; it is not a claim that the address is invalid.
The example source list is a controlled sample, not a claim of commercial fit.
No appointment, clinic performance, or patient data is inferred.
