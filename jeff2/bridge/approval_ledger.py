"""Canonical, immutable, single-use decisions shared by source adapters."""
from contextlib import contextmanager
import hashlib
import json
import sqlite3
import time
import uuid

class ApprovalConflict(Exception):
    pass

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()

class ApprovalLedger:
    def __init__(self,path,clock=time.time):
        self.path=str(path); self.clock=clock

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=10); db.row_factory=sqlite3.Row
        try:
            with db:
                db.execute('BEGIN IMMEDIATE'); yield db
        finally:
            db.close()

    @staticmethod
    def initialize_on(db):
        db.executescript('''
            CREATE TABLE IF NOT EXISTS approval_records (
                approval_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, action TEXT NOT NULL,
                recipient TEXT NOT NULL, channel TEXT NOT NULL, input_digest TEXT NOT NULL,
                binding_digest TEXT NOT NULL, binding_json TEXT NOT NULL,
                status TEXT NOT NULL, created_at REAL NOT NULL, expires_at REAL NOT NULL,
                decided_at REAL, owner_id TEXT, claim_id TEXT, claimed_by TEXT,
                consumed_at REAL, archived_at REAL);
            CREATE TABLE IF NOT EXISTS approval_source_links (
                source TEXT NOT NULL, source_id TEXT NOT NULL, binding_digest TEXT NOT NULL,
                approval_id TEXT NOT NULL, PRIMARY KEY(source,source_id,binding_digest));
            CREATE TABLE IF NOT EXISTS approval_audit (
                event_id TEXT PRIMARY KEY, approval_id TEXT NOT NULL, event TEXT NOT NULL,
                actor TEXT NOT NULL, timestamp REAL NOT NULL, details TEXT NOT NULL);
            CREATE TRIGGER IF NOT EXISTS approval_binding_immutable BEFORE UPDATE OF
                task_id,action,recipient,channel,input_digest,binding_digest,binding_json,created_at,expires_at
                ON approval_records BEGIN SELECT RAISE(ABORT,'approval binding is immutable'); END;
            CREATE TRIGGER IF NOT EXISTS approval_audit_no_update BEFORE UPDATE ON approval_audit
                BEGIN SELECT RAISE(ABORT,'approval audit is append-only'); END;
            CREATE TRIGGER IF NOT EXISTS approval_audit_no_delete BEFORE DELETE ON approval_audit
                BEGIN SELECT RAISE(ABORT,'approval audit is append-only'); END;
        ''')

    def initialize(self):
        with self.connect() as db: self.initialize_on(db)

    def _event(self,db,aid,event,actor,details=None):
        db.execute('INSERT INTO approval_audit VALUES(?,?,?,?,?,?)',
                   (uuid.uuid4().hex,aid,event,str(actor),self.clock(),json.dumps(details or {})))

    def _row(self,db,aid):
        row=db.execute('SELECT * FROM approval_records WHERE approval_id=?',(aid,)).fetchone()
        if row is None: raise ApprovalConflict('Unknown canonical approval')
        return row

    def request_on(self,db,source,source_id,binding,expires_at,created_at=None,approval_id=None):
        for key in ('task_id','action','recipient','channel','input_digest'):
            if not isinstance(binding.get(key),str) or not binding[key].strip():
                raise ApprovalConflict('Incomplete immutable binding: '+key)
        if len(binding['input_digest'])!=64 or any(c not in '0123456789abcdef' for c in binding['input_digest']):
            raise ApprovalConflict('Invalid input digest')
        now=self.clock(); created=now if created_at is None else float(created_at)
        binding_hash=digest(binding)
        link=db.execute('SELECT approval_id FROM approval_source_links WHERE source=? AND source_id=? AND binding_digest=?',
                        (source,str(source_id),binding_hash)).fetchone()
        if link: return dict(self._row(db,link[0]))
        if not source or not source_id or created>now or expires_at<=created or expires_at-created>172800:
            raise ApprovalConflict('Invalid approval lifetime or source')
        # A changed source context invalidates old authority before creating a new decision.
        old=db.execute('SELECT r.* FROM approval_records r JOIN approval_source_links l USING(approval_id) '
                       'WHERE l.source=? AND l.source_id=?',(source,str(source_id))).fetchall()
        for row in old:
            if row['status'] in ('pending','approved'):
                db.execute("UPDATE approval_records SET status='revoked',archived_at=? WHERE approval_id=?",(now,row['approval_id']))
                self._event(db,row['approval_id'],'revoked','context-change')
        # Merge only the same explicit operation and complete binding, never title similarity.
        existing=db.execute("SELECT approval_id FROM approval_records WHERE task_id=? AND binding_digest=? "
                            "AND status IN ('pending','approved','claimed','consumed') ORDER BY rowid DESC LIMIT 1",
                            (binding['task_id'],binding_hash)).fetchone()
        aid=existing[0] if existing else approval_id or uuid.uuid4().hex
        if not existing:
            status='expired' if expires_at<=now else 'pending'
            db.execute('INSERT INTO approval_records VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)',
                       (aid,binding['task_id'],binding['action'],binding['recipient'],binding['channel'],binding['input_digest'],
                        binding_hash,json.dumps(binding,ensure_ascii=False,sort_keys=True),status,created,float(expires_at),
                        None,None,None,None,None,now if status=='expired' else None))
            self._event(db,aid,'requested' if status=='pending' else 'imported_expired',source)
        db.execute('INSERT INTO approval_source_links VALUES(?,?,?,?)',(source,str(source_id),binding_hash,aid))
        return dict(self._row(db,aid))

    def request(self,source,source_id,binding,expires_at,created_at=None):
        self.expire()
        with self.connect() as db: return self.request_on(db,source,source_id,binding,expires_at,created_at)

    def _expire_on(self,db):
        rows=db.execute("SELECT approval_id FROM approval_records WHERE status IN ('pending','approved') AND expires_at<=?",(self.clock(),)).fetchall()
        for row in rows:
            db.execute("UPDATE approval_records SET status='expired',archived_at=? WHERE approval_id=?",(self.clock(),row[0]))
            self._event(db,row[0],'expired','expiry')
        return len(rows)

    def expire(self):
        with self.connect() as db: return self._expire_on(db)

    def decide_on(self,db,aid,input_digest,owner,approve):
        self._expire_on(db); row=self._row(db,aid)
        if row['input_digest']!=input_digest or row['status']!='pending' or not owner:
            raise ApprovalConflict('Decision expired, consumed, changed or not pending')
        status='approved' if approve else 'rejected'
        db.execute('UPDATE approval_records SET status=?,decided_at=?,owner_id=?,archived_at=? WHERE approval_id=?',
                   (status,self.clock(),str(owner),None if approve else self.clock(),aid))
        self._event(db,aid,status,owner)
        return dict(self._row(db,aid))

    def decide(self,aid,input_digest,owner,approve):
        self.expire()  # Commit expiry even if the attempted decision is refused.
        with self.connect() as db: return self.decide_on(db,aid,input_digest,owner,approve)

    def claim_on(self,db,aid,binding,worker):
        self._expire_on(db); row=self._row(db,aid)
        if row['binding_digest']!=digest(binding) or row['status']!='approved' or not worker:
            raise ApprovalConflict('Approval is not executable or binding changed')
        claim=uuid.uuid4().hex
        db.execute("UPDATE approval_records SET status='claimed',claim_id=?,claimed_by=? WHERE approval_id=?",(claim,worker,aid))
        self._event(db,aid,'claimed',worker)
        return dict(self._row(db,aid))

    def claim(self,aid,binding,worker):
        self.expire()
        with self.connect() as db: return self.claim_on(db,aid,binding,worker)

    def complete_on(self,db,aid,claim_id,worker,outcome):
        row=self._row(db,aid)
        if row['status']!='claimed' or row['claim_id']!=claim_id or row['claimed_by']!=worker:
            raise ApprovalConflict('Claim mismatch or already consumed')
        db.execute("UPDATE approval_records SET status='consumed',consumed_at=?,archived_at=? WHERE approval_id=?",(self.clock(),self.clock(),aid))
        self._event(db,aid,'consumed',worker,{'outcome':outcome})
        return dict(self._row(db,aid))

    def complete(self,aid,claim_id,worker,outcome):
        with self.connect() as db: return self.complete_on(db,aid,claim_id,worker,outcome)

    def revoke(self,aid,actor):
        with self.connect() as db:
            row=self._row(db,aid)
            if row['status'] not in ('pending','approved'): raise ApprovalConflict('Approval cannot be revoked')
            db.execute("UPDATE approval_records SET status='revoked',archived_at=? WHERE approval_id=?",(self.clock(),aid))
            self._event(db,aid,'revoked',actor)

    def get(self,aid):
        self.expire()
        with self.connect() as db: return dict(self._row(db,aid))

    def queue(self):
        self.expire()
        with self.connect() as db:
            return [dict(r) for r in db.execute("SELECT * FROM approval_records WHERE status IN ('pending','approved') AND archived_at IS NULL ORDER BY created_at")]
