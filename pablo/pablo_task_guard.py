"""Durable, single-use action boundary shared by REST, bridge and Telegram."""
import hashlib
import ipaddress
import json
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager


def fingerprint(action, params):
    return hashlib.sha256(json.dumps([action, params], sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def allowed_ip(address, allowlist):
    try:
        ip = ipaddress.ip_address(address)
        return ip.is_loopback or any(ip == ipaddress.ip_address(x) for x in allowlist)
    except ValueError:
        return False


READ_ACTIONS = {'ping', 'window_list', 'gui_coords', 'screenshot', 'vision_grounding', 'browser_read', 'pilot_status'}
GUI_ACTIONS = {'window_focus', 'gui_click', 'gui_drag', 'gui_scroll', 'gui_type', 'screenshot',
               'vision_grounding', 'browser_open', 'browser_read', 'browser_act', 'browser_session',
               'pilot_run_session', 'youtube_play', 'whatsapp_send', 'whatsapp_draft'}


class TaskGuard:
    def __init__(self, path, actions, owner, desktop_ready, clock=time.time, ttl=300):
        self.path, self.actions, self.owner = str(path), actions, str(owner or '')
        self.desktop_ready, self.clock, self.ttl = desktop_ready, clock, ttl
        self.lock = threading.RLock()
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('CREATE TABLE IF NOT EXISTS requests (id TEXT PRIMARY KEY, digest TEXT, action TEXT, params TEXT, status TEXT, response TEXT, approval TEXT, expires REAL, consumed INTEGER DEFAULT 0, approval_notified INTEGER DEFAULT 0)')
            columns = {row[1] for row in db.execute('PRAGMA table_info(requests)')}
            if 'approval_notified' not in columns:
                db.execute('ALTER TABLE requests ADD COLUMN approval_notified INTEGER DEFAULT 0')
            db.execute('CREATE TABLE IF NOT EXISTS outbox (id TEXT PRIMARY KEY, payload TEXT)')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def response(self, rid, status, **kw):
        return dict(request_id=rid, task_id=rid, status=status, ok=status == 'SUCCESS', **kw)

    def store(self, db, rid, result):
        db.execute('UPDATE requests SET status=?, response=? WHERE id=?', (result['status'], json.dumps(result), rid))
        return result

    def get(self, rid):
        with self.connect() as db:
            row = db.execute('SELECT response FROM requests WHERE id=?', (rid,)).fetchone()
            return json.loads(row[0]) if row else self.response(rid, 'NOT_FOUND', error='Unknown request')

    def claim_approval_notification(self, rid):
        """Claim the owner notification once before sending it externally."""
        with self.lock, self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            changed = db.execute(
                "UPDATE requests SET approval_notified=1 WHERE id=? AND status='APPROVAL_REQUIRED' AND approval_notified=0",
                (rid,),
            )
            return changed.rowcount == 1

    def queue_result(self, payload):
        with self.connect() as db:
            db.execute('INSERT OR REPLACE INTO outbox VALUES (?,?)', (payload['task_id'], json.dumps(payload)))

    def flush_results(self, sender):
        with self.connect() as db:
            rows = db.execute('SELECT id,payload FROM outbox').fetchall()
        for rid, raw in rows:
            try:
                sender(json.loads(raw))
            except Exception:
                continue
            with self.connect() as db:
                db.execute('DELETE FROM outbox WHERE id=? AND payload=?', (rid, raw))

    def execute(self, action, params, request_id=None):
        rid = request_id or str(uuid.uuid4())
        if not isinstance(rid, str) or not rid or len(rid) > 128 or not isinstance(params, dict):
            return self.response(str(rid)[:128], 'ERROR', error='Invalid request')
        params = json.loads(json.dumps(params))
        digest = fingerprint(action, params)
        with self.lock, self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT digest,response FROM requests WHERE id=?', (rid,)).fetchone()
            if row:
                if row[0] != digest:
                    return self.response(rid, 'CONFLICT', error='Request ID reused with changed action/params')
                return json.loads(row[1])
            result = self.response(rid, 'IN_PROGRESS')
            db.execute('INSERT INTO requests(id,digest,action,params,status,response) VALUES(?,?,?,?,?,?)',
                       (rid, digest, action, json.dumps(params), result['status'], json.dumps(result)))
            if action not in self.actions:
                return self.store(db, rid, self.response(rid, 'ERROR', error='Unknown action'))
            # Shell and arbitrary GUI inputs can publish, delete or spend indirectly.
            # They therefore require approval of this exact immutable request.
            if action not in READ_ACTIONS:
                aid = str(uuid.uuid4())
                result = self.response(rid, 'APPROVAL_REQUIRED', approval_id=aid, error='Owner approval required')
                db.execute('UPDATE requests SET approval=?,expires=? WHERE id=?', (aid, self.clock() + self.ttl, rid))
                return self.store(db, rid, result)
            db.commit()  # Persist claim BEFORE executing anything.
        return self._run(rid, action, params)

    def approve(self, approval_id, user_id, chat_id, reject=False):
        with self.lock, self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT id,action,params,digest,expires,consumed,status FROM requests WHERE approval=?', (approval_id,)).fetchone()
            if not row:
                return self.response('', 'REJECTED', error='Unknown approval')
            rid, action, raw, digest, expires, consumed, status = row
            if not self.owner or str(user_id) != self.owner or str(chat_id) != self.owner:
                return self.response(rid, 'REJECTED', error='Wrong approver or chat')
            if consumed or status != 'APPROVAL_REQUIRED':
                return self.response(rid, 'REJECTED', error='Approval already consumed')
            params = json.loads(raw)
            if self.clock() > expires or fingerprint(action, params) != digest or reject:
                db.execute('UPDATE requests SET consumed=1 WHERE id=?', (rid,))
                return self.store(db, rid, self.response(rid, 'REJECTED', error='Expired, changed or rejected approval'))
            db.execute('UPDATE requests SET consumed=1 WHERE id=?', (rid,))
            self.store(db, rid, self.response(rid, 'IN_PROGRESS'))
            db.commit()
        return self._run(rid, action, params)

    def _run(self, rid, action, params):
        # One desktop action at a time; repeat the desktop check at execution time.
        with self.lock:
            try:
                if action in GUI_ACTIONS and not self.desktop_ready():
                    result = self.response(rid, 'BLOCKED', error='Desktop locked, active or unavailable')
                else:
                    raw = self.actions[action](params)
                    if not isinstance(raw, dict):
                        raw = dict(ok=False, error='Invalid action response')
                    inner = raw.get('result') if isinstance(raw.get('result'), dict) else {}
                    ok = raw.get('ok') is True and inner.get('ok', True) is not False and inner.get('exit_code', 0) == 0
                    result = self.response(rid, 'SUCCESS' if ok else 'ERROR', result=raw.get('result'),
                                           error=None if ok else raw.get('error', 'Action failed'))
            except Exception as exc:
                result = self.response(rid, 'ERROR', error=type(exc).__name__)
            with self.connect() as db:
                return self.store(db, rid, result)
