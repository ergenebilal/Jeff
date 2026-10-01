#!/usr/bin/env python3
"""
Jeff Bridge API — FastAPI service bridging Jeff (Aider) ↔ Alfred (Windows)
Port: 7700 | Auth: X-Bridge-Key header | DB: SQLite bridge.db
"""

import asyncio
import hashlib
import hmac
import ipaddress
import json
from coding_contract import validate_contract
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse
from urllib.request import urlopen

import aiosqlite
from fastapi import FastAPI, Header, HTTPException, Request
from pydantic import BaseModel
from task_contract import TaskConflict, TaskCreate, TaskLedger, TaskNotFound

# ── Config ─────────────────────────────────────────────────────────────────────
BRIDGE_KEY = os.environ.get("BRIDGE_KEY")
DB_PATH = os.environ.get("BRIDGE_DB_PATH", os.path.join(os.path.dirname(__file__), "bridge.db"))
LOG_PATH = os.path.join(os.path.dirname(__file__), "bridge.log")
ALFRED_TIMEOUT_SEC = 60
HOST = None
PORT = int(os.environ.get("BRIDGE_PORT", "7700"))

def validate_bridge_key(key):
    if not key or key.strip() != key or key.lower() in {
        'cybergene-bridge-2026', 'changeme', 'change-me', 'test', 'development', 'placeholder'
    }:
        raise ValueError('BRIDGE_KEY must be configured with a non-placeholder secret')
    return key

def host_from_environment(environ):
    host = environ.get('BRIDGE_HOST', '127.0.0.1')
    if not host:
        raise ValueError('BRIDGE_HOST cannot be empty')
    return host

HOST = host_from_environment(os.environ)

