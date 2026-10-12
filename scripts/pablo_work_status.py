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
