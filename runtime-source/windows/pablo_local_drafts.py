"""A bounded local draft and a separate observation of its expected bytes.

No caller-selected path, shell command, customer message or external delivery.
This is a file outcome check, not an operating-system sandbox.
"""
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import uuid

MAX_BYTES = 500_000


class DraftError(ValueError):
    pass


@dataclass(frozen=True)
class ExpectedDraft:
    filename: str
    data: bytes
    sha256: str


def expectation(request_id, params):
    if not isinstance(request_id, str) or not request_id or len(request_id) > 128:
        raise DraftError('Invalid draft request')
    try:
        request_id.encode('utf-8')
    except UnicodeError as exc:
        raise DraftError('Invalid draft request encoding') from exc
    if not isinstance(params, dict) or set(params) - {'name', 'format', 'content', 'request_id', 'deadline_at'}:
        raise DraftError('Unsupported draft parameters')
    deadline = params.get('deadline_at')
    if deadline is not None and (type(deadline) not in (int, float) or not math.isfinite(deadline)
                                 or not 0 < deadline <= 253402300799):
        raise DraftError('Invalid UTC deadline')
    if params.get('request_id', request_id) != request_id:
        raise DraftError('Draft request mismatch')
    name, format_, content = params.get('name', 'draft'), params.get('format', 'txt'), params.get('content')
    if (not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', name)
            or name.upper() in {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(10)), *(f'LPT{i}' for i in range(10))}
            or format_ not in ('txt', 'md', 'json')):
        raise DraftError('Invalid draft name or format')
    if not isinstance(content, str) or not content or len(content) > MAX_BYTES:
        raise DraftError('Invalid draft content')
    try:
        data = content.encode('utf-8')
        if format_ == 'json':
            json.loads(content, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError) as exc:
        raise DraftError('Invalid draft encoding or JSON') from exc
    if len(data) > MAX_BYTES:
        raise DraftError('Draft exceeds byte limit')
    return ExpectedDraft(name + '.' + format_, data, hashlib.sha256(data).hexdigest())


class LocalDraftStore:
    def __init__(self, root):
        self.root = Path(root).absolute()

    @staticmethod
    def is_redirect(info):
        return stat.S_ISLNK(info.st_mode) or bool(getattr(info, 'st_file_attributes', 0) & 0x400)

    def path(self, rid, expected):
        return self.root / hashlib.sha256(rid.encode('utf-8')).hexdigest() / expected.filename

    def _check_parents(self, path):
        for parent in (self.root, path.parent):
            info = parent.lstat()
            if self.is_redirect(info) or not stat.S_ISDIR(info.st_mode):
                raise DraftError('Draft directory is redirected or invalid')
        if path.parent.resolve().parent != self.root.resolve():
            raise DraftError('Draft escaped managed root')

    def observe(self, rid, expected):
        path = self.path(rid, expected)
        self._check_parents(path)
        before = path.lstat()
        if self.is_redirect(before) or not stat.S_ISREG(before.st_mode) or before.st_size > MAX_BYTES:
            raise DraftError('Draft is not a bounded regular file')
        descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_BINARY', 0))
        with os.fdopen(descriptor, 'rb') as file:
            info = os.fstat(file.fileno())
            if ((info.st_dev, info.st_ino) != (before.st_dev, before.st_ino)
                    or not stat.S_ISREG(info.st_mode) or self.is_redirect(info)):
                raise DraftError('Draft changed before observation')
            data = file.read(MAX_BYTES + 1)
            after = os.fstat(file.fileno())
        self._check_parents(path)
        current = path.lstat()
        # On Windows lstat reports creation time as ctime while fstat reports
        # change time. Compare ctime within each API, never across those APIs.
        signature = lambda item: (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns)
        if (len(data) > MAX_BYTES or signature(before) != signature(after)
                or signature(after) != signature(current) or self.is_redirect(current)
                or before.st_ctime_ns != current.st_ctime_ns or info.st_ctime_ns != after.st_ctime_ns):
            raise DraftError('Draft changed during observation')
        return {'observed_sha256': hashlib.sha256(data).hexdigest(), 'observed_bytes': len(data)}

    def write(self, rid, expected):
        path = self.path(rid, expected)
        self.root.mkdir(parents=True, exist_ok=True)
        # Reject redirected root before creating a task directory beneath it.
        root_info = self.root.lstat()
        if self.is_redirect(root_info) or not stat.S_ISDIR(root_info.st_mode):
            raise DraftError('Draft root is redirected or invalid')
        path.parent.mkdir(exist_ok=True)
        self._check_parents(path)
        if path.exists() or path.is_symlink():
            observed = self.observe(rid, expected)
            if observed['observed_sha256'] != expected.sha256 or observed['observed_bytes'] != len(expected.data):
                raise DraftError('Existing draft differs; no overwrite')
            return {'publication': 'existing_matching'}
        temporary = path.parent / ('.' + uuid.uuid4().hex + '.tmp')
        try:
            with temporary.open('xb') as file:
                file.write(expected.data)
                file.flush()
                os.fsync(file.fileno())
            self._check_parents(path)
            try:
                os.link(temporary, path)  # Publish without overwriting another file.
            except FileExistsError:
                return {'publication': 'existing_after_race'}
            return {'publication': 'created'}
        finally:
            temporary.unlink(missing_ok=True)
