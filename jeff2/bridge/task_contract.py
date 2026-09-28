"""Durable task lifecycle, append-only evidence and independent verification."""
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import sqlite3
import time
import uuid
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class TaskConflict(Exception):
    pass


class InvalidTransition(TaskConflict):
    pass


class TaskNotFound(Exception):
    pass


class TaskCreate(BaseModel):
    task_id: str | None = Field(default=None, min_length=1, max_length=128)
    source: str = Field(min_length=1)
    actor_id: str | None = None
    session_id: str | None = None
    goal: str = Field(min_length=1)
    success_criteria: list[str] = Field(min_length=1)
    risk_level: Literal['low', 'medium', 'high', 'critical']
    side_effect_class: Literal['none', 'local', 'reversible', 'external', 'irreversible']
    approval_required: bool
    input_digest: str | None = None
    assigned_worker: str | None = None
    max_attempts: int = Field(default=3, ge=1, le=10)

    @model_validator(mode='after')
    def check_policy(self):
        if any(not item.strip() for item in self.success_criteria):
            raise ValueError('Success criteria cannot be empty')
        if self.side_effect_class != 'none' and not self.approval_required:
            raise ValueError('Side effects require approval')
        return self


TRANSITIONS = {
    'received': {'planned', 'cancelled'},
    'planned': {'queued', 'cancelled'},
    'queued': {'claimed', 'cancelled'},
    'claimed': {'running', 'reconciling', 'cancelled'},
    'running': {'waiting_approval', 'verifying', 'reconciling', 'failed'},
    'waiting_approval': {'running', 'reconciling', 'cancelled', 'failed'},
    'reconciling': {'claimed', 'verifying', 'escalated', 'cancelled'},
    'verifying': {'verified', 'failed', 'escalated'},
    'verified': set(), 'failed': set(), 'escalated': set(), 'cancelled': set(),
}


def digest(value):
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


