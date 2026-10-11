"""Private first-dispatch byte receipts; no execution or approval evidence.

The runtime store is fixed. Explicit store injection is for trusted local tests,
never a tool or model argument. Readers never create a store or run stage imports.
"""
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import stat
import time

DEFAULT_STORE = Path.home() / '.hermes' / 'runtime' / 'original_plan_receipts.sqlite3'
MAX_REQUEST_BYTES = 2_100_000
RECEIPT_FIELDS = frozenset({
    'schema_version', 'request_id', 'action', 'input_digest',
    'request_bytes_sha256', 'captured_at', 'criterion_source', 'read_only',
    'semantic_goal_verified', 'owner_approval_verified', 'submission_verified',
})
SOURCE = 'original_dispatch_input'


class ReceiptError(ValueError):
    """A safe closed receipt boundary; exception text has no private input."""


class ReceiptInvalid(ReceiptError):
    pass


class AlreadyCaptured(ReceiptError):
    pass


class ReceiptConflict(ReceiptError):
    pass


class ReceiptUnavailable(ReceiptError):
    pass


def _reject_constant(_value):
    raise ReceiptInvalid('Invalid original dispatch')


def _finite_float(value):
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ReceiptInvalid('Invalid original dispatch')
    return parsed


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ReceiptInvalid('Invalid original dispatch')
        value[key] = item
    return value


def decode_plan_input(data):
    """Strict bounded JSON object parsing; no plan/business validity assertion."""
    try:
        if type(data) is not bytes or not 1 <= len(data) <= MAX_REQUEST_BYTES:
            raise ReceiptInvalid('Invalid original dispatch')
        value = json.loads(data.decode('utf-8'), parse_constant=_reject_constant,
                           object_pairs_hook=_unique_object, parse_float=_finite_float)
        if not isinstance(value, dict):
            raise ReceiptInvalid('Invalid original dispatch')
        return value
    except ReceiptError:
        raise
    except (ValueError, TypeError, RecursionError, UnicodeError):
        raise ReceiptInvalid('Invalid original dispatch') from None


