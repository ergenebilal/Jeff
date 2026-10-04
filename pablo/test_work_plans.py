"""Real files and interrupted processes; time jumps are explicit fixture clocks."""
import ast
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from http.server import BaseHTTPRequestHandler
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.parse
from unittest import mock
from pablo_local_drafts import LocalDraftStore
from pablo_task_guard import TaskGuard,allowed_ip
from pablo_work_plans import WorkPlans,DraftError,step_id,step_params


def fixture():
    return {'goal':'Private ordered draft fixture','deadline_at':200000,
            'steps':[{'name':'first','draft':{'content':'first file'}},
                     {'name':'second','draft':{'format':'md','content':'second file'}}]}


CHILD='''
import json,os,sys
from pathlib import Path
from pablo_task_guard import TaskGuard
from pablo_work_plans import step_id
Path(sys.argv[1],'child-source.json').write_text(json.dumps({'guard':sys.modules[TaskGuard.__module__].__file__}))
guard=TaskGuard(Path(sys.argv[1])/'journal.db',{},'',lambda:False,clock=lambda:1000)
plan=json.loads(sys.argv[3]);mode=sys.argv[2]
original_store=guard.store
def store(db,rid,result):
    if mode=='before_final' and rid=='plan' and result['status']=='SUCCESS':os._exit(91)
    value=original_store(db,rid,result)
    if mode=='after_first' and rid==step_id('plan','first') and result['status']=='SUCCESS':
        db.commit()
        os._exit(91)
    return value
guard.store=store
write=guard.local_drafts.write
def interrupted(rid,expected):
    if rid==step_id('plan','second') and mode=='before_second':os._exit(91)
    value=write(rid,expected)
    if rid==step_id('plan','second') and mode=='after_second':os._exit(91)
    return value
guard.local_drafts.write=interrupted
guard.execute('local_draft_plan',plan,'plan')
os._exit(91)
'''


class WorkPlanTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.now=1000;self.plan=fixture()

    def guard(self):return TaskGuard(self.root/'journal.db',{},'',lambda:False,clock=lambda:self.now)
    def create(self,plan=None):return self.guard().execute('local_draft_plan',plan or self.plan,'plan')
    def path(self,name):return self.root/'verified-drafts'/__import__('hashlib').sha256(step_id('plan',name).encode()).hexdigest()/(name+('.md' if name=='second' else '.txt'))
    def crash(self,mode):
        source_root=Path(sys.modules[TaskGuard.__module__].__file__).parent
        env=os.environ|{'PYTHONPATH':str(source_root)+os.pathsep+os.environ.get('PYTHONPATH','')}
        result=subprocess.run([sys.executable,'-c',CHILD,str(self.root),mode,json.dumps(self.plan)],env=env,capture_output=True,timeout=15)
        self.assertEqual(result.returncode,91,result.stderr.decode())
        self.assertEqual(Path(json.loads((self.root/'child-source.json').read_text())['guard']).resolve(),(source_root/'pablo_task_guard.py').resolve())
        if mode=='after_first':
            with closing(sqlite3.connect(self.root/'journal.db')) as db:
                self.assertEqual(db.execute('SELECT status FROM requests WHERE id=?',(step_id('plan','first'),)).fetchone()[0],'SUCCESS')

    def test_real_crash_after_first_checkpoint_resumes_only_unclaimed_second(self):
        self.crash('after_first');first=self.path('first');mtime=first.stat().st_mtime_ns
        guard=self.guard();original=guard.local_drafts.write;written=[]
        def write(rid,expected):written.append(rid);return original(rid,expected)
        with mock.patch.object(guard.local_drafts,'write',write):result=guard.advance_plan('plan')
        self.assertEqual(written,[step_id('plan','second')])
        self.assertEqual(result['status'],'SUCCESS');self.assertTrue(result['outcome_verified'])
        self.assertEqual(first.stat().st_mtime_ns,mtime)
        self.assertEqual(result['work']['completed_count'],2)
        self.assertEqual(self.path('second').read_bytes(),b'second file')

    def test_real_crash_after_second_publication_recovers_with_no_writes(self):
        self.crash('after_second');before={n:self.path(n).stat().st_mtime_ns for n in ('first','second')}
        with mock.patch.object(LocalDraftStore,'write',side_effect=AssertionError('replayed')):
            self.assertEqual(self.guard().advance_plan('plan')['status'],'SUCCESS')
        self.assertEqual(before,{n:self.path(n).stat().st_mtime_ns for n in before})

    def test_real_crash_before_final_parent_commit_reconstructs_verified_plan(self):
        self.crash('before_final')
        with mock.patch.object(LocalDraftStore,'write',side_effect=AssertionError('replayed')):
            result=self.guard().advance_plan('plan')
        self.assertEqual(result['status'],'SUCCESS')
        self.assertEqual(len(result['outcome_evidence']['steps']),2)

    def test_claimed_missing_step_stays_open_and_blocks_later_steps(self):
        self.plan['steps'].append({'name':'third','draft':{'content':'third'}})
        self.crash('before_second');self.now=1600
        with mock.patch.object(LocalDraftStore,'write',side_effect=AssertionError('replayed')):
            result=self.guard().advance_plan('plan')
        self.assertEqual(result['status'],'NEEDS_REVIEW')
        self.assertEqual(result['work']['next_step'],'second')
        self.assertEqual(result['work']['completed_count'],1)
        self.assertFalse(self.path('second').exists())
        self.assertEqual(self.guard().get(step_id('plan','third'))['status'],'NOT_FOUND')

    def test_multi_day_time_and_event_wait_survive_reopening(self):
        self.plan['steps'][1].update(not_before=173800,wait_for={'kind':'event','key':'input_ready'})
        result=self.create();self.assertEqual(result['status'],'WAITING_FOR_TIME')
        mtime=self.path('first').stat().st_mtime_ns
        self.assertEqual(self.guard().work_snapshot()['open_count'],1) # No child duplication.
        self.now=173800;guard=self.guard();result=guard.advance_plan('plan')
        self.assertEqual(result['status'],'WAITING_FOR_EVENT')
        self.assertEqual(result['work']['waiting_for']['key'],'input_ready')
        recorded=WorkPlans(guard).signal('plan','second','input_ready','fixture input receipt')
        self.assertFalse(recorded['is_approval'])
        self.assertEqual(WorkPlans(self.guard()).signal('plan','second','input_ready','fixture input receipt'),recorded)
        result=self.guard().advance_plan('plan')
        self.assertEqual(result['status'],'SUCCESS')
        self.assertEqual(self.path('first').stat().st_mtime_ns,mtime)

    def test_person_wait_requires_owner_and_persists_across_restart(self):
        self.plan['steps'][1]['wait_for']={'kind':'person','key':'input_ready','who':'fixture-person'}
        self.assertEqual(self.create()['work']['phase'],'waiting_for_person')
        with self.assertRaises(PermissionError):WorkPlans(self.guard()).signal('plan','second','input_ready','fixture-person reply')
        self.assertFalse(self.path('second').exists())
        WorkPlans(self.guard()).signal('plan','second','input_ready','fixture-person reply',owner=True)
        self.assertEqual(self.guard().advance_plan('plan')['status'],'SUCCESS')

    def test_changed_plan_or_signal_cannot_reuse_immutable_identity(self):
        self.plan['steps'][1]['wait_for']={'kind':'event','key':'ready'}
        self.create();guard=self.guard()
        changed=self.plan|{'goal':'changed'}
        self.assertEqual(guard.execute('local_draft_plan',changed,'plan')['status'],'CONFLICT')
        with self.assertRaises(DraftError):WorkPlans(guard).signal('plan','first','ready','fixture')
        with self.assertRaises(DraftError):WorkPlans(guard).signal('plan','second','wrong','fixture')
        WorkPlans(guard).signal('plan','second','ready','fixture')
        with self.assertRaises(DraftError):WorkPlans(guard).signal('plan','second','ready','edited receipt')
        with guard.connect() as db:db.execute('UPDATE requests SET params=? WHERE id=?',(json.dumps(changed),'plan'))
        with mock.patch.object(LocalDraftStore,'write') as writer:
            self.assertEqual(guard.advance_plan('plan')['status'],'RECOVERY_BLOCKED');writer.assert_not_called()

    def test_changed_completed_file_blocks_further_steps_without_overwrite(self):
        self.plan['steps'][1]['not_before']=2000;self.create()
        self.path('first').write_bytes(b'changed');self.now=2001
        with mock.patch.object(LocalDraftStore,'write') as writer:result=self.guard().advance_plan('plan');writer.assert_not_called()
        self.assertEqual(result['status'],'NEEDS_REVIEW')
        self.assertEqual(result['work']['next_step'],'first')
        self.assertFalse(self.path('second').exists());self.assertEqual(self.path('first').read_bytes(),b'changed')

    def test_observation_only_reconcile_never_claims_new_steps(self):
        self.crash('after_first');guard=self.guard()
        with mock.patch.object(LocalDraftStore,'write') as writer:
            result=guard.reconcile('plan');writer.assert_not_called()
        self.assertEqual(result['work']['phase'],'ready')
        self.assertEqual(guard.get(step_id('plan','second'))['status'],'NOT_FOUND')

    def test_concurrent_guards_write_each_stable_step_at_most_once(self):
        self.plan['steps'][0]['not_before']=2000;self.create();self.now=2000
        first,second=self.guard(),self.guard();entered,release=threading.Event(),threading.Event()
        original=LocalDraftStore.write;calls=[];lock=threading.Lock()
        def delayed(store,rid,expected):
            with lock:calls.append(rid)
            if rid==step_id('plan','first'):
                entered.set();self.assertTrue(release.wait(5))
            return original(store,rid,expected)
        with mock.patch.object(LocalDraftStore,'write',delayed),ThreadPoolExecutor(max_workers=2) as pool:
            job=pool.submit(first.advance_plan,'plan');self.assertTrue(entered.wait(3))
            other=pool.submit(second.advance_plan,'plan')
            self.assertEqual(other.result(5)['status'],'IN_PROGRESS');release.set()
            self.assertEqual(job.result(5)['status'],'SUCCESS')
        self.assertEqual(sorted(calls),sorted([step_id('plan','first'),step_id('plan','second')]))
        self.assertEqual(second.advance_plan('plan')['status'],'SUCCESS')

    def test_invalid_or_external_step_never_creates_a_claim(self):
        bad=[self.plan|{'steps':[]},self.plan|{'steps':[{'name':'pay','action':'payment','draft':{'content':'x'}}]},
             self.plan|{'steps':[self.plan['steps'][0]]*2},self.plan|{'steps':[{'name':'bad','draft':{'content':'x','path':'outside'}}]},
             self.plan|{'deadline_at':float('nan')},self.plan|{'steps':[{'name':'bad','draft':{'content':'x'},'not_before':True}]},
             self.plan|{'steps':[{'name':'bad','draft':{'content':'x'},'wait_for':{'kind':'person','key':'ready'}}]}]
        guard=self.guard()
        for index,plan in enumerate(bad):
            with self.subTest(index=index),mock.patch.object(LocalDraftStore,'write') as writer:
                self.assertEqual(guard.execute('local_draft_plan',plan,'bad-'+str(index))['status'],'ERROR');writer.assert_not_called()
                self.assertEqual(guard.get('bad-'+str(index))['status'],'NOT_FOUND')

    def test_historical_errors_are_quiet_but_unverified_unknowns_are_visible(self):
        guard=self.guard()
        with guard.connect() as db:
            for rid,status in [('error','ERROR'),('failed','FAILED'),('blocked','BLOCKED'),('unknown','UNKNOWN'),('running','IN_PROGRESS'),('queued-result','ERROR')]:
                db.execute('INSERT INTO requests(id,action,status,response) VALUES(?,?,?,?)',(rid,'shell',status,json.dumps(guard.response(rid,status))))
            db.execute('INSERT INTO outbox VALUES(?,?)',('queued-result','{}'))
        reopened=self.guard();view=reopened.work_snapshot()
        self.assertEqual(view['history_open_count'],3);self.assertEqual(view['open_count'],3)
        self.assertEqual(view['total_open_and_history'],6)
        self.assertEqual(reopened.work_snapshot(include_history=True)['open_count'],6)
        history=reopened.work_status('error');self.assertTrue(history['history_only']);self.assertTrue(history['open'])
        self.assertIsNone(history['created_at']);self.assertEqual(history['status'],'ERROR')
        self.assertFalse(reopened.work_status('unknown')['history_only'])
        with reopened.connect() as db:
            with self.assertRaises(sqlite3.IntegrityError):db.execute('DELETE FROM work_history')

    def test_parent_link_rejects_unplanned_child_and_history_is_append_only(self):
        self.create();guard=self.guard()
        with mock.patch.object(LocalDraftStore,'write') as writer:
            self.assertEqual(guard.execute('local_draft',{'name':'extra','content':'x'},'extra',parent_id='plan')['status'],'CONFLICT');writer.assert_not_called()
        with guard.connect() as db:
            with self.assertRaises(sqlite3.IntegrityError):db.execute("UPDATE work_events SET phase='completed'")

    def test_cancelled_plan_cannot_start_new_steps_after_reopening(self):
        self.plan['steps'][1]['not_before']=2000;self.create();guard=self.guard()
        first=self.path('first');mtime=first.stat().st_mtime_ns
        self.assertEqual(guard.cancel_plan('plan')['status'],'CANCELLED');self.now=2000
        reopened=self.guard()
        with mock.patch.object(LocalDraftStore,'write') as writer:
            self.assertEqual(reopened.advance_plan('plan')['status'],'CANCELLED');writer.assert_not_called()
        self.assertFalse(self.path('second').exists());self.assertEqual(first.stat().st_mtime_ns,mtime)
        self.assertEqual(reopened.work_snapshot()['open_count'],0)

    def test_expired_deadline_holds_new_steps_without_faking_completion(self):
        self.plan['deadline_at']=900
        with mock.patch.object(LocalDraftStore,'write') as writer:result=self.create();writer.assert_not_called()
        self.assertEqual(result['status'],'NEEDS_REVIEW');self.assertEqual(result['work']['phase'],'deadline_passed')
        self.assertTrue(self.guard().work_status('plan')['overdue'])
        self.assertFalse(result['outcome_verified'])

    def test_cancel_from_second_guard_prevents_later_claim_after_active_step(self):
        guard=self.guard();entered,release=threading.Event(),threading.Event()
        original=guard.local_drafts.write
        def paused(rid,expected):
            entered.set();self.assertTrue(release.wait(5));return original(rid,expected)
        with mock.patch.object(guard.local_drafts,'write',paused),ThreadPoolExecutor(max_workers=1) as pool:
            job=pool.submit(guard.execute,'local_draft_plan',self.plan,'plan');self.assertTrue(entered.wait(3))
            other=self.guard()
            try:self.assertEqual(other.cancel_plan('plan')['status'],'CANCELLED')
            finally:release.set()
            self.assertEqual(job.result(5)['status'],'CANCELLED')
        self.assertTrue(self.path('first').exists());self.assertFalse(self.path('second').exists())

    def test_real_rest_entry_preserves_plan_and_owner_signal_boundary(self):
        guard=self.guard();self.plan['steps'][1]['wait_for']={'kind':'person','key':'ready','who':'fixture'}
        tree=ast.parse(Path(__file__).with_name('hermes_node.py').read_text(encoding='utf-8'))
        selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('normalize_tool_params','execute_request') or isinstance(n,ast.ClassDef) and n.name=='PabloRequestHandler']
        namespace={'BaseHTTPRequestHandler':BaseHTTPRequestHandler,'json':json,'ast':ast,'urllib':__import__('urllib'),
                   'allowed_ip':allowed_ip,'CONFIG':{'auth_token':'agent-fixture','approval_decision_key':'owner-fixture'},
                   'task_guard':lambda:guard,'send_telegram_approval_request':mock.Mock(side_effect=AssertionError('notification'))}
        exec(compile(ast.Module(body=selected,type_ignores=[]),'real-plan-http','exec'),namespace)
        def post(path,body,owner=''):
            handler=namespace['PabloRequestHandler'].__new__(namespace['PabloRequestHandler']);handler.path=path
            handler.client_address=('127.0.0.1',1234);data=json.dumps(body).encode()
            handler.headers={'X-Bridge-Key':'agent-fixture','X-Approval-Key':owner,'Content-Length':str(len(data))}
            handler.rfile,handler.wfile=io.BytesIO(data),io.BytesIO()
            handler.send_response,handler.send_header,handler.end_headers=mock.Mock(),mock.Mock(),mock.Mock()
            handler.do_POST();return handler.send_response.call_args.args[0],json.loads(handler.wfile.getvalue())
        code,result=post('/execute',{'action':'local_draft_plan','params':self.plan,'request_id':'plan'})
        self.assertEqual(code,200);self.assertEqual(result['status'],'WAITING_FOR_EVENT')
        body={'step':'second','key':'ready','source':'fixture-person reply'}
        self.assertEqual(post('/work/plan/signal',body)[0],403)
        self.assertFalse(self.path('second').exists())
        self.assertEqual(post('/work/plan/signal',body,'owner-fixture')[0],200)
        self.assertEqual(post('/work/plan/advance',{})[1]['phase'],'completed')


if __name__=='__main__':unittest.main()
