"""Read the original stored draft criterion, never expectations from its result.

Called only behind the node's authenticated GET boundary. No journal constructor,
execution, migration, path supplied by callers, or private text in the response.
"""
from contextlib import closing
from pathlib import Path
import re
import sqlite3
from pablo_outcome_observer import strict_object
from pablo_local_drafts import expectation
from pablo_task_guard import fingerprint


def read_criterion(journal, rid):
    if not isinstance(rid, str) or re.fullmatch(r'[A-Za-z0-9_-]{1,128}', rid) is None:
        raise ValueError('Invalid task identity')
    out = dict(schema_version=1, request_id=rid, status='unavailable',
               source='stored_original_request', input_digest=None,
               expected_sha256=None, expected_bytes=None, execution_state='unknown',
               read_only=True, execution_authorized=False, reexecution_authorized=False)
    try:
        with closing(sqlite3.connect(Path(journal).absolute().as_uri()+'?mode=ro',
                                    uri=True, timeout=1)) as db:
            db.execute('PRAGMA query_only=ON')
            row = db.execute('SELECT action,params,digest,status FROM requests WHERE id=?', (rid,)).fetchone()
        if row is None:
            return out
        action, raw, digest, status = row
        if action != 'local_draft':
            out['status'] = 'unsupported'
            return out
        if not isinstance(raw, str) or len(raw) > 2000000:
            return out
        params = strict_object(raw)
        if fingerprint(action, params) != digest:
            return out
        expected = expectation(rid, params)
        out.update(status='available', input_digest=digest, expected_sha256=expected.sha256,
                   expected_bytes=len(expected.data),
                   execution_state='recorded' if status == 'SUCCESS' else 'unknown')
    except (OSError, ValueError, TypeError, sqlite3.Error, RecursionError):
        pass
    return out
