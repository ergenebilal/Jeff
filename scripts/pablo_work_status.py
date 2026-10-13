#!/usr/bin/env python3
"""Read Pablo's durable work record or reconcile file evidence without replay."""
import argparse
import json
import math
import time
import os
import re
import sys
import urllib.error
from urllib.request import Request, urlopen, build_opener, ProxyHandler, HTTPRedirectHandler
try:
    from .pablo_dispatch import bridge_key
except ImportError:
    from pablo_dispatch import bridge_key



WORK_PAGE_LIMIT = 20
WORK_RESPONSE_BOUND = 262144
WORK_MAX_AGE = 60
WORK_FIELDS = {'open_count','items','next_offset','observed_at','automatic_replay',
               'history_open_count','total_open_and_history','includes_history'}
WORK_BUCKETS = ('execution_claim_waiting_outcome','recorded_error','recorded_in_progress',
                'recorded_owner_wait','recorded_time_wait','recorded_event_wait',
                'recorded_uncertain','recorded_result_claim','other_or_unknown')
WORK_ACTIONS = {'read_file','shell','clinic_radar','marketing_draft','marketing_deep_prepare',
                'local_draft','local_draft_plan','marketing_contact_event','marketing_deep_analyze'}


def unknown_work(reason='work_observation_unavailable'):
    return dict(schema_version=1,status='unavailable',reason_code=reason,observed_at=None,
                visible_page_records=None,reported_open_projection_count=None,
                reported_history_open_count=None,reported_total_open_and_history=None,
                next_offset=None,page_complete=None,counts_scope='current_page_only',
                counts={name:None for name in WORK_BUCKETS},records=[],
                active_business_work_count=None,accepted_results_count=None,
                runtime_process_health_verified=False,current_file_outcome_verified=False,
                semantic_goal_verified=False,customer_delivery_verified=False,
                closed_records_included=False,read_only=True,execution_authorized=False,
                reexecution_authorized=False,owner_approval_verified=False,
                source_instruction_authority='none',automatic_replay=False)


def work_bucket(status):
    if status=='EXECUTION_SUCCEEDED':return 'execution_claim_waiting_outcome'
    if status in {'ERROR','FAILED','EXECUTION_FAILED'}:return 'recorded_error'
    if status=='IN_PROGRESS':return 'recorded_in_progress'
    if status=='APPROVAL_REQUIRED':return 'recorded_owner_wait'
    if status=='WAITING_FOR_TIME':return 'recorded_time_wait'
    if status=='WAITING_FOR_EVENT':return 'recorded_event_wait'
    if status in {'OUTCOME_UNKNOWN','RECOVERY_BLOCKED','NEEDS_REVIEW','VERIFICATION_UNAVAILABLE','OUTCOME_MISMATCH'}:return 'recorded_uncertain'
    if status=='SUCCESS':return 'recorded_result_claim'
    return 'other_or_unknown'


def summarize_current_work(value, *, now):
    out=unknown_work('invalid_work_projection')
    if not isinstance(value,dict) or set(value)!=WORK_FIELDS:
        return out
    stamp=value['observed_at']
    if (type(now) not in (int,float) or not math.isfinite(now) or now<=0
            or type(stamp) not in (int,float) or not math.isfinite(stamp) or stamp<=0):
        return unknown_work('invalid_observation_time')
    if now-stamp>WORK_MAX_AGE or stamp>now+5:
        return unknown_work('stale_or_future_work_observation')
    counts=[value[k] for k in ('open_count','history_open_count','total_open_and_history')]
    if (any(type(n) is not int or not 0<=n<=1000000 for n in counts)
            or counts[2]!=counts[0]+counts[1] or value['automatic_replay'] is not False
            or value['includes_history'] is not False):
        return out
    items=value['items'];cursor=value['next_offset']
    if not isinstance(items,list) or len(items)>WORK_PAGE_LIMIT or len(items)>counts[0]:
        return out
    if (cursor is None and counts[0]!=len(items)
            or cursor is not None and (type(cursor) is not int or cursor!=len(items) or not 0<cursor<counts[0])):
        return out
    totals={name:0 for name in WORK_BUCKETS};records=[];seen=set()
    for row in items:
        if not isinstance(row,dict):return out
        rid=row.get('request_id');status=row.get('status');action=row.get('action')
        if (not isinstance(rid,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}',rid)
                or rid in seen or not isinstance(status,str) or not re.fullmatch(r'[A-Z_]{1,64}',status)
                or not isinstance(action,str) or not re.fullmatch(r'[a-z][a-z0-9_]{0,63}',action)
                or row.get('open') is not True):return out
        for field in ('history_only','outcome_verified','completion_authority'):
            if field in row and type(row[field]) is not bool:return out
        if row.get('history_only') is True:return out
        seen.add(rid);bucket=work_bucket(status);totals[bucket]+=1
        records.append(dict(request_id=rid,action=action if action in WORK_ACTIONS else 'unsupported_action',
                            classification=bucket,history_only=row.get('history_only'),
                            recorded_outcome_claim=row.get('outcome_verified'),
                            current_outcome_independently_verified=False))
    out.update(status='observed' if cursor is None else 'observed_partial',
               reason_code='record_projection_not_business_inventory',observed_at=stamp,
               visible_page_records=len(items),reported_open_projection_count=counts[0],
               reported_history_open_count=counts[1],reported_total_open_and_history=counts[2],
               next_offset=cursor,page_complete=cursor is None,counts=totals,records=records)
    out['usage']='Pablo record projection only. A successful execution claim or error is not a running business task. No current outcome, business goal, runtime health or delivery is independently established. History stays separate; missing data is unknown. Do not replay.'
    return out


