"""Content-free seven-day observation. Unknown human effort is never zero."""
import argparse
from collections import Counter
import json
import math
import os
from pathlib import Path
import sqlite3
import time
from urllib.request import Request,urlopen

DURATION=7*86400


def db_count(path,query,params=()):
    try:
        with sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True) as db:
            return {'known':True,'value':db.execute(query,params).fetchone()[0]}
    except Exception as exc:return {'known':False,'value':None,'failure_class':type(exc).__name__}


def collect(bridge,attention,now,work_reader):
    result={
        'pending_approvals':db_count(bridge,"SELECT count(*) FROM approval_records WHERE status='pending' AND archived_at IS NULL AND expires_at>?",(now,)),
        'expired_visible_approvals':db_count(bridge,"SELECT count(*) FROM approval_records WHERE status IN ('pending','approved') AND expires_at<=? AND archived_at IS NULL",(now,)),
        'approval_expirations_total':db_count(bridge,"SELECT count(*) FROM approval_audit WHERE event='expired'"),
        'server_notifications_sent_total':db_count(attention,"SELECT count(*) FROM attention_outbox WHERE status='sent'"),
        'server_notifications_unknown_total':db_count(attention,"SELECT count(*) FROM attention_outbox WHERE status IN ('sending','delivery_unknown')"),
    }
    try:
        work=work_reader()
        if type(work.get('open_count')) is not int or work['open_count']<0 or not isinstance(work.get('items'),list):raise ValueError('Invalid work record')
        result['open_work']={'known':True,'value':work['open_count']}
        result['sampled_work_statuses']=dict(Counter(i['status'] for i in work['items']))
        result['all_open_work_statuses_sampled']=work.get('next_offset') is None and len(work['items'])==work['open_count']
        result['automatic_replay']=work.get('automatic_replay')
    except Exception as exc:
        result['open_work']={'known':False,'value':None,'failure_class':type(exc).__name__}
        result['sampled_work_statuses']={};result['all_open_work_statuses_sampled']=False
    result['manual_checks']=None;result['repeated_explanations']=None;result['unnecessary_notifications']=None
    result['human_effort_source']='not_reported';result['windows_notification_coverage']='not_measured'
    return result


def read_work():
    from scripts.pablo_dispatch import bridge_key
    key=bridge_key()
    if not key:raise RuntimeError('Work credential unavailable')
    req=Request('http://100.89.26.86:7788/work',headers={'X-Bridge-Key':key})
    with urlopen(req,timeout=10) as resp:return json.load(resp)


