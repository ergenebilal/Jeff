"""Wake the owner only for an evidenced financial or irreversible-loss decision."""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import time

FINANCIAL_ACTIONS={'payment','checkout','buy','transfer_money'}

def financial_decisions(path,now):
    try:
        with sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True) as db:
            db.row_factory=sqlite3.Row
            tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            # Windows owns its inline financial card. Do not send a second
            # notification for the same canonical decision from the server.
            exclude=" AND approval_id NOT IN (SELECT approval_id FROM approval_source_links WHERE source='journal')" if 'approval_source_links' in tables else ''
            rows=db.execute("SELECT approval_id,action,recipient,expires_at FROM approval_records WHERE status='pending' AND expires_at>?"+exclude,(now,)).fetchall()
        return [{'id':'approval:'+r['approval_id'],'kind':'money_decision','evidence_ref':'approval:'+r['approval_id'],
                 'deadline':r['expires_at'],'message':f"Finansal işlem için karar gerekiyor: {r['action']} → {r['recipient']}\nOnay: {r['approval_id']}\nSon karar zamanı: {time.strftime('%d.%m %H:%M UTC',time.gmtime(r['expires_at']))}"}
                for r in rows if r['action'] in FINANCIAL_ACTIONS]
    except sqlite3.Error:return []

def irreversible_disk_decision(state,now,usage=shutil.disk_usage):
    record=state.get('disk',{})
    if record.get('ok',True) or now-record.get('since',now)<300:return []
    u=usage('/')
    if u.free>=1024**3 or u.used/u.total<.98:return []
    incident=str(record['since'])
    return [{'id':'disk:'+incident,'kind':'critical_decision','evidence_ref':'disk-usage:'+incident,
             'deadline':now+3600,'message':'Diskte 1 GB altında yer kaldı ve doluluk %98 üzerinde. Veri yazımları durabilir. Alan açma veya kapasite artırma kararı gerekiyor.'}]

class AttentionOutbox:
    def __init__(self,path,clock=time.time):
        self.path=str(path);self.clock=clock
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS attention_outbox (id TEXT PRIMARY KEY,evidence_digest TEXT NOT NULL,payload TEXT NOT NULL,status TEXT NOT NULL,created_at REAL,updated_at REAL)')

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=10)
        try:
            with db:db.execute('BEGIN IMMEDIATE');yield db
        finally:db.close()

    def dispatch(self,items,sender):
        sent=0
        for item in items:
            if item.get('kind') not in ('money_decision','critical_decision') or not item.get('evidence_ref') or not item.get('id') or not item.get('message') or item.get('deadline',0)<=self.clock():continue
            payload=json.dumps(item,sort_keys=True);digest=hashlib.sha256(payload.encode()).hexdigest()
            with self.connect() as db:
                # Commit before sending. A crash or ambiguous timeout cannot replay.
                changed=db.execute("INSERT OR IGNORE INTO attention_outbox VALUES(?,?,?,'sending',?,?)",(item['id'],digest,payload,self.clock(),self.clock())).rowcount
            if not changed:continue
            try:accepted=sender(item['message']) is True
            except Exception:accepted=False
            with self.connect() as db:
                db.execute('UPDATE attention_outbox SET status=?,updated_at=? WHERE id=?',('sent' if accepted else 'delivery_unknown',self.clock(),item['id']))
            sent+=int(accepted)
        return sent
