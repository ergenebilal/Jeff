"""Read-only approval totals shared by Bridge and operational reports.

The Windows node publishes counts in its authenticated heartbeat. Missing or
stale sources are named explicitly; they must not be interpreted as zero.
"""
import json
import math
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path


def read_only(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)


def collect(bridge_db, now=None, stale_hours=48, panel_db=None):
    now = now or datetime.now(timezone.utc)
    cutoff = (now - timedelta(hours=stale_hours)).isoformat()
    totals = {'waiting': 0, 'old': 0, 'stuck': 0, 'expired': 0, 'unavailable': [], 'sources': {}}
    legacy_expired=0
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
            if 'task_approvals' in tables:
                totals['expired'] += db.execute(
                    "SELECT count(*) FROM task_approvals a JOIN task_records t ON t.task_id=a.task_id "
                    "WHERE t.approval_id=a.approval_id AND t.status='waiting_approval' "
                    "AND a.expires_at<=? AND a.status IN ('pending','expired')", (now.timestamp(),)).fetchone()[0]
        else:
            totals['unavailable'].append('Görev defteri')
        # Only production bridge databases have a node heartbeat table. Unit
        # fixtures and installations without a node can still read their ledger.
        if 'alfred_heartbeat' in tables:
            row = (db.execute('SELECT observed_at,payload FROM node_approval_snapshots WHERE node_id=?', ('pablo',)).fetchone()
                   if 'node_approval_snapshots' in tables else None)
            if (row is None or type(row[0]) not in (int,float) or not math.isfinite(row[0]) or
                    not 0 <= now.timestamp()-row[0] <= 180):
                totals['unavailable'].append('Pablo ve pazarlama onayları')
            else:
                snapshot = json.loads(row[1])
                if not isinstance(snapshot,dict):
                    raise ValueError('Invalid snapshot')
                for flag in ('journal_complete','marketing_complete'):
                    if type(snapshot.get(flag,False)) is not bool:
                        raise ValueError('Invalid source coverage')
                for counter in ('journal_waiting','journal_expired','marketing_waiting','marketing_old',
                                'journal_legacy_expired','marketing_legacy_expired','notification_delivery_unknown'):
                    value=snapshot.get(counter,0)
                    if type(value) is not int or value < 0:
                        raise ValueError('Invalid source count')
                legacy_expired+=int(snapshot.get('journal_legacy_expired',0))+int(snapshot.get('marketing_legacy_expired',0))
                if snapshot.get('notification_delivery_unknown',0):
                    totals['unavailable'].append('Pablo karar bildirimi: teslim doğrulanamadı')
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
                panel_tables={r[0] for r in panel.execute("SELECT name FROM sqlite_master WHERE type='table'")}
                if 'canonical_approval_links' in panel_tables:
                    legacy_expired+=panel.execute("SELECT count(*) FROM canonical_approval_links WHERE canonical_id IS NULL AND reason='expired'").fetchone()[0]
            finally:
                panel.close()
        except sqlite3.Error:
            totals['unavailable'].append('Panel onayları')
    # Once the canonical ledger exists, source projections are coverage checks,
    # never additional decisions. One approval linked twice is counted once.
    if 'approval_records' in tables:
        try:
            with read_only(bridge_db) as canonical:
                active="status IN ('pending','approved') AND expires_at>?"
                legacy_sources=dict(totals['sources'])
                totals['waiting']=canonical.execute('SELECT count(*) FROM approval_records WHERE '+active,(now.timestamp(),)).fetchone()[0]
                totals['old']=canonical.execute('SELECT count(*) FROM approval_records WHERE '+active+' AND created_at<?',(now.timestamp(),now.timestamp()-stale_hours*3600)).fetchone()[0]
                totals['expired']=legacy_expired+canonical.execute("SELECT count(*) FROM approval_records WHERE status='expired' OR (status IN ('pending','approved') AND expires_at<=?)",(now.timestamp(),)).fetchone()[0]
                totals['sources']={}
                for source,group in (('native','tasks'),('journal','journal'),('marketing_campaign','marketing'),('marketing_idea','marketing'),('panel','panel')):
                    count=canonical.execute('SELECT count(DISTINCT r.approval_id) FROM approval_records r JOIN approval_source_links l USING(approval_id) WHERE l.source=? AND r.'+active,(source,now.timestamp())).fetchone()[0]
                    totals['sources'][group]=totals['sources'].get(group,0)+count
                for source,count in legacy_sources.items():
                    if count>totals['sources'].get(source,0):
                        totals['unavailable'].append(source+': eski kayıtların mutabakatı gerekiyor')
                totals['canonical']=True
        except sqlite3.Error:return None
    return totals
