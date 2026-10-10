"""Prototype: ephemeral, task-bound owner correction proposals; never memory writes.

Call through authenticated channel metadata, with the existing owner predicate,
authenticated decision reader, source-backed memory reader and pure secret filter.
Dependency injection is a test seam, not authentication of supplied dictionaries.
The explicit prototype grammar is internal; natural-language inference is absent.
No result is an approved or applied lesson, new execution permission, or evidence
that source statements are true. Rechecking requires a fresh owner reaffirmation.
"""
import hashlib
import json
import math
from pathlib import PurePosixPath
import re
import time


def base(status):
    return dict(status=status, candidate=None, read_only=True, proposed_only=True,
                rule_applied=False, memory_write_authorized=False,
                execution_authorized=False, reexecution_authorized=False,
                customer_contact_authorized=False, source_statement_truth_verified=False,
                model_calls=0)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def sha(value):
    return isinstance(value, str) and re.fullmatch('[a-f0-9]{64}', value) is not None


def strict_object(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError('Duplicate key')
            out[key] = value
        return out
    def invalid(_):
        raise ValueError('Nonfinite number')
    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    if not isinstance(value, dict):
        raise ValueError('Invalid object')
    return value


def owner_text(message):
    if not isinstance(message, str) or len(message) > 250000:
        raise ValueError('Invalid message')
    if message.lstrip().startswith(('{', '[')):
        wrapper = strict_object(message)
        if set(wrapper) != {'trusted_user_request', 'untrusted_panel_data'}:
            raise ValueError('Foreign envelope')
        data = wrapper['untrusted_panel_data']
        if isinstance(data, str):
            data = strict_object(data)
        if not isinstance(data, dict):
            raise ValueError('Invalid panel envelope')
        message = wrapper['trusted_user_request']
    if not isinstance(message, str) or not 1 <= len(message) <= 1800:
        raise ValueError('Missing or oversized owner text')
    # An explicit internal prototype format. Missing links must not be inferred.
    match = re.fullmatch(r'Düzeltme: ([^\r\n]{1,600})\r?\n'
                         r'görev:([A-Za-z0-9_-]{1,128})\r?\n'
                         r'kaynak:([^\r\n]{1,400})', message.strip())
    if not match:
        raise ValueError('No explicit scoped correction')
    correction, task_id, source = match.groups()
    path = PurePosixPath(source)
    if (path.is_absolute() or '..' in path.parts or '\\' in source or
            not path.parts or path.parts[0] != 'knowledge' or
            path.as_posix() != source or any(ord(c) < 32 for c in source)):
        raise ValueError('Outside knowledge scope')
    return correction, task_id, source


def binding(view, task_id, now):
    if (not isinstance(view, dict) or view.get('status') != 'observed'
            or view.get('request_id') != task_id
            or view.get('requested_task_id') != task_id
            or view.get('criterion_source') != 'stored_original_request'
            or view.get('goal_scope') != 'existing_private_draft_bytes_only'
            or view.get('read_only') is not True or view.get('fresh_file_read') is not True
            or view.get('current_task_binding_matched') is not True
            or view.get('new_task_outcome') not in ('matched_at_observation', 'mismatch', 'unknown')
            or any(view.get(k) is not False for k in (
                'execution_authorized', 'reexecution_authorized', 'execution_outcome_verified',
                'semantic_quality_verified', 'customer_delivery_verified'))):
        raise ValueError('Unusable task evidence')
    proof = view.get('current_observation')
    if (not isinstance(proof, dict) or proof.get('request_id') != task_id
            or not sha(proof.get('input_digest')) or not sha(proof.get('expected_sha256'))
            or proof.get('method') != 'independent_current_file_read'
            or not sha(proof.get('observed_sha256'))
            or type(proof.get('expected_bytes')) is not int or not 0 < proof['expected_bytes'] <= 500000
            or type(proof.get('observed_bytes')) is not int or not 0 <= proof['observed_bytes'] <= 500000
            or type(proof.get('observed_at')) not in (int, float)
            or not math.isfinite(proof['observed_at']) or not 0 < proof['observed_at'] <= now
            or now - proof['observed_at'] > 60):
        raise ValueError('Invalid criterion binding')
    matched = proof['observed_sha256'] == proof['expected_sha256'] and proof['observed_bytes'] == proof['expected_bytes']
    if (view.get('current_file_outcome_verified') is not matched
            or view['new_task_outcome'] == 'matched_at_observation' and not matched
            or view['new_task_outcome'] == 'mismatch' and matched):
        raise ValueError('Contradictory observation')
    return {k: proof[k] for k in ('request_id', 'input_digest', 'expected_sha256', 'expected_bytes')}


def source_record(result, source):
    if not isinstance(result, dict) or result.get('read_only') is not True:
        raise ValueError('Unusable source response')
    records = result.get('records')
    if not isinstance(records, list):
        raise ValueError('Invalid source records')
    found = [r for r in records if isinstance(r, dict) and r.get('source') == source]
    if len(found) != 1 or found[0].get('source_hash_matched') is not True or not sha(found[0].get('source_sha256')):
        raise ValueError('Missing, ambiguous or changed source')
    record = found[0]
    date = record.get('declared_date')
    if (not isinstance(date, dict) or date.get('state') not in ('declared', 'unknown', 'invalid', 'future_invalid')):
        raise ValueError('Invalid source date')
    conflicts = result.get('conflicts')
    if not isinstance(conflicts, list):
        raise ValueError('Invalid conflicts')
    conflicted = any(source in c.get('sources', []) and c.get('resolved') is not True
                     for c in conflicts if isinstance(c, dict))
    review = (conflicted or date['state'] != 'declared'
              or record.get('assessment') != 'historical_source_statement')
    return record, review


def propose_owner_lesson(*, platform, session_id, sender_id='', user_message,
                         scope='this_task_only', owner_check, decision_read,
                         memory_read, redact, clock=time.time):
    out = base('unavailable')
    try:
        # Authenticate before parsing, exposing, or reading any private task/source.
        if owner_check(platform, session_id, sender_id) is not True:
            return base('not_owner')
        if scope != 'this_task_only':
            return base('unsupported_scope')
        correction, task_id, source = owner_text(user_message)
        safe, count = redact(correction + '\n' + source)
        if safe != correction + '\n' + source or type(count) is not int or count != 0:
            return base('private_content_blocked')
        started = clock()
        if type(started) not in (int, float) or not math.isfinite(started) or started <= 0:
            raise ValueError('Invalid clock')
        view = decision_read(task_id)
        # Reject unusable tasks before consulting any memory source.
        current = clock()
        task_binding = binding(view, task_id, current)
        memory = memory_read(source)
        observed_at = clock()
        if type(observed_at) not in (int, float) or not math.isfinite(observed_at) or observed_at < started:
            raise ValueError('Clock changed')
        binding(view, task_id, observed_at)
        record, review = source_record(memory, source)
        source_time = memory.get('observed_at')
        if (type(source_time) not in (int, float) or not math.isfinite(source_time)
                or not 0 < source_time <= observed_at or observed_at - source_time > 60):
            raise ValueError('Stale source read')
        item = dict(schema_version=1, scope='this_task_only', owner_correction=correction,
                    owner_correction_sha256=digest([correction, task_id, source]),
                    correction_origin='authenticated_current_owner_request',
                    inferred_general_rule=False, task_binding=task_binding,
                    source=source, source_sha256=record['source_sha256'],
                    source_date=dict(record['declared_date']),
                    source_assessment=record.get('assessment'),
                    source_review_required=review, current_task_outcome=view['new_task_outcome'],
                    execution_state=view.get('execution_state'), observed_at=observed_at,
                    rule_applied=False, memory_write_authorized=False)
        # Identity binds the original request and source, not a reusable success score.
        item['candidate_id'] = digest({k: item[k] for k in (
            'scope', 'owner_correction_sha256', 'task_binding', 'source', 'source_sha256')})
        out.update(status='requires_source_review' if review else 'candidate_only', candidate=item)
    except Exception as exc:
        out['error_kind'] = type(exc).__name__
    return out


def recheck_owner_lesson(candidate, **dependencies):
    """Fresh owner reaffirmation + fresh readers. Does not authenticate cached prose."""
    current = propose_owner_lesson(**dependencies)
    out = base('inconclusive')
    if current['status'] == 'not_owner':
        return current
    if not isinstance(candidate, dict) or current.get('candidate') is None:
        return out
    expected = current['candidate']
    if (candidate.get('rule_applied') is not False or candidate.get('memory_write_authorized') is not False
            or candidate.get('scope') != 'this_task_only' or candidate.get('inferred_general_rule') is not False):
        return base('untrusted_candidate')
    if candidate.get('owner_correction_sha256') != expected['owner_correction_sha256']:
        return base('correction_changed')
    if candidate.get('owner_correction') != expected['owner_correction']:
        return base('untrusted_candidate')
    if candidate.get('task_binding') != expected['task_binding']:
        return base('task_binding_changed')
    if candidate.get('source') != expected['source'] or candidate.get('source_sha256') != expected['source_sha256']:
        return base('source_changed')
    if candidate.get('candidate_id') != expected['candidate_id']:
        return base('untrusted_candidate')
    out.update(status='requires_source_review' if expected['source_review_required'] else 'bindings_still_match',
               candidate=expected, owner_reaffirmed_now=True, owner_review_still_required=True)
    return out
