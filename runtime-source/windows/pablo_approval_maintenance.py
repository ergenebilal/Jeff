"""Approval-only archival; retains original payloads and records every transition."""
from datetime import datetime,timezone
from contextlib import contextmanager
import json
import sqlite3
import time

@contextmanager
def connect(path):
    db=sqlite3.connect(path)
    try:
        with db:yield db
    finally:db.close()

def initialize(db):
    db.execute('CREATE TABLE IF NOT EXISTS approval_archives (source TEXT,source_id TEXT,archived_at REAL,reason TEXT,original_status TEXT,PRIMARY KEY(source,source_id))')

def journal_decay(db,now):
    initialize(db)
    rows=db.execute("SELECT id,expires,created_at,response FROM requests WHERE status='APPROVAL_REQUIRED' AND consumed=0").fetchall()
    for rid,expires,created,response in rows:
        if expires is not None and expires<=now:status='EXPIRED'
        elif created is None or expires is None:status='NEEDS_REVALIDATION'
        else:continue
        payload=json.loads(response);payload.update(status=status,ok=False,error='Approval archived; no authority remains')
        db.execute('INSERT OR IGNORE INTO approval_archives VALUES(?,?,?,?,?)',('journal',rid,now,status,'APPROVAL_REQUIRED'))
        db.execute('UPDATE requests SET status=?,response=?,consumed=1 WHERE id=?',(status,json.dumps(payload),rid))

def review_link(path,source,source_id,canonical_id,expires_at):
    with connect(path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS canonical_review_links (source TEXT,source_id TEXT,canonical_id TEXT,expires_at REAL,PRIMARY KEY(source,source_id))')
        db.execute('INSERT OR REPLACE INTO canonical_review_links VALUES(?,?,?,?)',(source,str(source_id),canonical_id,expires_at))

def marketing_decay(path,now=None):
    now=time.time() if now is None else now
    with connect(path) as db:
        initialize(db)
        db.execute('CREATE TABLE IF NOT EXISTS canonical_review_links (source TEXT,source_id TEXT,canonical_id TEXT,expires_at REAL,PRIMARY KEY(source,source_id))')
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for source,table in (('marketing_campaign','outreach_campaigns'),('marketing_idea','instagram_content_ideas')):
            if table not in tables:continue
            columns={r[1] for r in db.execute('PRAGMA table_info('+table+')')}
            timestamp='approval_requested_at' if 'approval_requested_at' in columns else 'NULL'
            for rid,requested in db.execute('SELECT id,'+timestamp+' FROM '+table+" WHERE status='PENDING_APPROVAL'").fetchall():
                link=db.execute('SELECT expires_at FROM canonical_review_links WHERE source=? AND source_id=?',(source,str(rid))).fetchone()
                reason=None
                if link:reason='EXPIRED' if link[0]<=now else None
                else:
                    try:
                        created=datetime.fromisoformat(requested).replace(tzinfo=timezone.utc).timestamp()
                        reason='EXPIRED' if created+172800<=now else 'NEEDS_REVALIDATION'
                    except (ValueError,TypeError):reason='NEEDS_REVALIDATION'
                if reason:
                    db.execute('INSERT OR IGNORE INTO approval_archives VALUES(?,?,?,?,?)',(source,str(rid),now,reason,'PENDING_APPROVAL'))
                    db.execute('UPDATE '+table+' SET status=? WHERE id=?',(reason,rid))
