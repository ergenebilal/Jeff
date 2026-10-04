"""Observe existing Hermes hooks. No route, prompt, retry or tool changes."""
from contextlib import closing
import json
import logging
from pathlib import Path
import sqlite3
import time
import uuid
from urllib.parse import urlsplit

log = logging.getLogger(__name__)

class ReceiptStore:
    def __init__(self, path, clock=time.time):
        self.path = Path(path)
        self.clock = clock

    def connect(self):
        db=sqlite3.connect(str(self.path),timeout=2)
        try:
            db.row_factory=sqlite3.Row
            db.execute('''CREATE TABLE IF NOT EXISTS model_route_receipts (
                receipt_id TEXT PRIMARY KEY, call_id TEXT NOT NULL, session_id TEXT NOT NULL,
                turn_id TEXT NOT NULL, task_id TEXT, attempt INTEGER NOT NULL,
                requested_route TEXT NOT NULL, actual_route TEXT NOT NULL, model TEXT,
                endpoint_host TEXT, status TEXT NOT NULL, fallback_used INTEGER NOT NULL,
                fallback_reason TEXT, error_type TEXT, started_at REAL NOT NULL, ended_at REAL,
                UNIQUE(session_id,turn_id,call_id,attempt))''')
        except Exception:
            db.close()
            raise
        return db

    def pre(self, data):
        identity=tuple(str(data.get(k) or '') for k in ('session_id','turn_id','api_request_id'))
        if not all(identity):
            raise ValueError('Model receipt requires session, turn and request identity')
        actual=str(data.get('provider') or 'unknown')
        with closing(self.connect()) as db, db:
            db.execute('BEGIN IMMEDIATE')
            previous=db.execute('SELECT * FROM model_route_receipts WHERE session_id=? AND turn_id=? AND call_id=? ORDER BY attempt DESC LIMIT 1',identity).fetchone()
            first=db.execute('SELECT actual_route FROM model_route_receipts WHERE session_id=? AND turn_id=? ORDER BY rowid LIMIT 1',identity[:2]).fetchone()
            requested=first[0] if first else actual
            switched=bool(previous and previous['status']=='failed' and
                          (previous['actual_route']!=actual or previous['model']!=str(data.get('model') or '')))
            fallback=switched or bool(previous and previous['fallback_used'])
            reason=previous['error_type'] if switched else previous['fallback_reason'] if previous else None
            if previous and previous['status']=='running':
                db.execute("UPDATE model_route_receipts SET status='unknown',ended_at=? WHERE receipt_id=?",(self.clock(),previous['receipt_id']))
            db.execute('INSERT INTO model_route_receipts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                       (uuid.uuid4().hex,identity[2],identity[0],identity[1],str(data.get('task_id') or ''),
                        previous['attempt']+1 if previous else 1,requested,actual,str(data.get('model') or ''),
                        urlsplit(str(data.get('base_url') or '')).hostname,'running',int(fallback),reason,None,self.clock(),None))
            db.commit()

    def finish(self,data,status):
        identity=tuple(str(data.get(k) or '') for k in ('session_id','turn_id','api_request_id'))
        with closing(self.connect()) as db, db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM model_route_receipts WHERE session_id=? AND turn_id=? AND call_id=? ORDER BY attempt DESC LIMIT 1',identity).fetchone()
            if row is None or row['actual_route']!=str(data.get('provider') or 'unknown'):
                raise ValueError('No matching physical attempt')
            error=data.get('error') or {}
            # Persist a category only, never the exception text or request/response bodies.
            category=str(data.get('reason') or error.get('type') or 'unknown_error')[:80] if status=='failed' else None
            db.execute('UPDATE model_route_receipts SET status=?,error_type=?,ended_at=? WHERE receipt_id=?',
                       (status,category,self.clock(),row['receipt_id']))
            db.commit()

def _store():
    from hermes_constants import get_hermes_home
    return ReceiptStore(Path(get_hermes_home())/'state.db')

def _observe(kind,data):
    try:
        store=_store()
        if kind=='pre':
            store.pre(data)
        else:
            store.finish(data,kind)
    except Exception as exc:
        # Observability cannot retry or disrupt the model request.
        log.warning('Model route receipt unavailable: %s',type(exc).__name__)
        try:
            marker=store.path.parent/'model-route-receipt-error.json'
            marker.write_text(json.dumps({'status':'unknown','observed_at':time.time(),'error_type':type(exc).__name__}))
        except Exception:
            pass

def pre(**data):
    _observe('pre',data)

def post(**data):
    valid=bool(data.get('assistant_content_chars') or data.get('assistant_tool_call_count'))
    _observe('succeeded' if valid and data.get('finish_reason') not in ('error','error_finish') else 'unknown',data)

def error(**data):
    _observe('failed',data)

def register(ctx):
    ctx.register_hook('pre_api_request',pre)
    ctx.register_hook('post_api_request',post)
    ctx.register_hook('api_request_error',error)