class TaskLedger:
    def __init__(self, path, clock=time.time):
        self.path = str(path)
        self.clock = clock

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def initialize(self):
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS task_records (
                    task_id TEXT PRIMARY KEY, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                    source TEXT NOT NULL, actor_id TEXT, session_id TEXT, goal TEXT NOT NULL,
                    success_criteria TEXT NOT NULL, risk_level TEXT NOT NULL,
                    side_effect_class TEXT NOT NULL, approval_required INTEGER NOT NULL,
                    input_digest TEXT NOT NULL, assigned_worker TEXT, attempt INTEGER NOT NULL,
                    max_attempts INTEGER NOT NULL, lease_owner TEXT, lease_expires_at REAL,
                    status TEXT NOT NULL, approval_id TEXT, evidence_refs TEXT NOT NULL,
                    verification_result TEXT, final_result TEXT, failure_reason TEXT, rollback_ref TEXT
                );
                CREATE TABLE IF NOT EXISTS task_events (
                    event_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, event_type TEXT NOT NULL,
                    from_status TEXT, to_status TEXT NOT NULL, actor TEXT NOT NULL,
                    attempt INTEGER NOT NULL, timestamp TEXT NOT NULL,
                    payload_digest TEXT NOT NULL, evidence_ref TEXT
                );
                CREATE INDEX IF NOT EXISTS task_events_by_task ON task_events(task_id, timestamp);
                CREATE TABLE IF NOT EXISTS task_evidence (
                    evidence_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, kind TEXT NOT NULL,
                    producer TEXT NOT NULL, attempt INTEGER NOT NULL, data_json TEXT NOT NULL,
                    data_digest TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS task_rejections (
                    rejection_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, from_status TEXT,
                    requested_status TEXT, actor TEXT NOT NULL, reason TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );
                CREATE TRIGGER IF NOT EXISTS task_events_no_update BEFORE UPDATE ON task_events
                    BEGIN SELECT RAISE(ABORT, 'task events are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS task_events_no_delete BEFORE DELETE ON task_events
                    BEGIN SELECT RAISE(ABORT, 'task events are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS task_evidence_no_update BEFORE UPDATE ON task_evidence
                    BEGIN SELECT RAISE(ABORT, 'task evidence is append-only'); END;
                CREATE TRIGGER IF NOT EXISTS task_evidence_no_delete BEFORE DELETE ON task_evidence
                    BEGIN SELECT RAISE(ABORT, 'task evidence is append-only'); END;
                CREATE TRIGGER IF NOT EXISTS task_rejections_no_update BEFORE UPDATE ON task_rejections
                    BEGIN SELECT RAISE(ABORT, 'task rejections are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS task_rejections_no_delete BEFORE DELETE ON task_rejections
                    BEGIN SELECT RAISE(ABORT, 'task rejections are append-only'); END;
            ''')

    def _timestamp(self):
        return datetime.fromtimestamp(self.clock(), timezone.utc).isoformat()

    def _row(self, db, task_id):
        row = db.execute('SELECT * FROM task_records WHERE task_id=?', (task_id,)).fetchone()
        if row is None:
            raise TaskNotFound(task_id)
        return row

    def _public(self, row):
        result = dict(row)
        result['approval_required'] = bool(result['approval_required'])
        for name in ('success_criteria', 'evidence_refs', 'verification_result', 'final_result'):
            if result[name] is not None:
                result[name] = json.loads(result[name])
        if result['lease_expires_at'] is not None:
            result['lease_expires_at'] = datetime.fromtimestamp(result['lease_expires_at'], timezone.utc).isoformat()
        return result

    def get(self, task_id):
        with self.connect() as db:
            return self._public(self._row(db, task_id))

    def events(self, task_id):
        with self.connect() as db:
            self._row(db, task_id)
            return [dict(row) for row in db.execute(
                'SELECT * FROM task_events WHERE task_id=? ORDER BY rowid', (task_id,))]

    def evidence(self, task_id):
        with self.connect() as db:
            self._row(db, task_id)
            rows = [dict(row) for row in db.execute(
                'SELECT * FROM task_evidence WHERE task_id=? ORDER BY rowid', (task_id,))]
        for row in rows:
            row['data'] = json.loads(row.pop('data_json'))
        return rows

    def rejections(self, task_id):
        with self.connect() as db:
            self._row(db, task_id)
            return [dict(row) for row in db.execute(
                'SELECT * FROM task_rejections WHERE task_id=? ORDER BY rowid', (task_id,))]

    def _event(self, db, task_id, event_type, from_status, to_status, actor, attempt,
               payload=None, evidence_ref=None):
        db.execute('''INSERT INTO task_events VALUES(?,?,?,?,?,?,?,?,?,?)''',
                   (uuid.uuid4().hex, task_id, event_type, from_status, to_status, actor,
                    attempt, self._timestamp(), digest(payload or {}), evidence_ref))

    def _reject(self, db, row, to_status, actor, reason, exception=InvalidTransition):
        db.execute('INSERT INTO task_rejections VALUES(?,?,?,?,?,?,?)',
                   (uuid.uuid4().hex, row['task_id'], row['status'], to_status,
                    actor, reason, self._timestamp()))
        db.commit()
        raise exception(reason)

    def _transition(self, db, row, to_status, actor, changes=None, evidence_ref=None,
                    event_type=None):
        if to_status not in TRANSITIONS[row['status']]:
            self._reject(db, row, to_status, actor, 'Invalid state transition')
        values = dict(changes or {})
        values.update(status=to_status, updated_at=self._timestamp())
        columns = ','.join(f'{column}=?' for column in values)
        db.execute(f'UPDATE task_records SET {columns} WHERE task_id=?',
                   (*values.values(), row['task_id']))
        self._event(db, row['task_id'], event_type or to_status, row['status'], to_status,
                    actor, values.get('attempt', row['attempt']), values, evidence_ref)
        return self._public(self._row(db, row['task_id']))

    def create(self, body: TaskCreate):
        task_id = body.task_id or uuid.uuid4().hex
        immutable = body.model_dump(exclude={'task_id', 'input_digest'})
        input_digest = digest(immutable)
        if body.input_digest is not None and body.input_digest != input_digest:
            raise TaskConflict('Input digest mismatch')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT * FROM task_records WHERE task_id=?', (task_id,)).fetchone()
            if row:
                if row['input_digest'] != input_digest:
                    raise TaskConflict('Task ID reused with changed content')
                return self._public(row)
            for table in ('tasks', 'alfred_events'):
                present = db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                                     (table,)).fetchone()
                if present and db.execute(f'SELECT 1 FROM {table} WHERE task_id=? LIMIT 1',
                                          (task_id,)).fetchone():
                    raise TaskConflict('Task ID already belongs to a legacy task')
            now = self._timestamp()
            db.execute('''INSERT INTO task_records (
                task_id,created_at,updated_at,source,actor_id,session_id,goal,success_criteria,
                risk_level,side_effect_class,approval_required,input_digest,assigned_worker,
                attempt,max_attempts,lease_owner,lease_expires_at,status,approval_id,
                evidence_refs,verification_result,final_result,failure_reason,rollback_ref
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                (task_id, now, now, body.source, body.actor_id, body.session_id, body.goal,
                 json.dumps(body.success_criteria), body.risk_level, body.side_effect_class,
                 int(body.approval_required), input_digest, body.assigned_worker, 0,
                 body.max_attempts, None, None, 'received', None, '[]', None, None, None, None))
            self._event(db, task_id, 'received', None, 'received', body.source, 0, immutable)
            return self._public(self._row(db, task_id))

    def plan(self, task_id, actor):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            return self._transition(db, self._row(db, task_id), 'planned', actor)

    def queue(self, task_id, actor):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            return self._transition(db, self._row(db, task_id), 'queued', actor)

    def claim(self, task_id, worker, lease_seconds=30):
        if not worker or lease_seconds < 1 or lease_seconds > 3600:
            raise TaskConflict('Invalid worker or lease')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = self._row(db, task_id)
            if row['status'] in ('claimed', 'running', 'waiting_approval'):
                if row['lease_expires_at'] is None or row['lease_expires_at'] > self.clock():
                    self._reject(db, row, 'claimed', worker, 'Active lease exists', TaskConflict)
                self._transition(db, row, 'reconciling', 'lease-reconciler',
                                 {'lease_owner': None, 'lease_expires_at': None})
                row = self._row(db, task_id)
                if row['side_effect_class'] != 'none':
                    db.commit()
                    raise TaskConflict('Side effect requires reconciliation before retry')
            if row['status'] not in ('queued', 'reconciling'):
                self._reject(db, row, 'claimed', worker, 'Task is not claimable', TaskConflict)
            if row['status'] == 'reconciling' and row['side_effect_class'] != 'none':
                self._reject(db, row, 'claimed', worker, 'Side effect cannot auto-retry', TaskConflict)
            if row['assigned_worker'] and row['assigned_worker'] != worker:
                self._reject(db, row, 'claimed', worker, 'Wrong assigned worker', TaskConflict)
            if row['attempt'] >= row['max_attempts']:
                self._reject(db, row, 'claimed', worker, 'Maximum attempts reached', TaskConflict)
            return self._transition(db, row, 'claimed', worker,
                {'attempt': row['attempt'] + 1, 'lease_owner': worker,
                 'lease_expires_at': self.clock() + lease_seconds})

    def _require_lease(self, db, row, worker, target):
        if row['lease_owner'] != worker or row['lease_expires_at'] is None or row['lease_expires_at'] <= self.clock():
            self._reject(db, row, target, worker, 'Worker lease is invalid or expired', TaskConflict)

    def start(self, task_id, worker):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = self._row(db, task_id)
            self._require_lease(db, row, worker, 'running')
            return self._transition(db, row, 'running', worker)

    def finish(self, task_id, worker, execution):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = self._row(db, task_id)
            self._require_lease(db, row, worker, 'verifying')
            if row['status'] != 'running':
                self._reject(db, row, 'verifying', worker, 'Task is not running')
            if not isinstance(execution, dict) or execution.get('request_id') != task_id:
                self._reject(db, row, 'verifying', worker, 'Execution evidence is not bound to task', TaskConflict)
            if execution.get('status') == 'APPROVAL_REQUIRED' and not execution.get('approval_id'):
                self._reject(db, row, 'waiting_approval', worker,
                             'Approval evidence has no approval ID', TaskConflict)
            evidence_id = uuid.uuid4().hex
            db.execute('INSERT INTO task_evidence VALUES(?,?,?,?,?,?,?,?)',
                       (evidence_id, task_id, 'execution', worker, row['attempt'],
                        json.dumps(execution), digest(execution), self._timestamp()))
            refs = json.loads(row['evidence_refs']) + [evidence_id]
            if execution.get('status') == 'APPROVAL_REQUIRED':
                return self._transition(db, row, 'waiting_approval', worker,
                                        {'evidence_refs': json.dumps(refs),
                                         'approval_id': execution['approval_id']},
                                        evidence_ref=evidence_id)
            return self._transition(db, row, 'verifying', worker,
                                    {'evidence_refs': json.dumps(refs),
                                     'lease_owner': None, 'lease_expires_at': None},
                                    evidence_ref=evidence_id)

    def verify(self, task_id, health_probe):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = self._row(db, task_id)
            if row['status'] != 'verifying':
                self._reject(db, row, 'verified', 'verifier', 'Task is not ready for verification')
            execution_row = db.execute('''SELECT * FROM task_evidence WHERE task_id=? AND kind='execution'
                                          ORDER BY rowid DESC LIMIT 1''', (task_id,)).fetchone()
            execution = json.loads(execution_row['data_json']) if execution_row else {}
            execution_ok = bool(execution_row and execution_row['attempt'] == row['attempt']
                                and execution.get('request_id') == task_id
                                and execution.get('status') == 'SUCCESS')
            try:
                observation = health_probe()
            except Exception:
                observation = {'status_code': 0, 'status': 'unavailable'}
            if not isinstance(observation, dict):
                observation = {'status_code': 0, 'status': 'invalid'}
            outcome_ok = observation.get('status_code') == 200 and observation.get('status') == 'ok'
            criteria = {name: bool(outcome_ok) if name == 'pablo_health_ok' else False
                        for name in json.loads(row['success_criteria'])}
            outcome_id = uuid.uuid4().hex
            db.execute('INSERT INTO task_evidence VALUES(?,?,?,?,?,?,?,?)',
                       (outcome_id, task_id, 'outcome', 'verifier', row['attempt'],
                        json.dumps(observation), digest(observation), self._timestamp()))
            refs = json.loads(row['evidence_refs']) + [outcome_id]
            passed = (execution_ok and outcome_ok and all(criteria.values())
                      and row['side_effect_class'] == 'none')
            verification = {'execution_ok': execution_ok, 'outcome_ok': outcome_ok,
                            'criteria': criteria, 'execution_ref': execution_row['evidence_id'] if execution_row else None,
                            'outcome_ref': outcome_id}
            changes = {'evidence_refs': json.dumps(refs),
                       'verification_result': json.dumps(verification),
                       'final_result': json.dumps({'verified': True}) if passed else None,
                       'failure_reason': None if passed else 'Independent verification failed'}
            return self._transition(db, row, 'verified' if passed else 'failed',
                                    'verifier', changes, evidence_ref=outcome_id)

    def cancel(self, task_id, actor):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = self._row(db, task_id)
            if row['status'] in ('running', 'waiting_approval', 'reconciling') and row['side_effect_class'] != 'none':
                self._reject(db, row, 'cancelled', actor, 'Possible side effect requires outcome review')
            return self._transition(db, row, 'cancelled', actor,
                                    {'lease_owner': None, 'lease_expires_at': None})

    def reconcile(self, task_id, actor):
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = self._row(db, task_id)
            if row['status'] == 'reconciling':
                return self._public(row)
            if row['status'] not in ('claimed', 'running', 'waiting_approval'):
                self._reject(db, row, 'reconciling', actor, 'Task has no active lease')
            if row['lease_expires_at'] is None or row['lease_expires_at'] > self.clock():
                self._reject(db, row, 'reconciling', actor, 'Lease has not expired')
            return self._transition(db, row, 'reconciling', actor,
                                    {'lease_owner': None, 'lease_expires_at': None})

    def escalate(self, task_id, actor, reason):
        if not reason.strip():
            raise TaskConflict('Escalation reason required')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = self._row(db, task_id)
            return self._transition(db, row, 'escalated', actor,
                                    {'failure_reason': reason, 'lease_owner': None,
                                     'lease_expires_at': None})
