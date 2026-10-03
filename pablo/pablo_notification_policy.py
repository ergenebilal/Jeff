"""Node approval cards: one financial decision, never routine approval spam."""
import time
from pablo_approval_maintenance import connect

def reserve(path,approval_id,action,now=None):
    if action not in ('payment','checkout','buy','transfer_money'):return False
    now=time.time() if now is None else now
    with connect(path) as db:
        db.execute('CREATE TABLE IF NOT EXISTS approval_notifications (approval_id TEXT PRIMARY KEY,status TEXT,updated_at REAL)')
        row=db.execute("SELECT status,expires,consumed FROM requests WHERE approval=?",(approval_id,)).fetchone()
        if not row or row[0]!='APPROVAL_REQUIRED' or row[1]<=now or row[2]:return False
        return db.execute("INSERT OR IGNORE INTO approval_notifications VALUES(?,'sending',?)",(approval_id,now)).rowcount==1

def finish(path,approval_id,accepted):
    with connect(path) as db:db.execute('UPDATE approval_notifications SET status=?,updated_at=? WHERE approval_id=?',('sent' if accepted else 'delivery_unknown',time.time(),approval_id))
