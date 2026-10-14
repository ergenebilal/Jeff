"""Dated exact returned-text observation; never admission or semantic completion.

Only complete bounded UTF-8 reads are supported. The criterion is fixed before
the executor runs, and contains no caller-selected expected result. No IO occurs
at import. This observer does not restrict the existing executor's permissions.
"""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat
import time

READ_ALIASES = frozenset(('read', 'read_file', 'file_read', 'read_file_content'))
MAX_BYTES = 500_000
MAX_LINES = 1_000
PATH_KEYS = ('path', 'file_path', 'target', 'filepath')
PARAM_KEYS = frozenset((*PATH_KEYS, 'url', 'max_bytes', 'max_lines', 'request_id',
                        'require_approval', 'force_approval'))
RESULT_KEYS = frozenset(('path', 'content', 'lines_returned', 'total_lines',
                         'total_bytes', 'truncated'))


class ReadUnknown(ValueError):
    pass


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _identity(info):
    # Windows 3.13 lstat and descriptor fstat can expose different ctime
    # meanings. Compare their common identity, then compare path ctime only
    # with another lstat; do not silently remove the mutation check.
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns)


def _path_identity(info):
    return (*_identity(info), info.st_ctime_ns)


def _parents(path):
    identities = []
    for parent in path.parents:
        info = parent.lstat()
        if (stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode)
                or getattr(info, 'st_file_attributes', 0) & 0x400):
            raise ReadUnknown('redirected_parent')
        identities.append((info.st_dev, info.st_ino, info.st_mode))
    return tuple(identities)


def _snapshot(path, max_bytes, max_lines):
    parents = _parents(path)
    before = path.lstat()
    if (not stat.S_ISREG(before.st_mode) or stat.S_ISLNK(before.st_mode)
            or getattr(before, 'st_file_attributes', 0) & 0x400
            or before.st_size >= max_bytes):
        raise ReadUnknown('not_complete_regular_bounded_file')
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_BINARY', 0)
                         | getattr(os, 'O_NOFOLLOW', 0))
    with os.fdopen(descriptor, 'rb') as stream:
        opened = os.fstat(stream.fileno())
        if _identity(opened) != _identity(before):
            raise ReadUnknown('changed_before_read')
        data = stream.read(max_bytes)
        after = os.fstat(stream.fileno())
    if (_identity(before) != _identity(after)
            or _path_identity(path.lstat()) != _path_identity(before)
            or len(data) != before.st_size or _parents(path) != parents):
        raise ReadUnknown('changed_during_read')
    lines = data.decode('utf-8', errors='strict').splitlines()
    if len(lines) > max_lines:
        raise ReadUnknown('partial_line_range')
    # Match the actual existing executor's newline normalization, separately
    # from the full underlying byte hash. No response content is used here.
    text = '\n'.join(lines).encode('utf-8')
    return (_path_identity(before), parents, _sha(data), _sha(text), len(data),
            len(text), len(lines))


@dataclass(frozen=True)
class ReadCriterion:
    request_id: str
    action: str
    input_digest: str
    path: str
    max_bytes: int
    max_lines: int
    snapshot: tuple
    started_at: float


def bind_read(request_id, action, params):
    """Bind only the initial request and a bounded independent pre-read."""
    try:
        if (action not in READ_ALIASES or not isinstance(params, dict)
                or set(params) - PARAM_KEYS or not isinstance(request_id, str)
                or not request_id or len(request_id) > 128
                or params.get('request_id', request_id) != request_id):
            return None
        values = [params[k] for k in PATH_KEYS if k in params]
        if (not values or any(not isinstance(v, str) or not v for v in values)
                or len(set(values)) != 1):
            return None
        value = values[0]
        if (value != value.strip() or value.startswith(('"', "'", '\\\\', '//'))
                or '\x00' in value or ('url' in params and params['url'] != params.get('target'))):
            return None
        path = Path(value)
        if not path.is_absolute() or '..' in path.parts:
            return None
        if os.name == 'nt' and any(':' in part for part in path.parts[1:]):
            return None
        max_bytes = params.get('max_bytes', MAX_BYTES)
        max_lines = params.get('max_lines', MAX_LINES)
        if (type(max_bytes) is not int or not 1 <= max_bytes <= MAX_BYTES
                or type(max_lines) is not int or not 1 <= max_lines <= MAX_LINES
                or any(type(params[k]) is not bool for k in ('require_approval', 'force_approval') if k in params)):
            return None
        started = time.time()
        digest = _sha(json.dumps([action, params], sort_keys=True, ensure_ascii=False).encode())
        return ReadCriterion(request_id, action, digest, str(path), max_bytes,
                             max_lines, _snapshot(path, max_bytes, max_lines), started)
    except (OSError, ReadUnknown, ValueError, TypeError, UnicodeError):
        return None


def observe_read(criterion, raw):
    """Compare the actual return with an independent post-read, fail closed."""
    out = dict(schema_version=1, status='unknown', scope='bounded_returned_read_window',
               read_only=True, returned_content_verified=False,
               current_file_state_verified=False, semantic_goal_verified=False,
               customer_delivery_verified=False, owner_approval_verified=False,
               submission_verified=False, completion_authority=False,
               execution_authority_granted=False, observed_at=time.time())
    if not isinstance(criterion, ReadCriterion):
        return dict(out, reason='initial_criterion_unavailable')
    out.update(request_id=criterion.request_id, input_digest=criterion.input_digest,
               started_at=criterion.started_at, expected_file_sha256=criterion.snapshot[2],
               expected_returned_text_sha256=criterion.snapshot[3],
               max_bytes=criterion.max_bytes, max_lines=criterion.max_lines)
    if (not isinstance(raw, dict) or raw.get('ok') is not True
            or not isinstance(raw.get('result'), dict)):
        return dict(out, reason='returned_read_unavailable')
    value = raw['result']
    if (set(value) != RESULT_KEYS or not isinstance(value.get('content'), str)
            or value.get('truncated') is not False
            or value.get('path') != criterion.path
            or any(type(value.get(k)) is not int for k in ('lines_returned', 'total_lines', 'total_bytes'))):
        return dict(out, reason='partial_or_unrecognized_return')
    try:
        observed = _snapshot(Path(criterion.path), criterion.max_bytes, criterion.max_lines)
        if observed != criterion.snapshot:
            return dict(out, reason='file_changed_in_observation_window')
        returned = value['content'].encode('utf-8')
        matched = (_sha(returned) == observed[3] and len(returned) == observed[5]
                   and value['lines_returned'] == value['total_lines'] == observed[6]
                   and value['total_bytes'] == observed[4])
        out.update(status='matched' if matched else 'mismatch',
                   returned_content_verified=matched, observed_file_sha256=observed[2],
                   observed_returned_text_sha256=_sha(returned),
                   observed_file_bytes=observed[4], observed_text_bytes=observed[5],
                   observed_lines=observed[6], observed_at=time.time())
        return out
    except (OSError, ReadUnknown, ValueError, TypeError, UnicodeError):
        return dict(out, reason='independent_read_unavailable')
