"""Managed internal drafts, independent file observations and restart-safe work.

No arbitrary path, shell, network request or customer delivery is supported.
"""
import asyncio
import hashlib
import os
import logging
from pathlib import Path
import stat
import uuid

from task_contract import TaskConflict, TaskLedger

WORKER = 'jeff-server'
log = logging.getLogger(__name__)


class ArtifactStore:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)

    def path(self, task_id, step):
        directory = self.root / hashlib.sha256(task_id.encode()).hexdigest()
        directory.mkdir(mode=0o700, exist_ok=True)
        path = directory / (step['name'] + '.' + step['format'])
        if path.resolve().parent != directory or directory.resolve().parent != self.root:
            raise TaskConflict('Artifact path escapes managed root')
        return path

    def read(self, task_id, step):
        path = self.path(task_id, step)
        # Refuse symlinks even when they resolve inside the managed root.
        if path.is_symlink():
            raise TaskConflict('Artifact is a symlink')
        info = path.stat()
        if not stat.S_ISREG(info.st_mode) or info.st_size > 2_000_000:
            raise TaskConflict('Artifact is not a bounded regular file')
        data = path.read_bytes()
        if len(data) > 2_000_000:
            raise TaskConflict('Artifact exceeds read limit')
        return data

    def observe_step(self, task_id, step):
        data = self.read(task_id, step)
        return {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}

    def observe(self, task):
        try:
            artifacts = {step['name']: self.observe_step(task['task_id'], step) for step in task['steps']}
        except (OSError, TaskConflict):
            return {'task_id': task['task_id'], 'status': 'unavailable', 'artifacts': {}}
        return {'task_id': task['task_id'], 'status': 'ok', 'artifacts': artifacts}

    def write(self, task_id, step):
        path = self.path(task_id, step)
        content = step['content'].encode('utf-8')
        expected = hashlib.sha256(content).hexdigest()
        if path.exists() or path.is_symlink():
            observed = self.observe_step(task_id, step)
            if observed['sha256'] != expected:
                raise TaskConflict('Existing artifact differs; reconciliation required')
            return observed  # Crash after write: reconcile the file, never rewrite it.
        temporary = path.with_name('.' + uuid.uuid4().hex + '.tmp')
        try:
            with temporary.open('xb') as file:
                os.chmod(temporary, 0o600)
                file.write(content)
                file.flush()
                os.fsync(file.fileno())
            try:
                os.link(temporary, path)  # Atomic publication without overwrite.
                if os.name == 'posix':
                    descriptor = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
                    try:
                        os.fsync(descriptor)
                    finally:
                        os.close(descriptor)
            except FileExistsError:
                pass
        finally:
            temporary.unlink(missing_ok=True)
        observed = self.observe_step(task_id, step)
        if observed['sha256'] != expected:
            raise TaskConflict('Published artifact differs')
        return observed


class DraftWorker:
    def __init__(self, ledger, artifacts):
        self.ledger, self.artifacts = ledger, artifacts

    def run_task(self, task_id):
        task = self.ledger.get(task_id)
        if task['status'] == 'verifying':
            return self.ledger.verify(task_id, lambda: {}, self.artifacts.observe)
        if task['approval_required']:
            approvals = {a['approval_id']: a for a in self.ledger.approvals()}
            approval = approvals.get(task['approval_id'])
            if (task['status'] == 'waiting_approval'
                    or (task['status'] == 'queued' and (not approval or approval['expires_at'] <= self.ledger.clock()))):
                self.ledger.request_approval(task_id)
                return self.ledger.get(task_id)
        task = self.ledger.claim(task_id, WORKER, lease_seconds=120)
        self.ledger.start(task_id, WORKER)
        try:
            for step in task['steps']:
                observation = self.artifacts.write(task_id, step)
                self.ledger.checkpoint(task_id, WORKER, step['name'], observation)
        except (OSError, TaskConflict) as exc:
            self.ledger.finish(task_id, WORKER, {'request_id': task_id, 'status': 'ERROR', 'error': type(exc).__name__})
            return self.ledger.escalate(task_id, WORKER, 'Artifact outcome needs review')
        self.ledger.finish(task_id, WORKER, {'request_id': task_id, 'status': 'SUCCESS'})
        return self.ledger.verify(task_id, lambda: {}, self.artifacts.observe)

    def run_once(self):
        results = []
        for task in self.ledger.runnable_drafts():
            if task['assigned_worker'] != WORKER or not task['steps']:
                continue
            if task['status'] in ('queued', 'verifying', 'reconciling', 'claimed', 'running'):
                if task['status'] in ('claimed', 'running'):
                    # An existing process may still own the lease.
                    from datetime import datetime
                    lease = datetime.fromisoformat(task['lease_expires_at']).timestamp() if task['lease_expires_at'] else 0
                    if lease > self.ledger.clock():
                        continue
                try:
                    results.append(self.run_task(task['task_id']))
                except TaskConflict:
                    current = self.ledger.get(task['task_id'])
                    if current['attempt'] >= current['max_attempts'] and current['status'] == 'reconciling':
                        self.ledger.escalate(task['task_id'], WORKER, 'Maximum recovery attempts reached')
                    continue
        return results


async def run_draft_worker(db_path, root):
    worker = DraftWorker(TaskLedger(db_path), ArtifactStore(root))
    while True:
        try:
            await asyncio.to_thread(worker.run_once)
        except Exception as exc:
            # Never log plan contents or secrets. Retry a transient DB failure;
            # an expired lease will be reconciled rather than blindly replayed.
            log.error('Draft worker iteration failed: %s', type(exc).__name__)
        await asyncio.sleep(2)
