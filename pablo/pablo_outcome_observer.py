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
