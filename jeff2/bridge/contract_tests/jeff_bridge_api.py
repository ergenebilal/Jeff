#!/usr/bin/env python3
"""
Jeff Bridge API — FastAPI service bridging Jeff (Aider) ↔ Alfred (Windows)
Port: 7700 | Auth: X-Bridge-Key header | DB: SQLite bridge.db
"""

import asyncio
import json
from coding_contract import validate_contract
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional

import aiosqlite
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

# ── Config ─────────────────────────────────────────────────────────────────────
BRIDGE_KEY = os.environ.get("BRIDGE_KEY")
DB_PATH = os.path.join(os.path.dirname(__file__), "bridge.db")
LOG_PATH = os.path.join(os.path.dirname(__file__), "bridge.log")
ALFRED_TIMEOUT_SEC = 60
HOST = "0.0.0.0"
PORT = 7700

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
        await db.commit()
    log.info("DB initialised at %s", DB_PATH)


# ── Lifespan ───────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    from aider_runner import start_runner
    runner_task = asyncio.create_task(start_runner())
    log.info("Aider runner started")
    yield
    runner_task.cancel()
    try:
        await runner_task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="Jeff Bridge API", version="1.0.0", lifespan=lifespan)


# ── Auth ───────────────────────────────────────────────────────────────────────
def require_key(x_bridge_key: Optional[str] = Header(default=None)):
    if not BRIDGE_KEY or not x_bridge_key or x_bridge_key != BRIDGE_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Bridge-Key")


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


@app.post("/alfred/task")
async def create_alfred_task(body: AlfredTaskRequest, x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    import json
    task_id = body.task_id or str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    payload_str = json.dumps(body.payload) if isinstance(body.payload, dict) else str(body.payload)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO alfred_events (task_id, type, payload, status, created_at) VALUES (?, ?, ?, 'pending', ?)",
            (task_id, body.type, payload_str, now),
        )
        await db.commit()

    log.info("ALFRED_TASK_QUEUED  task_id=%s  type=%s", task_id, body.type)
    return {"task_id": task_id, "status": "queued", "type": body.type}


@app.post("/alfred/result")
async def alfred_result(body: AlfredResult, x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    import json
    now = datetime.now(timezone.utc).isoformat()
    payload = json.dumps({
        "result": body.result,
        "status": body.status, "ok": body.ok, "request_id": body.request_id,
        "approval_id": body.approval_id, "error": body.error,
        "screenshot_b64": body.screenshot_b64[:40] + "..." if body.screenshot_b64 else None,
    })
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO alfred_events (task_id, type, payload, created_at, status) VALUES (?, ?, ?, ?, 'result')",
            (body.task_id, body.type, payload, now),
        )
        await db.execute("UPDATE alfred_events SET status=? WHERE task_id=? AND status IN ('pending','delivered')",
                         (body.status, body.task_id))
        await db.commit()
    log.info("ALFRED_RESULT  task_id=%s  type=%s", body.task_id, body.type)
    return {"status": "received", "task_id": body.task_id}


@app.get('/alfred/task/{task_id}')
async def alfred_task_status(task_id: str, x_bridge_key: Optional[str] = Header(default=None)):
    require_key(x_bridge_key)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute('SELECT * FROM alfred_events WHERE task_id=? ORDER BY id DESC LIMIT 1', (task_id,)) as cur:
            row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail='Unknown task')
    if row['status'] == 'result':
        return dict(task_id=task_id, **json.loads(row['payload']))
    return {'task_id': task_id, 'status': row['status'], 'ok': False}

@app.get("/alfred/tasks")
async def alfred_get_tasks(
    timeout: int = 30,
    x_bridge_key: Optional[str] = Header(default=None)
):
    require_key(x_bridge_key)
    start_time = time.time()
    max_wait = min(max(timeout, 1), 60)

    while True:
        async with aiosqlite.connect(DB_PATH) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM alfred_events WHERE status = 'pending' OR (status='delivered' AND (delivered_at IS NULL OR delivered_at < ?)) ORDER BY created_at ASC LIMIT 10", (time.time()-120,)
            ) as cur:
                rows = await cur.fetchall()

            if rows:
                tasks = [dict(r) for r in rows]
                for r in rows:
                    await db.execute("UPDATE alfred_events SET status = 'delivered', delivered_at=? WHERE id = ?", (time.time(), r["id"]))
                await db.commit()
                return {"tasks": tasks}

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
async def get_alfred_client():
    from fastapi.responses import FileResponse
    client_path = os.path.join(os.path.dirname(__file__), "alfred_client.py")
    return FileResponse(client_path, media_type="text/x-python", filename="alfred_client.py")


@app.get("/health")
async def health():
    alfred_online = False
    queued = 0
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT last_seen FROM alfred_heartbeat WHERE id = 1") as cur:
            hb = await cur.fetchone()
        if hb and (time.time() - hb["last_seen"]) < ALFRED_TIMEOUT_SEC:
            alfred_online = True
        async with db.execute("SELECT COUNT(*) as cnt FROM tasks WHERE status = 'queued'") as cur:
            row = await cur.fetchone()
        queued = row["cnt"] if row else 0
    return {
        "status": "ok",
        "aider_ready": True,
        "alfred_online": alfred_online,
        "queued_tasks": queued,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Main ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("jeff_bridge_api:app", host=HOST, port=PORT, reload=False, log_level="info")
