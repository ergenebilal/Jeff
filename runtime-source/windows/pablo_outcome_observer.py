"""Independent current bytes from the existing private draft journal.

The node owns the journal path. Its HTTP handler authenticates and limits the
request before calling this reader. No action execution or journal mutation.
"""
from contextlib import closing
import json
import math
from pathlib import Path
import re
import sqlite3
import time
from pablo_local_drafts import DraftError, LocalDraftStore, expectation
from pablo_task_guard import fingerprint


def strict_object(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError('Duplicate stored key')
            value[key] = item
        return value
    def invalid(_):
        raise ValueError('Nonfinite stored number')
    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    if not isinstance(result, dict):
        raise ValueError('Invalid stored object')
    return result


def snapshot(journal, rid):
    # No constructor, migration, restart note, outbox or journal maintenance.
    with closing(sqlite3.connect(Path(journal).absolute().as_uri() + '?mode=ro', uri=True, timeout=1)) as db:
        db.execute('PRAGMA query_only=ON')
        return db.execute('SELECT action,params,digest,status,observation_after FROM requests WHERE id=?', (rid,)).fetchone()


def observe_current(journal, rid, *, clock=time.time):
    """Accepts an existing node-owned journal path. Returns no private paths/content.

    Outcome is bounded to the observation instant, not future file contents,
    semantic quality, action execution or customer delivery.
    """
    if not isinstance(rid, str) or re.fullmatch(r'[A-Za-z0-9_-]{1,128}', rid) is None:
        raise ValueError('Invalid task identity')
    started = clock()
    if type(started) not in (int, float) or not math.isfinite(started) or started <= 0:
        raise ValueError('Invalid clock')
    out = {'schema_version': 1, 'request_id': rid, 'status': 'unavailable',
           'method': 'independent_current_file_read', 'observed_at': None,
           'input_digest': None, 'expected_sha256': None, 'expected_bytes': None,
           'observed_sha256': None, 'observed_bytes': None,
           'file_bytes_matched_at_observation': False,
           'scope': 'private_draft_bytes_at_this_observation', 'read_only': True,
           'journal_status_updated': False, 'execution_authorized': False,
           'reexecution_authorized': False, 'customer_delivery_verified': False,
           'semantic_quality_verified': False, 'reason': 'Observation unavailable'}
    try:
        row = snapshot(journal, rid)
        if row is None:
            out['reason'] = 'Task not found'; return out
        action, raw, digest, status, after = row
        if action != 'local_draft':
            out.update(status='unsupported', reason='Only an existing private draft is supported'); return out
        if not isinstance(raw, str) or len(raw) > 2000000:
            raise ValueError('Invalid stored input size')
        params = strict_object(raw)
        if not isinstance(digest, str) or re.fullmatch(r'[a-f0-9]{64}', digest) is None or fingerprint(action, params) != digest:
            raise ValueError('Stored binding changed')
        expected = expectation(rid, params)
        out.update(input_digest=digest, expected_sha256=expected.sha256, expected_bytes=len(expected.data))
        if after is not None and (type(after) not in (int, float) or not math.isfinite(after) or after <= 0):
            raise ValueError('Invalid observation window')
        if status == 'IN_PROGRESS' and after is not None and after > started:
            out.update(status='deferred', reason='Writer observation window is still active'); return out
        observed = LocalDraftStore(Path(journal).absolute().parent / 'verified-drafts').observe(rid, expected)
        finished = clock()
        if type(finished) not in (int, float) or not math.isfinite(finished) or finished < started:
            raise ValueError('Clock changed during observation')
        # A second committed snapshot catches changed input while the file was read.
        current = snapshot(journal, rid)
        if current is None or current[:3] != row[:3] or current[3:] != row[3:]:
            raise ValueError('Task changed during observation')
        matched = observed['observed_sha256'] == expected.sha256 and observed['observed_bytes'] == len(expected.data)
        out.update(observed, observed_at=finished, status='matched' if matched else 'mismatch',
                   file_bytes_matched_at_observation=matched,
                   reason='Independent current draft bytes matched' if matched else 'Independent current draft bytes differ')
    except (OSError, ValueError, TypeError, sqlite3.Error, RecursionError):
        # No exception text, file path, params or private contents cross the boundary.
        out.update(status='unavailable', observed_at=None, observed_sha256=None, observed_bytes=None,
                   file_bytes_matched_at_observation=False, reason='Stored binding or independent file observation unavailable')
    return out


# Original-parent-bound current plan observation; no execution or writes.
from pablo_work_plans import PLAN_ACTION, validate_plan, step_id, step_params

def _plan_snapshot(journal, rid):
    with closing(sqlite3.connect(Path(journal).absolute().as_uri()+'?mode=ro', uri=True, timeout=1)) as db:
        db.execute('PRAGMA query_only=ON')
        return db.execute('SELECT action,params,digest,status,parent_id,observation_after FROM requests WHERE id=?',(rid,)).fetchone()


def observe_plan(journal, rid, *, clock=time.time):
    if not isinstance(rid,str) or re.fullmatch(r'[A-Za-z0-9_-]{1,128}',rid) is None:
        raise ValueError('Invalid existing plan identity')
    start=clock()
    if type(start) not in (int,float) or not math.isfinite(start) or start<=0:
        raise ValueError('Invalid observation clock')
    out=dict(schema_version=1,request_id=rid,status='unavailable',
             criterion_source='stored_original_parent_plan',input_digest=None,
             recorded_plan_status='unknown',expected_steps=None,observed_steps=0,
             matched_steps=0,mismatched_steps=0,unavailable_steps=0,deferred_steps=0,
             all_step_bytes_matched_during_read_window=False,observations=[],
             observed_from=None,observed_until=None,atomic_across_files=False,
             semantic_goal_verified=False,execution_verified=False,customer_delivery_verified=False,
             journal_status_updated=False,read_only=True,execution_authorized=False,
             reexecution_authorized=False,reason='Observation unavailable')
    try:
        parent=_plan_snapshot(journal,rid)
        if parent is None:
            return out
        if parent[0]!=PLAN_ACTION:
            out.update(status='unsupported',reason='Only existing bounded private draft plans');return out
        if parent[4] is not None or not isinstance(parent[1],str) or len(parent[1])>2_000_000:
            raise ValueError('Invalid parent')
        plan=validate_plan(rid,strict_object(parent[1]))
        if fingerprint(PLAN_ACTION,plan)!=parent[2]:
            raise ValueError('Parent binding changed')
        out.update(input_digest=parent[2],expected_steps=len(plan['steps']))
        if parent[3] in {'SUCCESS','CANCELLED','IN_PROGRESS','WAITING_FOR_TIME','WAITING_FOR_EVENT','NEEDS_REVIEW','RECOVERY_BLOCKED'}:
            out['recorded_plan_status']=parent[3]
        if parent[3]=='CANCELLED':
            if _plan_snapshot(journal,rid)!=parent:raise ValueError('Parent changed')
            out.update(status='cancelled',reason='Cancelled plan retained; no future step reads or execution');return out
        snapshots={rid:parent}
        for step in plan['steps']:
            sid=step_id(rid,step['name']);row=_plan_snapshot(journal,sid);snapshots[sid]=row
            if row is None:
                out['unavailable_steps']+=1
                continue
            params=step_params(rid,plan,step);expected=expectation(sid,params)
            if (row[0]!='local_draft' or row[4]!=rid or not isinstance(row[1],str)
                    or len(row[1])>2_000_000 or strict_object(row[1])!=params
                    or row[2]!=fingerprint('local_draft',params)):
                raise ValueError('Child binding differs from original parent')
            observed=observe_current(journal,sid,clock=clock)
            if (observed['input_digest']!=row[2]
                    or observed['expected_sha256']!=expected.sha256
                    or observed['expected_bytes']!=len(expected.data)):
                raise ValueError('Child expectation differs from original parent')
            status=observed['status']
            if status=='matched':out['matched_steps']+=1
            elif status=='mismatch':out['mismatched_steps']+=1
            elif status=='deferred':out['deferred_steps']+=1
            else:out['unavailable_steps']+=1
            out['observed_steps']+=1
            out['observations'].append(dict(request_id=sid,status=status,
                observed_at=observed['observed_at'],file_bytes_matched=observed['file_bytes_matched_at_observation']))
        if any(_plan_snapshot(journal,sid)!=row for sid,row in snapshots.items()):
            raise ValueError('Plan changed during observation')
        end=clock()
        if type(end) not in (int,float) or not math.isfinite(end) or end<start:
            raise ValueError('Clock changed')
        matched=out['matched_steps']==len(plan['steps'])
        out.update(status='matched' if matched else ('mismatch' if out['mismatched_steps'] else 'partial'),
                   all_step_bytes_matched_during_read_window=matched,observed_from=start,observed_until=end,
                   reason='Per-step current reads against original parent; no atomic or semantic completion claim')
    except (OSError,ValueError,TypeError,sqlite3.Error,RecursionError):
        out.update(status='unavailable',all_step_bytes_matched_during_read_window=False,
                   observations=[],observed_from=None,observed_until=None,
                   reason='Original plan binding or current observation unavailable')
    return out

