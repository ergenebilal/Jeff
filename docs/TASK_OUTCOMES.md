# Independently verified internal drafts

The original verifier measured worker health. Managed draft plans now have a
specific criterion, `artifact_sha256_matches`: a verifier reopens every output
file and compares its bytes with the immutable approved plan. A SUCCESS claim
alone is insufficient. Missing evidence escalates; changed content fails.

Set `TASK_ARTIFACT_ROOT=/home/hermes/jeff-artifacts` to enable the server worker.
Plans permit only named `.txt`, `.md` or `.json` files inside that managed root.
No arbitrary path, command, customer delivery, or overwrite is implemented.
Each step is persisted in SQLite. Atomic publication, expiry of leases and
hash reconciliation allow recovery after a crash without rewriting a saved
matching file. Existing mismatching files require review.

`POST /tasks` creates a plan; `/plan` and `/queue` submit it. The optional
`scripts/task_draft.py` client resumes the same task ID instead of duplicating
work after a timeout. Inspect `/tasks/{id}/steps`, `/events`, `/evidence` and
authenticated `/tasks/{id}/artifacts/{name}`. Downloading an altered file is
rejected. `verified` means **saved draft content**; `delivered` is always false.
It proves file persistence, not the truth of research claims or delivery.

For plans marked `approval_required`, the ledger creates one approval ID bound
to the immutable input digest. Only the configured owner in their private chat
can approve via a trusted adapter with a separate `APPROVAL_DECISION_KEY`.
The general agent Bridge key cannot call the decision endpoint. Cards expire,
can be renewed, are revoked on cancellation, and are consumed on claim.
Changing a draft requires a new task/digest and a new approval. Keep the
decision key out of agent client environments. Production owner decisions
remain disabled until a trusted owner adapter is configured.

This lifecycle covers managed internal plans. Legacy panel, marketing and
Pablo approval stores still have their own decision lifecycles. The shared
inventory now includes expired native cards, but aggregation is not a full
migration of those stores. External sends and GUI workflows still need their
own outcome observers and recovery policies; never auto-retry an uncertain send.

`scripts/jeff_backup.py` includes `jeff-artifacts` in protected runtime backups.
SQLite migrations add tables/`plan_json` while preserving legacy empty-plan
digests. The cognitive snapshot and panel boundary are documented separately.