def task_digest(type_, payload, policy):
    canonical = json.dumps({'type': type_, 'payload': payload, 'policy': policy},
                           sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("jeff_bridge")


# ── DB init ────────────────────────────────────────────────────────────────────
async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id     TEXT PRIMARY KEY,
                source      TEXT,
                prompt      TEXT,
                files       TEXT,
                priority    INTEGER DEFAULT 5,
                status      TEXT DEFAULT 'queued',
                result      TEXT,
                error       TEXT,
                created_at  TEXT,
                started_at  TEXT,
                finished_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS alfred_events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id     TEXT,
                type        TEXT,
                payload     TEXT,
                status      TEXT DEFAULT 'pending',
                created_at  TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS alfred_heartbeat (
                id        INTEGER PRIMARY KEY CHECK (id = 1),
                agent     TEXT,
                status    TEXT,
                version   TEXT,
                last_seen REAL
            )
        """)
        async with db.execute('PRAGMA table_info(tasks)') as cursor:
            columns = {row[1] for row in await cursor.fetchall()}
        for column in ('workspace', 'test_argv'):
            if column not in columns:
                await db.execute('ALTER TABLE tasks ADD COLUMN ' + column + ' TEXT')
        async with db.execute('PRAGMA table_info(alfred_events)') as cursor:
            event_columns = {row[1] for row in await cursor.fetchall()}
        if 'delivered_at' not in event_columns:
            await db.execute('ALTER TABLE alfred_events ADD COLUMN delivered_at REAL')
        for column, definition in {
            'digest': 'TEXT', 'policy': 'TEXT', 'worker_id': 'TEXT',
            'attempt': 'INTEGER DEFAULT 0'
        }.items():
            if column not in event_columns:
                await db.execute(f'ALTER TABLE alfred_events ADD COLUMN {column} {definition}')
        await db.execute('CREATE TABLE IF NOT EXISTS alfred_task_claims (task_id TEXT PRIMARY KEY, digest TEXT NOT NULL)')
        await db.execute('CREATE TABLE IF NOT EXISTS alfred_results (task_id TEXT PRIMARY KEY, digest TEXT NOT NULL, worker_id TEXT NOT NULL, attempt INTEGER NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL)')
        await db.execute('CREATE TABLE IF NOT EXISTS alfred_result_quarantine (id INTEGER PRIMARY KEY, task_id TEXT, reason TEXT, created_at TEXT)')
        await db.commit()
    await asyncio.to_thread(TaskLedger(DB_PATH).initialize)
    log.info("DB initialised at %s", DB_PATH)


# ── Lifespan ───────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_bridge_key(BRIDGE_KEY)
    if HOST == '0.0.0.0':
        log.warning('Bridge configured to bind all interfaces')
    await init_db()
    from aider_runner import start_runner
    runner_task = asyncio.create_task(start_runner())
    app.state.runner_task = runner_task
    log.info("Aider runner started")
    yield
    runner_task.cancel()
    try:
        await runner_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Jeff Bridge API", version="1.0.0", lifespan=lifespan)

# ── Isim temizligi (30.09.2026) ────────────────────────────────────────────────
# Windows ajaninin gercek adi PABLO (kendini oyle tanitiyor). "Alfred" eski
# dongunun adi; uclar hala /alfred/*. Bu middleware /pablo/* yollarini
# /alfred/*'a cevirir — boylece iki ad da calisir, hicbir istemci bozulmaz.
# Uclar kalici olarak /pablo/*'ya tasinana kadar gecis koprusudur.
@app.middleware('http')
async def pablo_alias(request: Request, call_next):
    path = request.scope.get('path', '')
    if path == '/pablo' or path.startswith('/pablo/'):
        request.scope['path'] = '/alfred' + path[len('/pablo'):]
    return await call_next(request)


@app.middleware('http')
async def enforce_ip_allowlist(request: Request, call_next):
    from fastapi.responses import JSONResponse
    raw = os.environ.get('BRIDGE_ALLOWED_IPS', '')
    allowed = {part.strip() for part in raw.split(',') if part.strip()}
    try:
        client_ip = ipaddress.ip_address(request.client.host)
        permitted = client_ip.is_loopback or any(client_ip == ipaddress.ip_address(item) for item in allowed)
    except (ValueError, AttributeError):
        permitted = False
    if not permitted:
        return JSONResponse(status_code=403, content={'detail': 'Client IP not allowed'})
    return await call_next(request)


# ── Auth ───────────────────────────────────────────────────────────────────────
def require_key(x_bridge_key: Optional[str] = Header(default=None)):
    if not BRIDGE_KEY or not x_bridge_key or not hmac.compare_digest(x_bridge_key, BRIDGE_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing X-Bridge-Key")


def require_task_worker_key(x_task_worker_key: Optional[str]):
    configured = os.environ.get('TASK_WORKER_KEY')
    if (not configured or configured == BRIDGE_KEY or not x_task_worker_key
            or not hmac.compare_digest(configured, x_task_worker_key)):
        raise HTTPException(status_code=401, detail='Invalid or missing X-Task-Worker-Key')


def task_health_probe():
    """Verifier-owned observation of a configured local worker health endpoint."""
    url = os.environ.get('TASK_WORKER_HEALTH_URL', '')
    parsed = urlparse(url)
    if parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1', 'localhost', '::1'):
        return {'status_code': 0, 'status': 'unconfigured'}
    try:
        with urlopen(url, timeout=3) as response:
            data = json.load(response)
            return {'status_code': response.status, 'status': data.get('status')}
    except (OSError, ValueError, TypeError):
        return {'status_code': 0, 'status': 'unavailable'}


async def task_call(method, *args):
    try:
        return await asyncio.to_thread(getattr(TaskLedger(DB_PATH), method), *args)
    except TaskNotFound as exc:
        raise HTTPException(status_code=404, detail='Task not found') from exc
    except TaskConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


class TaskActorRequest(BaseModel):
    actor: str


class TaskClaimRequest(BaseModel):
    worker: str
    lease_seconds: int = 30


class TaskFinishRequest(BaseModel):
    worker: str
    execution: dict


class TaskEscalateRequest(BaseModel):
    actor: str
    reason: str


@app.post('/tasks')
async def task_create(body: TaskCreate, x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    return await task_call('create', body)


@app.get('/tasks/{task_id}')
async def task_get(task_id: str, x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    return await task_call('get', task_id)


@app.get('/tasks/{task_id}/events')
async def task_events(task_id: str, x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    return await task_call('events', task_id)


@app.get('/tasks/{task_id}/evidence')
async def task_evidence(task_id: str, x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    return await task_call('evidence', task_id)


@app.get('/tasks/{task_id}/rejections')
async def task_rejections(task_id: str, x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    return await task_call('rejections', task_id)


@app.post('/tasks/{task_id}/plan')
async def task_plan(task_id: str, body: TaskActorRequest,
                    x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    return await task_call('plan', task_id, body.actor)


@app.post('/tasks/{task_id}/queue')
async def task_queue(task_id: str, body: TaskActorRequest,
                     x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    return await task_call('queue', task_id, body.actor)


@app.post('/tasks/{task_id}/claim')
async def task_claim(task_id: str, body: TaskClaimRequest,
                     x_task_worker_key: Optional[str] = Header(default=None)):
    require_task_worker_key(x_task_worker_key)
    return await task_call('claim', task_id, body.worker, body.lease_seconds)


@app.post('/tasks/{task_id}/start')
async def task_start(task_id: str, body: TaskClaimRequest,
                     x_task_worker_key: Optional[str] = Header(default=None)):
    require_task_worker_key(x_task_worker_key)
    return await task_call('start', task_id, body.worker)


@app.post('/tasks/{task_id}/finish')
async def task_finish(task_id: str, body: TaskFinishRequest,
                      x_task_worker_key: Optional[str] = Header(default=None)):
    require_task_worker_key(x_task_worker_key)
    return await task_call('finish', task_id, body.worker, body.execution)


@app.post('/tasks/{task_id}/verify')
async def task_verify(task_id: str, x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    return await task_call('verify', task_id, task_health_probe)


@app.post('/tasks/{task_id}/cancel')
async def task_cancel(task_id: str, body: TaskActorRequest,
                      x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    return await task_call('cancel', task_id, body.actor)


@app.post('/tasks/{task_id}/reconcile')
async def task_reconcile(task_id: str, body: TaskActorRequest,
                         x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    return await task_call('reconcile', task_id, body.actor)


@app.post('/tasks/{task_id}/escalate')
async def task_escalate(task_id: str, body: TaskEscalateRequest,
                        x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    return await task_call('escalate', task_id, body.actor, body.reason)


# ── Pydantic models ────────────────────────────────────────────────────────────
class TaskRequest(BaseModel):
    task_id: Optional[str] = None
    prompt: str
    files: list[str] = []
    priority: int = 5
    source: str = "unknown"
    workspace: str
    test_argv: list[str]


class AlfredResult(BaseModel):
    task_id: str
    type: str
    result: Optional[str] = None
    screenshot_b64: Optional[str] = None
    status: str = "UNKNOWN"
    ok: bool = False
    request_id: Optional[str] = None
    approval_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: Optional[str] = None
    digest: Optional[str] = None
    worker_id: Optional[str] = None
    attempt: Optional[int] = None


class AlfredHeartbeat(BaseModel):
    agent: str = "alfred"
    status: str = "ok"
    version: str = "unknown"
    timestamp: Optional[str] = None


# ── Endpoints ──────────────────────────────────────────────────────────────────
@app.get('/aider/capabilities')
async def aider_capabilities(x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    return {'contract_version': 2, 'workspace_required': True, 'test_evidence_required': True}

@app.post("/aider/task")
async def create_aider_task(body: TaskRequest, x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    try:
        workspace, files, test_argv = validate_contract(body.workspace, body.files, body.test_argv)
    except (ValueError, OSError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    task_id = body.task_id or str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('BEGIN IMMEDIATE')
        async with db.execute('SELECT 1 FROM task_records WHERE task_id=?', (task_id,)) as cur:
            if await cur.fetchone():
                raise HTTPException(status_code=409, detail='Task ID belongs to task contract')
        async with db.execute('SELECT 1 FROM alfred_events WHERE task_id=? LIMIT 1', (task_id,)) as cur:
            if await cur.fetchone():
                raise HTTPException(status_code=409, detail='Task ID belongs to Pablo queue')
        async with db.execute('SELECT prompt,files,workspace,test_argv,status FROM tasks WHERE task_id=?', (task_id,)) as cur:
            existing = await cur.fetchone()
        contract = (body.prompt, json.dumps(files), workspace, json.dumps(test_argv))
        if existing:
            if tuple(existing[:4]) != contract:
                raise HTTPException(status_code=409, detail='Task ID content conflict')
            return {'task_id': task_id, 'status': existing[4]}
        await db.execute('INSERT INTO tasks(task_id,source,prompt,files,priority,status,created_at,workspace,test_argv) VALUES(?,?,?,?,?,?,?,?,?)',
            (task_id, body.source, contract[0], contract[1], body.priority, 'queued', now, contract[2], contract[3]))
        await db.commit()
    return {'task_id': task_id, 'status': 'queued'}


@app.get("/aider/task/{task_id}")
async def get_aider_task(task_id: str, x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,)) as cur:
            row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    return dict(row)


class AlfredTaskRequest(BaseModel):
    task_id: Optional[str] = None
    type: str  # WHATSAPP_DRAFT, SCREENSHOT_REQUEST, BROWSER_ACTION, etc.
    payload: dict | str
    policy: dict = {}


@app.post("/alfred/task")
async def create_alfred_task(body: AlfredTaskRequest, x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    task_id = body.task_id or str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    payload_str = json.dumps(body.payload, sort_keys=True, ensure_ascii=False)
    digest = task_digest(body.type, body.payload, body.policy)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('BEGIN IMMEDIATE')
        async with db.execute('SELECT 1 FROM task_records WHERE task_id=?', (task_id,)) as cursor:
            if await cursor.fetchone():
                raise HTTPException(status_code=409, detail='Task ID belongs to task contract')
        async with db.execute('SELECT 1 FROM tasks WHERE task_id=?', (task_id,)) as cursor:
            if await cursor.fetchone():
                raise HTTPException(status_code=409, detail='Task ID belongs to Aider queue')
        async with db.execute('SELECT type,payload,policy,digest,status FROM alfred_events WHERE task_id=?', (task_id,)) as cursor:
            existing = await cursor.fetchone()
        if existing:
            old_digest = existing[3] or task_digest(existing[0], json.loads(existing[1]), json.loads(existing[2] or '{}'))
            if old_digest != digest:
                raise HTTPException(status_code=409, detail='Task ID content conflict')
            return {'task_id': task_id, 'status': existing[4], 'type': body.type, 'digest': digest}
        await db.execute('INSERT INTO alfred_task_claims(task_id,digest) VALUES(?,?)', (task_id,digest))
        await db.execute(
            "INSERT INTO alfred_events (task_id,type,payload,status,created_at,digest,policy) VALUES (?,?,?,'pending',?,?,?)",
            (task_id, body.type, payload_str, now, digest, json.dumps(body.policy, sort_keys=True)),
        )
        await db.commit()

    log.info("ALFRED_TASK_QUEUED  task_id=%s  type=%s", task_id, body.type)
    return {"task_id": task_id, "status": "queued", "type": body.type, "digest": digest}


@app.post("/alfred/result")
async def alfred_result(body: AlfredResult, x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('BEGIN IMMEDIATE')
        async with db.execute('SELECT type,digest,worker_id,attempt,status FROM alfred_events WHERE task_id=?', (body.task_id,)) as cursor:
            event = await cursor.fetchone()
        reason = None
        if not event:
            reason = 'unknown_task'
        elif (event[0] != body.type or event[1] != body.digest or event[2] != body.worker_id
              or event[3] != body.attempt or event[4] != 'delivered'
              or body.request_id != body.task_id):
            reason = 'binding_mismatch_or_late_result'
        if reason:
            await db.execute('INSERT INTO alfred_result_quarantine(task_id,reason,created_at) VALUES(?,?,?)',
                             (body.task_id, reason, now))
            await db.commit()
            return {'status': 'quarantined', 'task_id': body.task_id}
        if body.status == 'APPROVAL_REQUIRED':
            await db.commit()
            return {'status': 'approval_required', 'task_id': body.task_id}
        payload = json.dumps({'result': body.result, 'status': body.status, 'ok': False,
                              'request_id': body.request_id, 'approval_id': body.approval_id,
                              'error': body.error})
        await db.execute('INSERT INTO alfred_results(task_id,digest,worker_id,attempt,status,payload,created_at) VALUES(?,?,?,?,?,?,?)',
                         (body.task_id, body.digest, body.worker_id, body.attempt, 'unverified', payload, now))
        await db.execute("UPDATE alfred_events SET status='unverified' WHERE task_id=?", (body.task_id,))
        await db.commit()
    log.info("ALFRED_RESULT  task_id=%s  type=%s", body.task_id, body.type)
    return {"status": "unverified", "task_id": body.task_id}


@app.get('/alfred/task/{task_id}')
async def alfred_task_status(task_id: str, x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM alfred_events WHERE task_id=? ORDER BY id DESC LIMIT 1', (task_id,)) as cur:
            row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='Unknown task')
    if row['status'] == 'unverified':
        return {'task_id': task_id, 'status': 'unverified', 'ok': False}
    if row['digest'] is None:
        return {'task_id': task_id, 'status': 'legacy_unverified', 'ok': False}
    return {'task_id': task_id, 'status': row['status'], 'ok': False,
            'type': row['type'], 'digest': row['digest'], 'worker_id': row['worker_id'],
            'attempt': row['attempt']}

@app.get("/alfred/tasks")
async def alfred_get_tasks(
    timeout: int = 30,
    x_bridge_key: Optional[str] = Header(default=None),
    x_worker_id: Optional[str] = Header(default=None),
):
    require_key(x_bridge_key)
    if not x_worker_id or len(x_worker_id) > 128:
        raise HTTPException(status_code=422, detail='X-Worker-ID required')
    start_time = time.time()
    max_wait = min(max(timeout, 1), 60)

    while True:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            await db.execute('BEGIN IMMEDIATE')
            async with db.execute(
                "SELECT * FROM alfred_events WHERE status='pending' OR (status='delivered' AND worker_id=? AND delivered_at < ?) ORDER BY created_at ASC LIMIT 10",
                (x_worker_id, time.time() - 120),
            ) as cur:
                rows = await cur.fetchall()

            if rows:
                tasks = []
                for r in rows:
                    reconcile_only = r['status'] == 'delivered'
                    attempt = (r['attempt'] or 0) if reconcile_only else 1
                    worker_id = r['worker_id'] if reconcile_only else x_worker_id
                    await db.execute("UPDATE alfred_events SET status='delivered', delivered_at=?,worker_id=?,attempt=? WHERE id=?",
                                     (time.time(), worker_id, attempt, r['id']))
                    task = dict(r)
                    task.update(worker_id=worker_id, attempt=attempt, reconcile_only=reconcile_only)
                    tasks.append(task)
                await db.commit()
                return {"tasks": tasks}
            await db.commit()

        if time.time() - start_time >= max_wait:
            return {"tasks": []}

        await asyncio.sleep(0.2)


@app.post("/alfred/heartbeat")
async def alfred_heartbeat(body: AlfredHeartbeat, x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    now = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO alfred_heartbeat (id, agent, status, version, last_seen)
               VALUES (1, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET
                   agent=excluded.agent, status=excluded.status,
                   version=excluded.version, last_seen=excluded.last_seen""",
            (body.agent, body.status, body.version, now),
        )
        await db.commit()
    log.debug("HEARTBEAT  agent=%s  status=%s", body.agent, body.status)
    return {"status": "ok", "received_at": datetime.now(timezone.utc).isoformat()}