def assessment(started,now,observations):
    if (type(started) not in (int,float) or type(now) not in (int,float)
            or not math.isfinite(started) or not math.isfinite(now)
            or not 0<=started<=now):raise ValueError('Invalid observation start')
    relevant=[];invalid=0;outside=0
    for observation in observations:
        stamp=observation.get('observed_at') if isinstance(observation,dict) else None
        if type(stamp) not in (int,float) or not math.isfinite(stamp):
            invalid+=1;continue
        if started<=stamp<=now and stamp<started+DURATION:
            relevant.append(observation)
        else:outside+=1
    relevant.sort(key=lambda o:o['observed_at'])
    automatic=[o for o in relevant if o.get('kind')=='automatic']
    days={int((o['observed_at']-started)//86400) for o in relevant if o.get('kind')=='automatic'}
    elapsed=now-started
    human=[o for o in relevant if o.get('kind')=='owner_report']
    completed=min(7,int(elapsed//86400))
    reached=min(7,int(elapsed//86400)+1)
    sources={}
    for name in ('pending_approvals','expired_visible_approvals','approval_expirations_total',
                 'server_notifications_sent_total','server_notifications_unknown_total','open_work'):
        known=0;known_days=set();failures=Counter();latest=None;last_known=None
        for observation in automatic:
            metrics=observation.get('metrics')
            metric=metrics.get(name) if isinstance(metrics,dict) else None
            good=(isinstance(metric,dict) and metric.get('known') is True
                  and type(metric.get('value')) is int and metric['value']>=0)
            latest={'observed_at':observation['observed_at'],'known':good,
                    'value':metric['value'] if good else None}
            if good:
                known+=1;known_days.add(int((observation['observed_at']-started)//86400))
                last_known=dict(latest)
            else:
                reason=metric.get('failure_class') if isinstance(metric,dict) else None
                # Only classifier names, never arbitrary payloads or exception text.
                reason=reason if isinstance(reason,str) and reason.isidentifier() and len(reason)<=64 else 'MissingOrInvalidMetric'
                failures[reason]+=1
        sources[name]={'known_samples':known,'unknown_samples':len(automatic)-known,
                       'failure_classes':dict(failures),'days_with_known_data':sorted(known_days),
                       'latest_sample':latest,'last_known_sample':last_known,
                       'all_recorded_samples_known':bool(automatic) and known==len(automatic)}
    complete_work=sum(isinstance(o.get('metrics'),dict)
                      and o['metrics'].get('all_open_work_statuses_sampled') is True
                      and isinstance(o['metrics'].get('open_work'),dict)
                      and o['metrics']['open_work'].get('known') is True
                      and type(o['metrics']['open_work'].get('value')) is int
                      and o['metrics']['open_work']['value']>=0 for o in automatic)
    return {'started_at':started,'due_at':started+DURATION,'elapsed_seconds':elapsed,
            'seven_days_elapsed':elapsed>=DURATION,'days_with_observations':len(days),
            'completed_window_days':completed,'window_day_indices_with_observations':sorted(days),
            'completed_days_without_observations':sorted(set(range(completed))-days),
            'reached_days_without_observations':sorted(set(range(reached))-days),
            'days_not_started':list(range(reached,7)),
            'automatic_observation_samples':len(automatic),'sources':sources,
            'work_samples_with_complete_status_list':complete_work,
            'work_samples_without_complete_status_list':len(automatic)-complete_work,
            'invalid_timestamp_records':invalid,'records_outside_acceptance_window':outside,
            'measurement_scope':'Scheduled point observations, not continuous availability, unique verified work outcomes or human effort.',
            'owner_reports':len(human),'pre_change_human_baseline_known':False,
            'burden_reduction_proven':False,'reason':'Real elapsed time, comparable owner baseline and successful work outcomes are required; automated counts alone do not prove reduced burden.'}


def write_observation(directory,observation,now):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    start=directory/'start.json'
    if not start.exists():
        with start.open('x',encoding='utf-8') as handle:json.dump({'version':1,'started_at':now,'due_at':now+DURATION,'chosen_burdens':['manual_system_check','expired_approval_cleanup','unfinished_work_followup'],'scope':'infrastructure_and_jarvis','before_change_baseline':None},handle,indent=2)
    started=json.loads(start.read_text())['started_at']
    log=directory/'observations.jsonl'
    line={'version':1,'observed_at':now,**observation}
    with log.open('a',encoding='utf-8') as handle:handle.write(json.dumps(line,separators=(',',':'))+'\n')
    observations=[json.loads(line) for line in log.read_text().splitlines()]
    result=assessment(started,now,observations);temp=directory/'summary.tmp';temp.write_text(json.dumps(result,indent=2));temp.replace(directory/'summary.json')
    if os.name!='nt':
        directory.chmod(0o700)
        for p in (start,log,directory/'summary.json'):p.chmod(0o600)
    return result


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--directory',default='/home/hermes/jeff-artifacts/jarvis-observation')
    ap.add_argument('--bridge-db',default='/home/hermes/jeff2/bridge/bridge.db');ap.add_argument('--attention-db',default='/home/hermes/logs/attention.db')
    ap.add_argument('--owner-counts',nargs=3,type=int,metavar=('MANUAL_CHECKS','REPEATS','UNNECESSARY_NOTIFICATIONS'))
    args=ap.parse_args(argv);now=time.time()
    if args.owner_counts is not None:
        if any(n<0 for n in args.owner_counts):ap.error('Counts cannot be negative')
        data={'kind':'owner_report','manual_checks':args.owner_counts[0],'repeated_explanations':args.owner_counts[1],'unnecessary_notifications':args.owner_counts[2],'human_effort_source':'explicit_owner_report','period':'since_previous_owner_report_or_observation_start'}
    else:data={'kind':'automatic','metrics':collect(args.bridge_db,args.attention_db,now,read_work)}
    summary=write_observation(args.directory,data,now);print(json.dumps({'observation_recorded':True,**summary}));return 0


if __name__=='__main__':raise SystemExit(main())
