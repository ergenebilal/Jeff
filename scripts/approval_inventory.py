"""Read-only approval totals shared by Bridge and operational reports.

The Windows node publishes counts in its authenticated heartbeat. Missing or
stale sources are named explicitly; they must not be interpreted as zero.
"""
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


def read_only(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)


def collect(bridge_db, now=None, stale_hours=48, panel_db=None):
    now = now or datetime.now(timezone.utc)
    cutoff = (now - timedelta(hours=stale_hours)).isoformat()
    totals = {'waiting': 0, 'old': 0, 'stuck': 0, 'expired': 0, 'unavailable': [], 'sources': {}}
    try:
        db = read_only(bridge_db)
    except sqlite3.Error:
        return None
    try:
        tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'task_records' in tables:
            waiting = db.execute("SELECT count(*) FROM task_records WHERE status='waiting_approval'").fetchone()[0]
            old = db.execute("SELECT count(*) FROM task_records WHERE status='waiting_approval' AND updated_at<?", (cutoff,)).fetchone()[0]
            totals['stuck'] = db.execute("SELECT count(*) FROM task_records WHERE status IN ('failed','escalated','reconciling')").fetchone()[0]
            totals['waiting'] += waiting
            totals['old'] += old
            totals['sources']['tasks'] = waiting
        else:
            totals['unavailable'].append('Görev defteri')
        # Only production bridge databases have a node heartbeat table. Unit
        # fixtures and installations without a node can still read their ledger.
        if 'alfred_heartbeat' in tables:
            row = (db.execute('SELECT observed_at,payload FROM node_approval_snapshots WHERE node_id=?', ('pablo',)).fetchone()
                   if 'node_approval_snapshots' in tables else None)
            if row is None or now.timestamp() - row[0] > 180:
                totals['unavailable'].append('Pablo ve pazarlama onayları')
            else:
                snapshot = json.loads(row[1])
                for name, label, prefix in (('journal', 'Pablo onayları', 'journal'), ('marketing', 'Pazarlama onayları', 'marketing')):
                    if not snapshot.get(prefix + '_complete'):
                        totals['unavailable'].append(label)
                        continue
                    count = int(snapshot[prefix + '_waiting'])
                    totals['waiting'] += count
                    totals['sources'][name] = count
                totals['expired'] += int(snapshot.get('journal_expired', 0)) if snapshot.get('journal_complete') else 0
                totals['old'] += int(snapshot.get('marketing_old', 0)) if snapshot.get('marketing_complete') else 0
    except (sqlite3.Error, ValueError, KeyError, TypeError):
        return None
    finally:
        db.close()
    if panel_db is not None:
        try:
            panel = read_only(panel_db)
            try:
                count = panel.execute("SELECT count(*) FROM approvals WHERE status='Bekliyor'").fetchone()[0]
                old = panel.execute("SELECT count(*) FROM approvals WHERE status='Bekliyor' AND created_at<?", (now.timestamp() - stale_hours * 3600,)).fetchone()[0]
                totals['sources']['panel'] = count
                totals['waiting'] += count
                totals['old'] += old
            finally:
                panel.close()
        except sqlite3.Error:
            totals['unavailable'].append('Panel onayları')
    return totals
