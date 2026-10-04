"""Ordered, bounded private draft plans in the existing Pablo journal.

No shell, GUI, customer delivery or implicit human decision. Each step uses
the existing single-use guard and independent file reader. Signals describe
declared input availability; they are never external outcome verification.
"""
import hashlib
import json
import math
import re
from pablo_local_drafts import DraftError, expectation
from pablo_task_guard import fingerprint

PLAN_ACTION = 'local_draft_plan'


def instant(value):
    if value is not None and (type(value) not in (int, float) or not math.isfinite(value)
                              or not 0 < value <= 253402300799):
        raise DraftError('Invalid UTC instant')


def step_id(rid, name):
    return 'plan-step-' + hashlib.sha256((rid + '\0' + name).encode()).hexdigest()


def step_params(rid, plan, step):
    params = dict(name=step['name'], format=step['draft'].get('format', 'txt'),
                  content=step['draft']['content'], request_id=step_id(rid, step['name']))
    if plan.get('deadline_at') is not None:
        params['deadline_at'] = plan['deadline_at']
    return params


def validate_plan(rid, plan):
    if not isinstance(rid, str) or not rid or len(rid) > 128:
        raise DraftError('Invalid plan ID')
    rid.encode('utf-8')
    if not isinstance(plan, dict) or set(plan) - {'goal', 'steps', 'deadline_at', 'request_id'}:
        raise DraftError('Unsupported plan fields')
    if plan.get('request_id', rid) != rid:
        raise DraftError('Plan request mismatch')
    if not isinstance(plan.get('goal'), str) or not plan['goal'].strip() or len(plan['goal']) > 256:
        raise DraftError('Invalid goal')
    plan['goal'].encode('utf-8')
    instant(plan.get('deadline_at'))
    steps = plan.get('steps')
    if not isinstance(steps, list) or not 1 <= len(steps) <= 20:
        raise DraftError('Invalid step count')
    names, size = set(), 0
    for step in steps:
        if not isinstance(step, dict) or set(step) - {'name', 'draft', 'not_before', 'wait_for'}:
            raise DraftError('Unsupported step fields')
        name = step.get('name')
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', name) or name in names:
            raise DraftError('Invalid or repeated step name')
        names.add(name)
        draft = step.get('draft')
        if not isinstance(draft, dict) or set(draft) - {'format', 'content'} or 'content' not in draft:
            raise DraftError('Only bounded private drafts are supported')
        size += len(expectation(step_id(rid, name), step_params(rid, plan, step)).data)
        instant(step.get('not_before'))
        wait = step.get('wait_for')
        if wait is not None:
            if (not isinstance(wait, dict) or set(wait) - {'kind', 'key', 'who'}
                    or wait.get('kind') not in ('event', 'person')
                    or not isinstance(wait.get('key'), str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,64}', wait['key'])):
                raise DraftError('Invalid wait contract')
            if 'who' in wait and (not isinstance(wait['who'], str) or not 1 <= len(wait['who']) <= 64):
                raise DraftError('Invalid waiting person')
            if 'who' in wait:
                wait['who'].encode('utf-8')
            if wait['kind'] == 'person' and not wait.get('who'):
                raise DraftError('Person wait needs an identity label')
    if size > 2_000_000:
        raise DraftError('Plan exceeds total draft limit')
    return plan


class WorkPlans:
    def __init__(self, guard):
        self.guard = guard

    def load(self, rid):
        with self.guard.connect() as db:
            row = db.execute('SELECT params,digest,response FROM requests WHERE id=? AND action=?', (rid, PLAN_ACTION)).fetchone()
        if row is None:
            raise DraftError('Unknown plan')
        plan = validate_plan(rid, json.loads(row[0]))
        if fingerprint(PLAN_ACTION, plan) != row[1]:
            raise DraftError('Persisted plan binding changed')
        return plan, row[1], json.loads(row[2])

    def view(self, rid):
        with self.guard.connect() as db:
            row = db.execute('SELECT response,created_at,updated_at,deadline_at FROM requests WHERE id=?', (rid,)).fetchone()
            events = [dict(seq=r[0], phase=r[1], status=r[2], observed_at=r[3]) for r in
                      db.execute('SELECT seq,phase,status,observed_at FROM work_events WHERE request_id=? ORDER BY seq DESC LIMIT 20', (rid,))]
        result = json.loads(row[0])
        work = result.get('work') or {'phase': 'claimed' if result['status'] == 'IN_PROGRESS' else 'needs_review',
                                     'next_step': 'resume_plan', 'waiting_for': None}
        return dict(work, request_id=rid, action=PLAN_ACTION, status=result['status'], open=result['status'] not in ('SUCCESS','CANCELLED'),
                    created_at=row[1], updated_at=row[2], deadline_at=row[3], deadline_known=row[3] is not None,
                    overdue=row[3] is not None and row[3] < self.guard.clock() and result['status'] not in ('SUCCESS','CANCELLED'),
                    automatic_replay=False, events=list(reversed(events)))

    def child(self, rid, plan, step):
        sid = step_id(rid, step['name'])
        with self.guard.connect() as db:
            row = db.execute('SELECT action,digest,response,parent_id FROM requests WHERE id=?', (sid,)).fetchone()
        if row is None:
            return None
        if (row[0] != 'local_draft' or row[1] != fingerprint('local_draft', step_params(rid, plan, step))
                or row[3] != rid):
            raise DraftError('Step claim binding changed')
        return json.loads(row[2])

    def released(self, rid, digest, step):
        wait = step.get('wait_for')
        if wait is None:
            return True
        with self.guard.connect() as db:
            row = db.execute('SELECT input_digest,signal_key,actor_kind FROM work_plan_signals WHERE request_id=? AND step_name=?', (rid, step['name'])).fetchone()
        return bool(row and row[0] == digest and row[1] == wait['key']
                    and (wait['kind'] != 'person' or row[2] == 'owner'))

    def signal(self, rid, name, key, source, owner=False):
        with self.guard.lock:
            plan, digest, saved = self.load(rid)
            step = next((s for s in plan['steps'] if s['name'] == name), None)
            if (step is None or not step.get('wait_for') or step['wait_for']['key'] != key
                    or not isinstance(source, str) or not 1 <= len(source) <= 128):
                raise DraftError('Signal does not match the plan')
            if step['wait_for']['kind'] == 'person' and not owner:
                raise PermissionError('Person wait requires a distinct owner credential')
            actor = 'owner' if step['wait_for']['kind'] == 'person' else 'event_report'
            with self.guard.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                old = db.execute('SELECT input_digest,signal_key,actor_kind,source FROM work_plan_signals WHERE request_id=? AND step_name=?', (rid, name)).fetchone()
                value = (digest, key, actor, source)
                if old:
                    if old != value:
                        raise DraftError('Signal changed after recording')
                else:
                    current = json.loads(db.execute('SELECT response FROM requests WHERE id=?', (rid,)).fetchone()[0])
                    if current.get('work', {}).get('next_step') != name or current['status'] != 'WAITING_FOR_EVENT':
                        raise DraftError('Only the current waiting step can be released')
                    db.execute('INSERT INTO work_plan_signals VALUES(?,?,?,?,?,?,?)', (rid, name, *value, self.guard.clock()))
                    self.guard._phase(db, rid, 'signal_recorded')
            return {'request_id': rid, 'step': name, 'signal_recorded': True, 'authority': actor, 'is_approval': False}

    def save(self, rid, plan, status, index, observations, phase, waiting=None, reason=None):
        current = plan['steps'][index] if index < len(plan['steps']) else None
        work = {'goal': plan['goal'], 'phase': phase, 'next_step': current['name'] if current else 'none',
                'waiting_for': waiting, 'resume_at': current.get('not_before') if current else None,
                'completed_count': index, 'total_steps': len(plan['steps']),
                'steps': [{'name': s['name'], 'request_id': step_id(rid, s['name']),
                           'status': 'verified' if i < index else ('current' if i == index else 'pending')}
                          for i, s in enumerate(plan['steps'])]}
        result = self.guard.response(rid, status, work=work, outcome_verified=status == 'SUCCESS',
                                    action_verified=False, delivered=False, error=reason,
                                    outcome_evidence={'method': 'independent_plan_file_reads', 'request_id': rid,
                                    'input_digest': fingerprint(PLAN_ACTION, plan), 'steps': observations,
                                    'observed_at': self.guard.clock()})
        with self.guard.connect() as db:
            return self.guard.store(db, rid, result)

    def cancel(self, rid):
        with self.guard.lock:
            plan, digest, saved = self.load(rid)
            if saved['status'] in ('SUCCESS','CANCELLED'):
                return saved
            work = dict(saved.get('work') or {}, phase='cancelled', next_step='none', waiting_for=None)
            result = self.guard.response(rid, 'CANCELLED', outcome_verified=False, work=work,
                                         delivered=False, error='Stop future steps; retain already claimed work and files')
            with self.guard.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                return self.guard.store(db,rid,result)

    def observe(self, rid, plan, step):
        params = step_params(rid, plan, step); sid = params['request_id']
        expected = expectation(sid, params)
        observed = self.guard.local_drafts.observe(sid, expected)
        if observed['observed_sha256'] != expected.sha256 or observed['observed_bytes'] != len(expected.data):
            raise DraftError('Completed step file changed')
        return dict(observed, request_id=sid, input_digest=fingerprint('local_draft', params),
                    expected_sha256=expected.sha256, expected_bytes=len(expected.data), observed_at=self.guard.clock())

    def advance(self, rid, allow_new=True):
        with self.guard.lock:
            try:
                plan, digest, saved = self.load(rid)
            except (DraftError, ValueError, TypeError, UnicodeError):
                with self.guard.connect() as db:
                    return self.guard.store(db, rid, self.guard.response(rid, 'RECOVERY_BLOCKED', outcome_verified=False,
                                            error='Invalid persisted plan; do not execute'))
            if saved['status'] in ('SUCCESS','CANCELLED'):
                return saved  # A recorded observation, not a fresh measurement.
            observations = []
            for index, step in enumerate(plan['steps']):
                try:
                    child = self.child(rid, plan, step)
                    if child is None:
                        if plan.get('deadline_at') is not None and plan['deadline_at'] < self.guard.clock():
                            return self.save(rid,plan,'NEEDS_REVIEW',index,observations,'deadline_passed',
                                             {'kind':'deadline','at':plan['deadline_at']},'Deadline passed; do not start new steps')
                        if step.get('not_before') is not None and step['not_before'] > self.guard.clock():
                            return self.save(rid, plan, 'WAITING_FOR_TIME', index, observations, 'waiting_for_time', {'kind': 'time', 'at': step['not_before']})
                        if not self.released(rid, digest, step):
                            return self.save(rid, plan, 'WAITING_FOR_EVENT', index, observations, 'waiting_for_'+step['wait_for']['kind'], step['wait_for'])
                        if not allow_new:
                            return self.save(rid, plan, 'IN_PROGRESS', index, observations, 'ready', {'kind': 'new_step'})
                        child = self.guard.execute('local_draft', step_params(rid, plan, step), step_id(rid, step['name']), parent_id=rid)
                    elif child['status'] != 'SUCCESS':
                        child = self.guard.reconcile(step_id(rid, step['name']))
                    if child['status'] != 'SUCCESS' or child.get('outcome_verified') is not True:
                        return self.save(rid, plan, 'IN_PROGRESS' if child['status'] == 'IN_PROGRESS' else 'NEEDS_REVIEW',
                                         index, observations, 'observing' if child['status'] == 'IN_PROGRESS' else 'needs_review',
                                         {'kind': 'file_evidence', 'step': step['name']}, 'Step outcome is not verified; no replay')
                    # Re-observe every completed prefix before allowing another
                    # step. A cached SUCCESS cannot mask a changed/missing file.
                    observations.append(self.observe(rid, plan, step))
                except (OSError, DraftError, ValueError, TypeError) as exc:
                    return self.save(rid, plan, 'NEEDS_REVIEW', index, observations, 'needs_review',
                                     {'kind': 'file_evidence', 'step': step['name']}, type(exc).__name__)
            return self.save(rid, plan, 'SUCCESS', len(plan['steps']), observations, 'completed')
