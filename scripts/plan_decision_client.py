"""Staged server consumer of the original-parent-bound authenticated plan read.

Requires the caller original input digest, never derived from the loaded result.
Never constructs a criterion from model text or replays a job. No integration
into the live agent yet. Successful transport is not semantic completion.
"""
import argparse
import math
import re
import time
from scripts.pablo_outcome_evidence import _load_authenticated,valid_id,valid_sha

FIELDS={'schema_version','request_id','status','criterion_source','input_digest',
 'recorded_plan_status','expected_steps','observed_steps','matched_steps','mismatched_steps',
 'unavailable_steps','deferred_steps','all_step_bytes_matched_during_read_window','observations',
 'observed_from','observed_until','atomic_across_files','semantic_goal_verified','execution_verified',
 'customer_delivery_verified','journal_status_updated','read_only','execution_authorized',
 'reexecution_authorized','reason'}


def validate(value,rid,now):
    if (not isinstance(value,dict) or set(value)!=FIELDS or type(value['schema_version']) is not int
            or value['schema_version']!=1 or value['request_id']!=rid
            or value['criterion_source']!='stored_original_parent_plan'
            or value['read_only'] is not True
            or any(value[k] is not False for k in ('atomic_across_files','semantic_goal_verified','execution_verified',
               'customer_delivery_verified','journal_status_updated','execution_authorized','reexecution_authorized'))
            or type(value['all_step_bytes_matched_during_read_window']) is not bool
            or value['status'] not in {'matched','mismatch','partial','cancelled','unavailable','unsupported'}):
        raise ValueError('Unsupported plan observation')
    counts=[value[k] for k in ('observed_steps','matched_steps','mismatched_steps','unavailable_steps','deferred_steps')]
    if any(type(n) is not int or not 0<=n<=20 for n in counts):raise ValueError('Invalid counts')
    if not isinstance(value['observations'],list) or len(value['observations'])>20:raise ValueError('Unbounded observations')
    if value['status'] in {'matched','mismatch','partial'}:
        expected=value['expected_steps'];start=value['observed_from'];end=value['observed_until']
        if (type(expected) is not int or not 1<=expected<=20 or sum(counts[1:])!=expected
                or len(value['observations'])!=value['observed_steps'] or not valid_sha(value['input_digest'])
                or type(start) not in (int,float) or type(end) not in (int,float)
                or not math.isfinite(start) or not math.isfinite(end) or not 0<start<=end<=now
                or now-end>300):raise ValueError('Incomplete or stale observation')
        ids=set();seen={'matched':0,'mismatch':0,'unavailable':0,'deferred':0}
        for row in value['observations']:
            if (not isinstance(row,dict) or set(row)!={'request_id','status','observed_at','file_bytes_matched'}
                    or not valid_id(row['request_id']) or row['request_id'] in ids
                    or row['status'] not in seen or type(row['file_bytes_matched']) is not bool
                    or row['file_bytes_matched']!=(row['status']=='matched')):raise ValueError('Invalid child observation')
            if row['status'] in {'matched','mismatch'}:
                stamp=row['observed_at']
                if type(stamp) not in (int,float) or not math.isfinite(stamp) or not start<=stamp<=end:raise ValueError('Invalid child time')
            ids.add(row['request_id']);seen[row['status']]+=1
        if (seen['matched']!=value['matched_steps'] or seen['mismatch']!=value['mismatched_steps']
                or seen['deferred']!=value['deferred_steps'] or seen['unavailable']>value['unavailable_steps']):raise ValueError('Conflicting count')
        match=value['matched_steps']==expected
        if value['all_step_bytes_matched_during_read_window']!=match or (value['status']=='matched')!=match:
            raise ValueError('Contradictory success')
        if (value['status']=='mismatch')!=(value['mismatched_steps']>0):raise ValueError('Contradictory mismatch')
    elif value['all_step_bytes_matched_during_read_window'] or value['observations']:
        raise ValueError('Unsupported status cannot accept a result')
    return value


def read_plan(rid,*,input_digest=None,loader=None,clock=time.time):
    if not valid_id(rid):raise ValueError('Invalid plan identity')
    out=dict(request_id=rid,status='unavailable',new_task_outcome='unknown',
             original_input_binding_matched=False,reason_code='observation_unavailable',
             all_step_bytes_matched_during_read_window=False,semantic_goal_verified=False,
             execution_verified=False,customer_delivery_verified=False,read_only=True,
             execution_authorized=False,reexecution_authorized=False,
             scope='Existing original bounded private draft plan only; per-step times, not atomic or semantic completion')
    if input_digest is None:
        out.update(status='criterion_required',reason_code='original_input_required')
        return out
    if not valid_sha(input_digest):raise ValueError('Invalid original plan input digest')
    loader=_load_authenticated if loader is None else loader
    try:
        value=validate(loader(rid,'/plan-observation'),rid,clock())
        supported=value['status'] in {'matched','mismatch','partial','cancelled'}
        if supported and value['input_digest']!=input_digest:
            out.update(status='binding_mismatch',reason_code='original_input_mismatch')
            return out
        out.update(original_input_binding_matched=supported,
                   reason_code='original_input_bound' if supported else 'observation_unavailable')
        out.update(status='observed' if value['status'] in {'matched','mismatch','partial','cancelled'} else value['status'],
                   new_task_outcome=value['status'],all_step_bytes_matched_during_read_window=value['all_step_bytes_matched_during_read_window'],
                   expected_steps=value['expected_steps'],observed_steps=value['observed_steps'],matched_steps=value['matched_steps'],
                   mismatched_steps=value['mismatched_steps'],unavailable_steps=value['unavailable_steps'],deferred_steps=value['deferred_steps'])
    except (OSError,ValueError,TypeError,RecursionError):pass
    return out


if __name__=='__main__':
    import json
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--plan-id',required=True);parser.add_argument('--input-digest',required=True)
    args=parser.parse_args();v=read_plan(args.plan_id,input_digest=args.input_digest);print(json.dumps(v,allow_nan=False));raise SystemExit(0 if v['status']=='observed' else 1)
