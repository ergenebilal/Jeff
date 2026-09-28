# PR-01 Bridge migration and rollback

The Bridge now requires `BRIDGE_KEY`. It binds to `127.0.0.1` by default.
The systemd unit reads `BRIDGE_KEY` from `/etc/jeff-bridge.env`; provision that
file with owner-only permissions before starting the unit.
Set `BRIDGE_HOST` and `BRIDGE_ALLOWED_IPS` explicitly when remote workers need
access. The Pablo worker must send its stable `node_id` as `X-Worker-ID`.
The legacy Alfred client now only sends heartbeats; Pablo/Hermes executes tasks.

On startup, the SQLite migration adds `digest`, `policy`, `worker_id`, and
`attempt` to `alfred_events`, plus `alfred_task_claims`, `alfred_results`, and
`alfred_result_quarantine`. Existing rows remain in place. Legacy rows without
a digest cannot produce a verified result; they require manual reconciliation.
Old code ignores the added columns and tables, so source rollback does not
need a destructive database migration.

To roll back the source on the PR branch, stop the Bridge and Pablo worker,
then run `git revert <PR-01-commit-sha>` for each PR-01 commit in reverse order.
Keep the SQLite database and take a backup before any later schema cleanup.
Never restore the old embedded Bridge key; set a fresh `BRIDGE_KEY` in the
service environment. Existing result rows remain unverified after rollback.

Local verification uses a fake TaskGuard browser action and localhost HTTP.
No external browser, message, or other side effect is executed.