def _bound_request(request_bytes):
    try:
        body = decode_plan_input(request_bytes)
        if (not isinstance(body, dict) or set(body) != {'action', 'params', 'request_id'}
                or body['action'] != 'local_draft_plan'
                or not isinstance(body['params'], dict)
                or not isinstance(body['request_id'], str)
                or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', body['request_id'])):
            raise ReceiptInvalid('Invalid original dispatch')
        # The outer request ID is deliberately not inserted into params.
        digest = hashlib.sha256(json.dumps([body['action'], body['params']],
                                           sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        return body['request_id'], body['action'], digest, hashlib.sha256(request_bytes).hexdigest()
    except ReceiptError:
        raise
    except (OSError, ValueError, TypeError, KeyError, RecursionError, UnicodeError, SyntaxError):
        raise ReceiptInvalid('Invalid original dispatch') from None


def _safe_path(store):
    path = Path(store).absolute()
    for candidate in (path, *path.parents):
        try:
            info = candidate.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ReceiptUnavailable('Original receipt unavailable')
        if candidate == path and not stat.S_ISREG(info.st_mode):
            raise ReceiptUnavailable('Original receipt unavailable')
        if candidate != path and not stat.S_ISDIR(info.st_mode):
            raise ReceiptUnavailable('Original receipt unavailable')
    return path


def _metadata(row):
    rid, action, digest, byte_digest, captured_at, source, version, raw = row
    if (version != 1 or type(version) is not int or source != SOURCE
            or type(captured_at) not in (int, float) or not math.isfinite(captured_at)
            or not 0 < captured_at <= 253402300799
            or _bound_request(raw) != (rid, action, digest, byte_digest)):
        raise ReceiptInvalid('Original receipt invalid')
    return dict(schema_version=1, request_id=rid, action=action,
                input_digest=digest, request_bytes_sha256=byte_digest,
                captured_at=captured_at, criterion_source=SOURCE, read_only=True,
                semantic_goal_verified=False, owner_approval_verified=False,
                submission_verified=False)


_SELECT = ('SELECT request_id,action,input_digest,request_bytes_sha256,captured_at,'
           'criterion_source,schema_version,request_bytes FROM original_plan_receipts '
           'WHERE request_id=?')
_SCHEMA = '''
CREATE TABLE IF NOT EXISTS original_plan_receipts (
    request_id TEXT PRIMARY KEY,
    action TEXT NOT NULL,
    input_digest TEXT NOT NULL,
    request_bytes_sha256 TEXT NOT NULL,
    captured_at REAL NOT NULL,
    criterion_source TEXT NOT NULL,
    schema_version INTEGER NOT NULL,
    request_bytes BLOB NOT NULL
);
CREATE TRIGGER IF NOT EXISTS original_plan_receipts_no_duplicate
BEFORE INSERT ON original_plan_receipts
WHEN EXISTS (SELECT 1 FROM original_plan_receipts WHERE request_id=NEW.request_id)
BEGIN SELECT RAISE(ABORT, 'immutable original receipt'); END;
CREATE TRIGGER IF NOT EXISTS original_plan_receipts_no_update
BEFORE UPDATE ON original_plan_receipts BEGIN
    SELECT RAISE(ABORT, 'immutable original receipt');
END;
CREATE TRIGGER IF NOT EXISTS original_plan_receipts_no_delete
BEFORE DELETE ON original_plan_receipts BEGIN
    SELECT RAISE(ABORT, 'immutable original receipt');
END;
'''


def capture_original(request_bytes, *, store=DEFAULT_STORE, clock=time.time):
    """Durably capture the exact initial HTTP bytes once, before any HTTP call.

    A matching duplicate is AlreadyCaptured, never permission to resubmit. A
    changed body (even a semantically equal differently encoded body) conflicts.
    """
    rid, action, digest, byte_digest = _bound_request(request_bytes)
    connection = None
    try:
        path = _safe_path(store)
        path.parent.mkdir(parents=True, mode=0o700, exist_ok=True)
        _safe_path(path)
        connection = sqlite3.connect(path, timeout=3, isolation_level=None)
        connection.execute('PRAGMA synchronous=FULL')
        connection.execute('PRAGMA journal_mode=DELETE')
        connection.executescript(_SCHEMA)
        if path.exists():
            path.chmod(0o600)
        connection.execute('BEGIN IMMEDIATE')
        existing = connection.execute(_SELECT, (rid,)).fetchone()
        if existing is not None:
            _metadata(existing)
            if (existing[1:4] != (action, digest, byte_digest)
                    or existing[7] != request_bytes):
                raise ReceiptConflict('Original receipt identity conflict')
            raise AlreadyCaptured('Original dispatch already captured; no resubmission')
        captured_at = clock()
        if (type(captured_at) not in (int, float) or not math.isfinite(captured_at)
                or not 0 < captured_at <= 253402300799):
            raise ReceiptInvalid('Original receipt time invalid')
        row = (rid, action, digest, byte_digest, captured_at, SOURCE, 1, request_bytes)
        connection.execute('INSERT INTO original_plan_receipts VALUES (?,?,?,?,?,?,?,?)', row)
        metadata = _metadata(row)
        connection.execute('COMMIT')
        # A separate read verifies the committed receipt before transport.
        if read_original(rid, store=path) != metadata:
            raise ReceiptUnavailable('Original receipt unavailable')
        return metadata
    except ReceiptError:
        raise
    except (OSError, sqlite3.Error, ValueError, TypeError, OverflowError):
        raise ReceiptUnavailable('Original receipt unavailable') from None
    finally:
        if connection is not None:
            connection.close()


def read_original(plan_id, *, store=DEFAULT_STORE):
    """Return validated first-receipt metadata or unknown (None), read-only.

    No private plan content or exception detail leaves this reader. It never
    creates a database or restores missing historical input from task results.
    """
    connection = None
    try:
        if not isinstance(plan_id, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', plan_id):
            return None
        path = _safe_path(store)
        if not path.is_file():
            return None
        connection = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True, timeout=3)
        connection.execute('PRAGMA query_only=ON')
        row = connection.execute(_SELECT, (plan_id,)).fetchone()
        return None if row is None else _metadata(row)
    except (ReceiptError, OSError, sqlite3.Error, ValueError, TypeError, KeyError,
            OverflowError, RecursionError):
        return None
    finally:
        if connection is not None:
            connection.close()