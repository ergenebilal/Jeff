# PR-02 — Task contract and verifier

## Result

The Bridge now has an additive, durable task API. A task moves through explicit
states and writes immutable events and evidence to SQLite. Only the verifier may
mark a task `verified`, after checking worker execution evidence and a separate
localhost health observation. The current verifier rule supports the read-only
`pablo_health_ok` criterion. Other criteria fail closed.

`/aider/task` and `/alfred/task` remain available. All three task namespaces
reject reuse of a task ID owned by another namespace. Existing legacy success
rules are unchanged; Pablo results remain unverified until a verifier checks
them. Existing TaskGuard remains the execution boundary for Pablo actions.

## Configuration

- `BRIDGE_KEY`: existing Bridge caller key.
- `TASK_WORKER_KEY`: distinct key for `/tasks/{id}/claim`, `/start`, and
  `/finish`. If missing or equal to `BRIDGE_KEY`, these routes return 401.
- `TASK_WORKER_HEALTH_URL`: verifier-owned local HTTP health endpoint. Only
  loopback URLs are accepted. Missing or unhealthy responses fail verification.
- `BRIDGE_DB_PATH`: existing SQLite database path.

No new package dependency was added. The verifier never accepts a URL from a
task or from worker execution evidence.

## API

`POST /tasks` accepts the task contract. `GET /tasks/{id}`, `/events`,
`/evidence`, and `/rejections` expose its state and audit records. The state
routes are `/plan`, `/queue`, `/claim`, `/start`, `/finish`, `/verify`, `/cancel`,
`/reconcile`, and `/escalate`. FastAPI publishes the exact request schemas at
`/openapi.json`. The worker's `/finish` response must contain a TaskGuard result
with `request_id` equal to the task ID. An `APPROVAL_REQUIRED` result moves the
task to `waiting_approval`; it never becomes verified. A side-effecting task
does not auto-retry after lease expiry.

## Database migration and rollback

Startup adds four new tables and append-only triggers. Existing tables and
columns are unchanged, so old code can read the database after rollback. Keep
the new tables for audit and forward compatibility.

From the repository checkout, restore the previous Bridge code with:

```powershell
git switch codex/pr-01-bridge-security
```

For a production rollback, restore the prior deployed Bridge files and restart
its service; keep the SQLite file. Do not delete task tables or evidence. New
`/tasks` API clients must stop using those routes after rollback.

## Verification

```powershell
& 'C:\Users\lenovo\Desktop\jeff-pablo-codex-spec\Jeff-source\.venv\Scripts\python.exe' -m unittest -v jeff2.bridge.test_task_contract jeff2.bridge.test_task_http jeff2.bridge.test_bridge_security jeff2.bridge.test_coding_bridge
```

The HTTP smoke starts a real local Bridge process, local health server, and
SQLite backed TaskGuard. It performs a read-only ping, verifies the outcome,
checks event and evidence records, rejects a duplicate claim, checks missing
worker authorization, and checks legacy task compatibility.

## Remaining scope

Live Pablo worker adoption of the new routes and a trusted approval-resume
protocol are separate integration work. Until then, side-effecting new tasks
wait for approval or fail verification; this PR must not be treated as a live
end-to-end rollout of side effects.
