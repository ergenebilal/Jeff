#!/usr/bin/env python3
"""
Aider Runner — polls bridge.db for queued tasks, runs Aider CLI, writes results back.
Max concurrency: 2 | Timeout: 300s | Poll interval: 5s
"""

import asyncio
import json
import logging
import os
from coding_contract import validate_contract
from datetime import datetime, timezone

import aiosqlite

DB_PATH = os.path.join(os.path.dirname(__file__), "bridge.db")

AIDER_BIN = os.path.expanduser("~/.local/bin/aider")
AIDER_MODEL = "openai/claude-3-5-sonnet-latest"
AIDER_API_BASE = "http://127.0.0.1:8999/v1"
AIDER_API_KEY = "antigravity"
TASK_TIMEOUT = 300
MAX_CONCURRENT = 2
POLL_INTERVAL = 5

log = logging.getLogger("aider_runner")


async def run_aider_task(task: dict):
    """Execute a single Aider task as an async subprocess."""
    task_id = task["task_id"]
    prompt = task["prompt"]
    now = datetime.now(timezone.utc).isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("UPDATE tasks SET status='running',started_at=? WHERE task_id=? AND status='queued'", (now, task_id))
        await db.commit()
        if cursor.rowcount != 1:
            return
    try:
        task_cwd, files, test_argv = validate_contract(task.get('workspace'),
            json.loads(task.get('files') or '[]'), json.loads(task.get('test_argv') or '[]'))
    except Exception as exc:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("UPDATE tasks SET status='error',error=?,finished_at=? WHERE task_id=?",
                ('Invalid coding contract: ' + str(exc), now, task_id))
            await db.commit()
        return

    cmd = [
        AIDER_BIN,
        "--model", AIDER_MODEL,
        "--message", prompt,
        "--yes",
        "--no-auto-commits",
        "--no-show-model-warnings",
    ]

    # Add --no-git if running outside an initialized git repository
    if not os.path.exists(os.path.join(task_cwd, ".git")):
        cmd.append("--no-git")

    if files:
        for f in files:
            abs_f = os.path.abspath(f)
            if os.path.dirname(abs_f) == task_cwd:
                cmd.append(os.path.basename(abs_f))
            else:
                cmd.append(abs_f)

    env = os.environ.copy()
    env["OPENAI_API_BASE"] = AIDER_API_BASE
    env["OPENAI_API_KEY"] = AIDER_API_KEY

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=task_cwd,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=TASK_TIMEOUT)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            raise TimeoutError(f"Aider task timed out after {TASK_TIMEOUT}s")

        finished = datetime.now(timezone.utc).isoformat()
        output = stdout.decode(errors="replace")
        err_output = stderr.decode(errors="replace")

        evidence = {'workspace': task_cwd, 'coder_exit_code': proc.returncode,
                    'coder_stdout': output[-12000:], 'coder_stderr': err_output[-4000:],
                    'test_argv': test_argv}
        if proc.returncode == 0:
            test_proc = await asyncio.create_subprocess_exec(*test_argv, cwd=task_cwd,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            try:
                test_out, test_err = await asyncio.wait_for(test_proc.communicate(), timeout=TASK_TIMEOUT)
            except asyncio.TimeoutError:
                test_proc.kill()
                await test_proc.communicate()
                raise TimeoutError('Verification test timed out')
            evidence.update(test_exit_code=test_proc.returncode,
                test_stdout=test_out.decode(errors='replace')[-12000:], test_stderr=test_err.decode(errors='replace')[-4000:])
            status = 'verified' if test_proc.returncode == 0 else 'error'
            error = None if status == 'verified' else 'Verification test failed'
        else:
            status, error = 'error', 'Coder process failed'
        result = json.dumps(evidence)

    except Exception as exc:
        finished = datetime.now(timezone.utc).isoformat()
        status = "error"
        result = None
        error = str(exc)
        log.error("TASK_EXCEPTION  task_id=%s  exc=%s", task_id, exc)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tasks SET status=?, result=?, error=?, finished_at=? WHERE task_id=?",
            (status, result, error, finished, task_id),
        )
        # Push Alfred notification event
        await db.execute(
            """INSERT INTO alfred_events (task_id, type, payload, created_at, status)
               VALUES (?, 'AIDER_RESULT_NOTIFY', ?, ?, 'result')""",
            (
                task_id,
                json.dumps({"status": status, "result_preview": (result or "")[:300]}),
                finished,
            ),
        )
        await db.commit()

    log.info("TASK_WRITTEN  task_id=%s  status=%s", task_id, status)


async def start_runner():
    """Main loop: poll DB every POLL_INTERVAL seconds, run tasks with concurrency limit."""
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    active: set[asyncio.Task] = set()

    log.info("Aider runner loop started (poll=%ds, max_concurrent=%d)", POLL_INTERVAL, MAX_CONCURRENT)

    while True:
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    """SELECT * FROM tasks WHERE status='queued'
                       ORDER BY priority ASC, created_at ASC LIMIT ?""",
                    (MAX_CONCURRENT,),
                ) as cur:
                    rows = await cur.fetchall()

            for row in rows:
                task = dict(row)
                if any(t.get_name() == task["task_id"] for t in active):
                    continue

                async def _run(t=task):
                    async with semaphore:
                        await run_aider_task(t)

                tsk = asyncio.create_task(_run(), name=task["task_id"])
                active.add(tsk)
                tsk.add_done_callback(active.discard)

        except asyncio.CancelledError:
            log.info("Aider runner cancelled, waiting for active tasks…")
            if active:
                await asyncio.gather(*active, return_exceptions=True)
            return
        except Exception as exc:
            log.error("Runner loop error: %s", exc)

        await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)-8s  %(message)s")
    asyncio.run(start_runner())
