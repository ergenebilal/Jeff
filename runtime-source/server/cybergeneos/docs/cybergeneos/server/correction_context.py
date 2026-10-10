"""Ephemeral authenticated selection -> literal Turkish correction -> P66 proposal.

Not production installed. Selection is an explicit authenticated owner workflow
event, not an inferred task/source relationship or a model-selected first result.
Transport must pass authenticated channel metadata; payload cannot assert it.
No automatic language intent classifier, execution, or permanent memory writes.
"""
from copy import deepcopy
import math
import secrets
import threading
import time

from .owner_lesson import base, binding, owner_text, propose_owner_lesson, source_record, strict_object


def literal_text(raw):
    if not isinstance(raw, str) or len(raw) > 250000:
        raise ValueError()
    if raw.lstrip().startswith(('{', '[')):
        wrapper = strict_object(raw)
        if set(wrapper) != {'trusted_user_request', 'untrusted_panel_data'}:
            raise ValueError()
        data = wrapper['untrusted_panel_data']
        if isinstance(data, str):
            data = strict_object(data)
        if not isinstance(data, dict):
            raise ValueError()
        raw = wrapper['trusted_user_request']
    if not isinstance(raw, str):
        raise ValueError()
    text = raw.strip()
    if not 1 <= len(text) <= 600 or any(ord(c) < 32 for c in text):
        raise ValueError()
    return text


class CorrectionContext:
    """Single active context per channel identity; ephemeral ticket, fresh evidence.

    No caller supplied binding or owner boolean is accepted. A new selection
    invalidates the previous ticket even if new evidence is unavailable. Tickets
    cannot survive context switches, expiry, process restart or foreign sessions.
    Caller enters correction mode explicitly; arbitrary chat is not interpreted.
    """
    def __init__(self, *, owner_check, decision_read, memory_read, redact,
                 clock=time.time, ttl=300, capacity=256):
        if type(ttl) is not int or not 1 <= ttl <= 300 or type(capacity) is not int or not 1 <= capacity <= 256:
            raise ValueError()
        self.owner_check = owner_check
        self.decision_read = decision_read
        self.memory_read = memory_read
        self.redact = redact
        self.clock = clock
        self.ttl = ttl
        self.capacity = capacity
        self._contexts = {}
        self._lock = threading.RLock()

    def _key(self, platform, session_id, sender_id):
        if not all(isinstance(v, str) for v in (platform, session_id, sender_id)) or not session_id:
            raise ValueError()
        if self.owner_check(platform, session_id, sender_id) is not True:
            return None
        return platform, session_id, sender_id

    def _now(self):
        now = self.clock()
        if type(now) not in (int, float) or not math.isfinite(now) or now <= 0:
            raise ValueError()
        return now

    def _purge(self, now):
        for key, item in list(self._contexts.items()):
            if not item['created_at'] <= now < item['expires_at']:
                self._contexts.pop(key)

    def select(self, *, platform, session_id, sender_id='', task_id, source):
        """Explicit owner selection; must come from authenticated workflow adapter.

        Existence and immutable source bytes are checked. This does NOT establish
        that the original task was derived from that source or its claims true.
        """
        out = base('selection_unavailable')
        try:
            with self._lock:
                key = self._key(platform, session_id, sender_id)
                if key is None:
                    return base('not_owner')
                self._contexts.pop(key, None)
                now = self._now(); self._purge(now)
                if len(self._contexts) >= self.capacity:
                    return base('context_capacity_reached')
                if not isinstance(task_id, str) or not isinstance(source, str):
                    raise ValueError()
                _, task_id, source = owner_text('Düzeltme: Seçim\ngörev:'+task_id+'\nkaynak:'+source)
                safe, count = self.redact(source)
                if safe != source or type(count) is not int or count != 0:
                    return base('private_content_blocked')
                view = self.decision_read(task_id)
                task_binding = binding(view, task_id, self._now())
                memory = self.memory_read(source)
                end = self._now()
                binding(view, task_id, end)
                record, _ = source_record(memory, source)
                observed = memory.get('observed_at')
                if (type(observed) not in (int, float) or not math.isfinite(observed)
                        or not 0 < observed <= end or end-observed > 60 or end < now):
                    raise ValueError()
                ticket = secrets.token_urlsafe(32)
                self._contexts[key] = dict(ticket=ticket, task_id=task_id, source=source,
                    task_binding=deepcopy(task_binding), source_sha256=record['source_sha256'],
                    created_at=end, expires_at=end+self.ttl)
                out.update(status='selection_ready', context_ticket=ticket,
                    association_origin='explicit_authenticated_owner_selection',
                    task_derived_from_source_verified=False)
        except Exception as exc:
            out['error_kind'] = type(exc).__name__
        return out

    def close(self, *, platform, session_id, sender_id=''):
        with self._lock:
            try:
                key = self._key(platform, session_id, sender_id)
                if key is None:
                    return base('not_owner')
                self._contexts.pop(key, None)
                return base('context_closed')
            except Exception:
                return base('unavailable')

    def correct(self, *, platform, session_id, sender_id='', context_ticket,
                user_message, mode='correction'):
        out = base('unavailable')
        try:
            with self._lock:
                key = self._key(platform, session_id, sender_id)
                if key is None:
                    return base('not_owner')
                now = self._now(); self._purge(now)
                item = self._contexts.get(key)
                if (not item or not isinstance(context_ticket, str)
                        or not secrets.compare_digest(context_ticket, item['ticket'])):
                    return base('context_missing_or_changed')
                if mode != 'correction':
                    return base('explicit_correction_required')
                correction = literal_text(user_message)
                internal = 'Düzeltme: '+correction+'\ngörev:'+item['task_id']+'\nkaynak:'+item['source']
                result = propose_owner_lesson(platform=platform, session_id=session_id, sender_id=sender_id,
                    user_message=internal, owner_check=self.owner_check, decision_read=self.decision_read,
                    memory_read=self.memory_read, redact=self.redact, clock=self.clock)
                candidate = result.get('candidate')
                end = self._now()
                if not item['created_at'] <= end < item['expires_at']:
                    self._contexts.pop(key, None)
                    return base('context_expired_during_read')
                if candidate is None:
                    return result
                if candidate['task_binding'] != item['task_binding']:
                    self._contexts.pop(key, None)
                    return base('task_binding_changed')
                if candidate['source_sha256'] != item['source_sha256']:
                    self._contexts.pop(key, None)
                    return base('source_changed')
                result.update(association_origin='explicit_authenticated_owner_selection',
                    task_derived_from_source_verified=False, natural_language_intent_inferred=False)
                return result
        except Exception as exc:
            out['error_kind'] = type(exc).__name__
        return out