class _WorkNoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None


def _current_work_page():
    # No caller/model host, task, pagination or mutation input. Existing credential and endpoint.
    key=bridge_key()
    if not key:raise ValueError('Missing existing authentication')
    host=os.environ.get('ALFRED_HOST','100.89.26.86')
    req=Request('http://'+host+':7788/work?offset=0&limit=20',
                headers={'X-Bridge-Key':key},method='GET')
    opener=build_opener(ProxyHandler({}),_WorkNoRedirect())
    with opener.open(req,timeout=6) as response:raw=response.read(WORK_RESPONSE_BOUND+1)
    if len(raw)>WORK_RESPONSE_BOUND:raise ValueError('Work response exceeds bound')
    def pairs(items):
        result={}
        for key,value in items:
            if key in result:raise ValueError('Duplicate source key')
            result[key]=value
        return result
    def invalid(_):raise ValueError('Invalid source number')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=invalid)


def read_current_work(*, loader=None, clock=time.time):
    loader=_current_work_page if loader is None else loader
    try:
        return summarize_current_work(loader(),now=clock())
    except (OSError,ValueError,TypeError,RecursionError):
        return unknown_work()


# Shared agenda uses existing panel readers; current_work above remains technical.
from pathlib import Path
from threading import RLock
import hashlib
import types

_SHARED_PANEL_DIRECTORY = Path('/home/hermes/cybergeneos/docs/cybergeneos/server')
_SHARED_PANEL_DB = Path('/home/hermes/cybergeneos-data/cgos.db')
_SHARED_PRIVATE_CONFIG = Path('/home/hermes/cybergeneos-data/approval-gateway.json')
_SHARED_PLAN = Path('/home/hermes/raporlar/JEFF_TO_JARVIS.md')
_SHARED_SOURCE_HASHES = {
    'work_agenda.py': 'ecd10c588497239e2f7b06a8aaa7fcd3490b35447a34df610d2002d1bc0c6800',
    'briefing.py': 'c98c675632fe3a44430d1468f13fb06b73f52e7c2684fa5992c513eeef91308b',
    'store.py': 'cee04dfde82c26b082c6ebae266ea7235ff9475cbce64e09802994f398ab641b',
}
_shared_sources_cache = None
_shared_sources_lock = RLock()
_SHARED_PACKAGE = '_pablo_verified_shared_agenda'


def _shared_unavailable(reason='SharedAgendaUnavailable'):
    return {'status':'unavailable','observed_at':None,'read_only':True,
            'scope':'recorded_panel_next_steps_windows_candidates_current_plan_header',
            'panel':{'known':False,'failure_class':reason},
            'marketing':{'known':False,'total_records':None,'candidate_count':None,'items':[],
                         'failure_class':reason,'outcome_verified':False},
            'plan':{'known':False,'failure_class':reason},
            'current_truth_verified':False,'semantic_goal_verified':False,
            'customer_delivery_verified':False,'owner_approval_verified':False,
            'submission_verified':False,'execution_authorized':False,'reexecution_authorized':False,
            'automatic_replay':False,'source_instruction_authority':'none'}


def _load_shared_sources():
    """Recheck all three source byte pins on every read, even with cached modules.

    Only existing source definitions are loaded. No panel app/main, adapter
    installation or Store initializer is called. Existing domain dependencies
    imported by briefing remain existing panel code, not new business rules.
    """
    global _shared_sources_cache
    with _shared_sources_lock:
        sources={}
        for name,expected in _SHARED_SOURCE_HASHES.items():
            path=_SHARED_PANEL_DIRECTORY/name
            if path.is_symlink():raise ValueError('Shared source changed')
            with path.open('rb') as handle:raw=handle.read(262145)
            if len(raw)>262144 or hashlib.sha256(raw).hexdigest()!=expected:
                raise ValueError('Shared source changed')
            sources[name]=raw
        identity=(str(_SHARED_PANEL_DIRECTORY),tuple(sorted(_SHARED_SOURCE_HASHES.items())))
        if _shared_sources_cache is not None and _shared_sources_cache[0]==identity:
            return _shared_sources_cache[1]
        # The namespace points only at the existing panel source directory.
        package=types.ModuleType(_SHARED_PACKAGE);package.__path__=[str(_SHARED_PANEL_DIRECTORY)]
        sys.modules[_SHARED_PACKAGE]=package
        modules={}
        try:
            for name in ('store.py','work_agenda.py','briefing.py'):
                short=name[:-3];qualified=_SHARED_PACKAGE+'.'+short
                module=types.ModuleType(qualified);module.__package__=_SHARED_PACKAGE
                module.__file__=str(_SHARED_PANEL_DIRECTORY/name)
                sys.modules[qualified]=module
                exec(compile(sources[name],module.__file__,'exec'),module.__dict__)
                modules[short]=module
            _shared_sources_cache=(identity,modules)
            return modules
        except Exception:
            for short in ('store','work_agenda','briefing'):sys.modules.pop(_SHARED_PACKAGE+'.'+short,None)
            _shared_sources_cache=None
            raise


