import json
import sqlite3
import pytest
from scripts.jarvis_load_observer import collect,assessment,write_observation,DURATION


def test_missing_source_and_unreported_effort_never_zero(tmp_path):
    data=collect(tmp_path/'missing',tmp_path/'missing2',100,lambda:(_ for _ in ()).throw(OSError()))
    assert data['pending_approvals']['value'] is None and not data['pending_approvals']['known']
    assert data['open_work']['value'] is None
    assert data['manual_checks'] is None and data['unnecessary_notifications'] is None
    assert not (tmp_path/'missing').exists()


def test_metadata_only_and_partial_work_scope(tmp_path):
    data=collect(tmp_path/'missing',tmp_path/'missing2',100,lambda:{'open_count':2,'items':[{'status':'OUTCOME_UNKNOWN','params':'private fixture','id':'private identifier'}],'next_offset':1,'automatic_replay':False})
    assert data['sampled_work_statuses']=={'OUTCOME_UNKNOWN':1} and not data['all_open_work_statuses_sampled']
    assert 'private' not in json.dumps(data)


def test_no_elapsed_time_or_owner_report_can_forge_seven_days():
    observations=[{'kind':'automatic','observed_at':100},{'kind':'owner_report','observed_at':101}]
    data=assessment(100,101,observations)
    assert not data['seven_days_elapsed'] and not data['burden_reduction_proven']
    data=assessment(100,100+DURATION,observations)
    assert data['seven_days_elapsed'] and data['days_with_observations']==1 and not data['burden_reduction_proven']


def test_append_preserves_start_and_previous_records(tmp_path):
    root=tmp_path/'observation';first=write_observation(root,{'kind':'automatic','metrics':{}},100)
    second=write_observation(root,{'kind':'automatic','metrics':{}},200)
    assert first['started_at']==second['started_at']==100 and second['elapsed_seconds']==100
    assert len((root/'observations.jsonl').read_text().splitlines())==2


def test_expired_approval_and_unknown_delivery_remain_visible(tmp_path):
    bridge=tmp_path/'bridge';attention=tmp_path/'attention'
    with sqlite3.connect(bridge) as db:
        db.executescript("CREATE TABLE approval_records(status,archived_at,expires_at);INSERT INTO approval_records VALUES('pending',NULL,90);CREATE TABLE approval_audit(event);INSERT INTO approval_audit VALUES('expired');")
    with sqlite3.connect(attention) as db:
        db.executescript("CREATE TABLE attention_outbox(status);INSERT INTO attention_outbox VALUES('delivery_unknown');")
    data=collect(bridge,attention,100,lambda:{'open_count':0,'items':[],'next_offset':None})
    assert data['expired_visible_approvals']['value']==1 and data['server_notifications_unknown_total']['value']==1
    assert data['approval_expirations_total']['value']==1


def test_completed_day_gaps_and_post_window_data_are_not_hidden():
    rows=[{'kind':'automatic','observed_at':100},
          {'kind':'automatic','observed_at':100+2*86400},
          {'kind':'automatic','observed_at':100+DURATION}]
    result=assessment(100,100+DURATION+3600,rows)
    assert result['window_day_indices_with_observations']==[0,2]
    assert result['completed_days_without_observations']==[1,3,4,5,6]
    assert result['records_outside_acceptance_window']==1
    assert not result['burden_reduction_proven']


def test_not_started_days_are_distinct_from_missing_completed_days():
    result=assessment(100,100+86400+1,[{'kind':'automatic','observed_at':100+86400}])
    assert result['completed_days_without_observations']==[0]
    assert result['reached_days_without_observations']==[0]
    assert result['days_not_started']==[2,3,4,5,6]


def test_previous_work_success_does_not_replace_latest_missing_value():
    rows=[{'kind':'automatic','observed_at':110,'metrics':{'open_work':{'known':True,'value':16}}},
          {'kind':'automatic','observed_at':120,'metrics':{'open_work':{'known':False,'value':None,'failure_class':'URLError'}}}]
    work=assessment(100,130,rows)['sources']['open_work']
    assert work['known_samples']==1 and work['unknown_samples']==1
    assert work['latest_sample']=={'observed_at':120,'known':False,'value':None}
    assert work['last_known_sample']['observed_at']==110 and work['last_known_sample']['value']==16
    assert work['failure_classes']=={'URLError':1} and not work['all_recorded_samples_known']


def test_boolean_negative_or_missing_counts_are_unknown_and_payload_is_not_copied():
    rows=[{'kind':'automatic','observed_at':110+i,'metrics':{'open_work':metric}}
          for i,metric in enumerate([{'known':True,'value':True},
              {'known':True,'value':-1},{'known':True,'value':None},
              {'known':False,'value':0,'failure_class':'private fixture contents'}])]
    result=assessment(100,120,rows);work=result['sources']['open_work']
    assert work['known_samples']==0 and work['unknown_samples']==4
    assert work['last_known_sample'] is None and work['latest_sample']['value'] is None
    assert 'private fixture' not in json.dumps(result)


def test_real_zero_and_partial_work_sample_keep_their_scope():
    rows=[{'kind':'automatic','observed_at':110,'metrics':{'open_work':{'known':True,'value':0},'all_open_work_statuses_sampled':True}},
          {'kind':'automatic','observed_at':120,'metrics':{'open_work':{'known':True,'value':2},'all_open_work_statuses_sampled':False}}]
    result=assessment(100,130,rows)
    assert result['sources']['open_work']['known_samples']==2
    assert result['work_samples_with_complete_status_list']==1
    assert result['work_samples_without_complete_status_list']==1
    assert not result['burden_reduction_proven']


def test_unordered_future_and_invalid_timestamps_do_not_fake_recent_success():
    rows=[{'kind':'automatic','observed_at':130,'metrics':{'open_work':{'known':True,'value':3}}},
          {'kind':'automatic','observed_at':120,'metrics':{'open_work':{'known':False,'value':None}}},
          {'kind':'automatic','observed_at':float('nan')},None,
          {'kind':'automatic','observed_at':True}]
    result=assessment(100,125,rows)
    assert result['invalid_timestamp_records']==3 and result['records_outside_acceptance_window']==1
    assert result['sources']['open_work']['latest_sample']['value'] is None


@pytest.mark.parametrize('started,now',[(True,100),(100,float('inf')),(float('nan'),100)])
def test_invalid_clock_is_rejected(started,now):
    with pytest.raises(ValueError):assessment(started,now,[])


def test_new_summary_preserves_original_start_and_prior_log_bytes(tmp_path):
    root=tmp_path/'observation'
    write_observation(root,{'kind':'automatic','metrics':{'open_work':{'known':False,'value':None}}},100)
    start=(root/'start.json').read_bytes();prefix=(root/'observations.jsonl').read_bytes()
    result=write_observation(root,{'kind':'automatic','metrics':{'open_work':{'known':True,'value':1}}},200)
    assert (root/'start.json').read_bytes()==start
    assert (root/'observations.jsonl').read_bytes().startswith(prefix)
    assert result['sources']['open_work']['unknown_samples']==1
    assert not result['pre_change_human_baseline_known'] and not result['burden_reduction_proven']
