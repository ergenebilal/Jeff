"""Read-only readiness evidence. A live ping alone is never work readiness."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import time


def inspect(root, ping, *, clock=time.time):
    root = Path(root)
    out = {'schema_version': 1, 'observed_at': clock(), 'runtime_ready': False,
           'mode': 'unavailable', 'missing_interval_reconciled': False,
           'checks': {}, 'reason': 'Runtime state unavailable', 'workers_started': False}
    try:
        if root.is_symlink() or not root.is_dir():
            return out
        for name in ('config.json', 'deployment.json', 'task-journal.sqlite3', 'intent_guard.sqlite3'):
            path = root/name
            out['checks'][name] = path.is_file() and not path.is_symlink() and path.stat().st_size > 0
        if not all(out['checks'].values()):
            out['reason'] = 'Required runtime file missing or empty'; return out
        config=json.loads((root/'config.json').read_text(encoding='utf-8'))
        deployment=json.loads((root/'deployment.json').read_text(encoding='utf-8'))
        out['checks']['configuration'] = (isinstance(config,dict) and isinstance(config.get('auth_token'),str)
                                          and bool(config['auth_token']) and config.get('listen_port') == 7788)
        out['checks']['release'] = bool(ping.get('ok') and deployment.get('commit') == ping.get('source_commit'))
        loaded = ping.get('loaded_source_sha256', {})
        out['checks']['running_sources'] = (isinstance(loaded,dict) and len(loaded)>=12 and
            all(isinstance(name,str) and Path(name).name==name and (root/name).is_file()
                and not (root/name).is_symlink()
                and hashlib.sha256((root/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==value
                for name,value in loaded.items()))
        with closing(sqlite3.connect((root/'task-journal.sqlite3').resolve().as_uri()+'?mode=ro',uri=True,timeout=2)) as db:
            db.execute('PRAGMA query_only=ON')
            tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            out['checks']['journal_schema'] = {'requests','outbox','work_events','work_history'}<=tables
            out['checks']['journal_integrity'] = db.execute('PRAGMA quick_check').fetchone()[0]=='ok'
            if 'recovery_boundary' in tables:
                row=db.execute('SELECT mode,snapshot_finished_at FROM recovery_boundary').fetchone()
                out['mode'] = row[0] if row else 'unavailable'
                out['historical_requests_retained'] = db.execute('SELECT count(*) FROM recovery_original_requests').fetchone()[0]
                out['historical_snapshot_finished_at'] = row[1] if row else None
                triggers={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
                out['checks']['recovery_write_lock'] = {'recovery_requests_insert','recovery_requests_update','recovery_requests_delete'}<=triggers
            else:
                out['mode']='normal';out['missing_interval_reconciled']=True
        with closing(sqlite3.connect((root/'intent_guard.sqlite3').resolve().as_uri()+'?mode=ro',uri=True,timeout=2)) as db:
            db.execute('PRAGMA query_only=ON')
            out['checks']['intent_schema'] = bool(db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='intent_leases'").fetchone())
            out['checks']['intent_integrity'] = db.execute('PRAGMA quick_check').fetchone()[0]=='ok'
        out['runtime_ready'] = all(value is True for value in out['checks'].values()) and out['mode'] in ('normal','read_only_recovery')
        out['reason']='Only reading admitted; missing history remains unresolved' if out['mode']=='read_only_recovery' else 'Current runtime checks passed' if out['runtime_ready'] else 'Runtime checks failed'
    except (OSError,ValueError,TypeError,KeyError,sqlite3.Error):
        out['runtime_ready']=False;out['reason']='Runtime evidence unavailable'
    return out