@app.get("/alfred_client")
async def get_alfred_client(x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    if os.environ.get('BRIDGE_ALLOW_CLIENT_DOWNLOAD') != '1':
        raise HTTPException(status_code=404, detail='Client download disabled')
    from fastapi.responses import FileResponse
    client_path = os.path.join(os.path.dirname(__file__), "alfred_client.py")
    return FileResponse(client_path, media_type="text/x-python", filename="alfred_client.py")


@app.get("/health")
async def health():
    alfred_online = False
    queued = 0
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT agent,last_seen FROM alfred_heartbeat WHERE id = 1") as cur:
            hb = await cur.fetchone()
        if hb and hb['agent'] == 'pablo' and (time.time() - hb["last_seen"]) < ALFRED_TIMEOUT_SEC:
            alfred_online = True
        async with db.execute("SELECT COUNT(*) as cnt FROM tasks WHERE status = 'queued'") as cur:
            row = await cur.fetchone()
        queued = row["cnt"] if row else 0
    return {
        "status": "ok",
        "aider_ready": bool(getattr(app.state, 'runner_task', None) and not app.state.runner_task.done()),
        "alfred_online": alfred_online,
        "queued_tasks": queued,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    validate_bridge_key(BRIDGE_KEY)
    uvicorn.run("jeff_bridge_api:app", host=HOST, port=PORT, reload=False, log_level="info")