def _shared_existing_key():
    """One existing private panel field. No sudo, helper, fallback or key output."""
    try:
        if _SHARED_PRIVATE_CONFIG.is_symlink():raise ValueError('Credential source unavailable')
        with _SHARED_PRIVATE_CONFIG.open('rb') as handle:raw=handle.read(16385)
        if len(raw)>16384:raise ValueError('Credential source exceeds bound')
        def unique(pairs):
            result={}
            for name,value in pairs:
                if name in result:raise ValueError('Duplicate configuration field')
                result[name]=value
            return result
        def invalid(_):raise ValueError('Invalid configuration number')
        value=json.loads(raw.decode('utf-8'),object_pairs_hook=unique,parse_constant=invalid)
        key=value.get('auth_token') if isinstance(value,dict) else None
        return key if isinstance(key,str) and key and all(ord(c)>=32 for c in key) else None
    except Exception:return None


def read_shared_agenda():
    """No caller/model arguments: same three read-only panel source boundaries.

    Source byte equality and saved stages do not establish business need, a new
    goal, permission, completed work, customer reply or delivery. Missing sources
    are unknown. Technical current_work is a separate projection and unchanged.
    """
    try:
        sources=_load_shared_sources();work=sources['work_agenda']
        # Initializing Store can migrate data and mark jobs. Never call __init__.
        store=object.__new__(sources['store'].Store);store.path=str(_SHARED_PANEL_DB)
        result=work.read(store,sources['briefing'].steps,plan=_SHARED_PLAN,
                         marketing_reader=lambda:work.read_marketing_agenda(key=_shared_existing_key()))
        if not isinstance(result,dict):raise ValueError('Invalid shared reader output')
        known=[result.get(name,{}).get('known') is True for name in ('panel','marketing','plan')]
        result.update(status='observed' if all(known) else 'observed_partial' if any(known) else 'unavailable',
            shared_source_bytes_verified=True,shared_source_sha256=dict(_SHARED_SOURCE_HASHES),
            current_truth_verified=False,semantic_goal_verified=False,customer_delivery_verified=False,
            owner_approval_verified=False,submission_verified=False,execution_authorized=False,
            reexecution_authorized=False,automatic_replay=False,source_instruction_authority='none')
        return result
    except Exception as exc:return _shared_unavailable(type(exc).__name__)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--summary', action='store_true', help='Bounded read-only current projection summary; no work or replay')
    parser.add_argument('--task-id')
    parser.add_argument('--reconcile', action='store_true')
    parser.add_argument('--offset', type=int, default=0)
    parser.add_argument('--include-history', action='store_true', help='Include quiet legacy failures; they remain unverified')
    args = parser.parse_args(argv)
    if args.summary:
        if args.task_id or args.reconcile or args.offset or args.include_history:
            parser.error('Summary cannot be combined with other modes')
        result=read_current_work()
        print(json.dumps(result,ensure_ascii=False,allow_nan=False))
        return 0 if result['status'] in ('observed','observed_partial') else 1
    if args.reconcile and not args.task_id:
        parser.error('Reconciliation requires one task-id')
    if args.task_id and not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', args.task_id):
        parser.error('Invalid task-id')
    if args.offset < 0:
        parser.error('Invalid offset')
    key = bridge_key()
    if not key:
        print('Görev bağlantısı okunamadı.', file=sys.stderr)
        return 2
    host = os.environ.get('ALFRED_HOST', '100.89.26.86')
    path = '/work/' + args.task_id if args.task_id else '/work?offset=' + str(args.offset)
    if args.include_history and not args.task_id:
        path += '&include_history=1'
    if args.reconcile:
        path += '/reconcile'
    req = Request('http://' + host + ':7788' + path,
                  data=b'{}' if args.reconcile else None,
                  headers={'X-Bridge-Key': key, 'Content-Type': 'application/json'})
    try:
        with urlopen(req, timeout=10) as response:
            result = json.load(response)
    except (OSError, ValueError):
        print('İş kaydı okunamadı; işlem tekrarlanmadı.', file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result.get('status') == 'NOT_FOUND' else 0


if __name__ == '__main__':
    raise SystemExit(main())
