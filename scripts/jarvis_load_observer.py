"""Content-free seven-day observation. Unknown human effort is never zero."""
import argparse
from collections import Counter
import json
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
    if type(started) not in (int,float) or not 0<=started<=now:raise ValueError('Invalid observation start')
    relevant=[o for o in observations if started<=o.get('observed_at',-1)<=now]
    days={int((o['observed_at']-started)//86400) for o in relevant if o.get('kind')=='automatic'}
    elapsed=now-started
    human=[o for o in relevant if o.get('kind')=='owner_report']
    return {'started_at':started,'due_at':started+DURATION,'elapsed_seconds':elapsed,
            'seven_days_elapsed':elapsed>=DURATION,'days_with_observations':len(days),
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
