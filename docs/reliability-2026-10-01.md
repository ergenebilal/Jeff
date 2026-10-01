# Jeff reliability corrections — 2026-10-01

Simulation previously marked marketing campaigns SENT and verified even though
no real sender existed. Telegram then described failed executions as success.
Simulation now returns SIMULATED with delivered=false and verified=false;
the approved draft remains available. Unsupported live delivery and the legacy
social publisher return explicit failure. No outbound sender is introduced.
Telegram approval callbacks require the configured owner in the owner's chat.

The Pablo guard now requires approval for missing/ambiguous new-contact flags,
public biography edits, live campaign delivery, recognised deletion commands
regardless of argument order, encoded/dynamic commands, and recognised indirect
desktop input. Coordinate clicks use the actual accessibility control and window;
an unresolved point on a sensitive messaging surface requires approval.

Authenticated Pablo heartbeats publish read-only approval counts. Bridge exposes
these together with its task ledger through authenticated GET /approvals. Optional
PANEL_DB_PATH enables panel counts in that endpoint; operational reports include
the installed panel database by default. Missing/incomplete/older-than-180-second
node snapshots are named as unavailable. Expired journal approvals are separate
from actionable waiting requests. This is a shared inventory, not a replacement
for the separate approval lifecycles; requests may still overlap across stores.

Backups now include jeff-beyin, cybergeneos-data and cybergeneos, SQLite .sqlite3
files and the CybergeneOS service configuration. SQLite uses the existing online
snapshot and integrity checks. The active manifest now covers operational cron
scripts, marketing dependencies and the runner's test modules. The secret scanner
fixture no longer resembles a real API credential.

## Validation

- Windows Bridge group: 228 tests, passed; 2 platform/environment skips.
- Active compile: 41 Python files; fatal-rule lint passed.
- Task schema/digest validation and deliberate broken fixture rejection passed.
- Regressions mock senders and desktop input; no test sends a real message.
- Linux validation, deployment and backup results are recorded after rollout below.

## Limits and next implementation work

This patch does not complete phases 2.7 or 5.3 of the Jarvis plan. General tasks
still need action-specific outcome verifiers and reconciliation. Approval needs
content/recipient binding, expiry and execution-time context validation across
all channels. Shell classification is not an isolation boundary for arbitrary
programs; indirect operations outside the recognised patterns remain possible.
Existing-contact flags still need validation against trusted history. Real
senders require provider acknowledgements and recipient/content verification.
Panel external content must be separated from trusted instructions, and the
cognitive service needs reproducible source/dependency coverage. A fresh-server
full restore remains separate from SQLite/archive verification.
