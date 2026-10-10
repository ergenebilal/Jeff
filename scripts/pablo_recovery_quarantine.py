"""Recover known history in a private copy without granting replay authority."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import time

# None of these actions sends, clicks, types, launches a command or resumes work.
READ_ACTIONS = ('read', 'read_file', 'file_read', 'file_read_content',
                'file_list', 'list_files', 'list_dir', 'dir_list',
                'window_list', 'marketing_list', 'pilot_status', 'ping')


def quarantine(source, destination, snapshot_finished_at, *, now=None):
    source, destination = Path(source), Path(destination)
    if destination.exists() or source.is_symlink() or not source.is_file():
        raise ValueError('Require a private new copy and an existing regular source')
    now = time.time() if now is None else now
    if type(snapshot_finished_at) not in (int, float) or not 0 < snapshot_finished_at <= now:
        raise ValueError('Invalid historical boundary')
    original = hashlib.sha256(source.read_bytes()).hexdigest()
    shutil.copy2(source, destination)
    with closing(sqlite3.connect(destination)) as db, db:
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Invalid history database')
        names = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'requests', 'outbox', 'work_events'} <= names:
            raise ValueError('Unsupported historical schema')
        old_count = db.execute('SELECT count(*) FROM requests').fetchone()[0]
        old_outbox = db.execute('SELECT count(*) FROM outbox').fetchone()[0]
        db.execute('CREATE TABLE recovery_boundary(snapshot_finished_at REAL, recovered_at REAL, original_sha256 TEXT, mode TEXT)')
        db.execute('INSERT INTO recovery_boundary VALUES(?,?,?,?)',
                   (snapshot_finished_at, now, original, 'read_only_recovery'))
        db.execute('CREATE TABLE recovery_original_requests AS SELECT * FROM requests')
        db.execute('CREATE TABLE recovery_original_outbox AS SELECT * FROM outbox')
        for rid, action in db.execute('SELECT id,action FROM recovery_original_requests').fetchall():
            response = {'request_id': rid, 'task_id': rid, 'status': 'RECOVERY_BLOCKED',
                        'ok': False, 'outcome_verified': False, 'completion_authority': False,
                        'history_only': True, 'reexecution_authorized': False,
                        'historical_action': action, 'snapshot_finished_at': snapshot_finished_at,
                        'missing_interval_reconciled': False,
                        'error': 'Historical recovery; later work is unknown. Do not replay.'}
            db.execute("UPDATE requests SET action='recovered_history',status='RECOVERY_BLOCKED',response=? WHERE id=?",
                       (json.dumps(response), rid))
        # Original rows remain separately available to a private, read-only audit.
        db.execute('DELETE FROM outbox')
        quoted = ','.join("'" + name + "'" for name in READ_ACTIONS)
        db.execute(f"""CREATE TRIGGER recovery_requests_insert BEFORE INSERT ON requests
                    WHEN NEW.action NOT IN ({quoted})
                    BEGIN SELECT RAISE(ABORT,'RECOVERY_READ_ONLY'); END""")
        db.execute(f"""CREATE TRIGGER recovery_requests_update BEFORE UPDATE ON requests
                    WHEN EXISTS(SELECT 1 FROM recovery_original_requests WHERE id=OLD.id)
                    OR NEW.action NOT IN ({quoted})
                    BEGIN SELECT RAISE(ABORT,'RECOVERY_HISTORY_IMMUTABLE'); END""")
        db.execute("""CREATE TRIGGER recovery_requests_delete BEFORE DELETE ON requests
                    BEGIN SELECT RAISE(ABORT,'RECOVERY_HISTORY_IMMUTABLE'); END""")
        for table in ('recovery_boundary','recovery_original_requests','recovery_original_outbox'):
            for operation in ('INSERT','UPDATE','DELETE'):
                db.execute(f"CREATE TRIGGER {table}_{operation.lower()} BEFORE {operation} ON {table} BEGIN SELECT RAISE(ABORT,'RECOVERY_EVIDENCE_IMMUTABLE'); END")
    assert hashlib.sha256(source.read_bytes()).hexdigest() == original
    return {'historical_requests_retained': old_count, 'historical_outbox_retained': old_outbox,
            'active_historical_outbox': 0, 'history_currently_verified': False,
            'mode': 'read_only_recovery', 'missing_interval_reconciled': False}


def quarantine_intents(source, destination):
    source, destination = Path(source), Path(destination)
    if destination.exists() or source.is_symlink() or not source.is_file():
        raise ValueError('Require a new private intent copy')
    original = hashlib.sha256(source.read_bytes()).hexdigest()
    shutil.copy2(source, destination)
    with closing(sqlite3.connect(destination)) as db, db:
        if db.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
            raise ValueError('Invalid intent history')
        count = db.execute('SELECT count(*) FROM intent_leases').fetchone()[0]
        db.execute('CREATE TABLE recovery_original_intents AS SELECT * FROM intent_leases')
        db.execute("UPDATE intent_leases SET status='EXPIRED_UNCERTAIN',outcome_verified=0")
        for table in ('intent_leases','recovery_original_intents'):
            for operation in ('INSERT','UPDATE','DELETE'):
                db.execute(f"CREATE TRIGGER recovery_{table}_{operation.lower()} BEFORE {operation} ON {table} BEGIN SELECT RAISE(ABORT,'RECOVERY_READ_ONLY'); END")
    assert hashlib.sha256(source.read_bytes()).hexdigest() == original
    return {'historical_intents_retained': count, 'outcome_verified': False}
