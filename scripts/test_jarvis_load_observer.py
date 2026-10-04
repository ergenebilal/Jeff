import json
import sqlite3
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
