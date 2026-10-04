import json
import sqlite3
from types import SimpleNamespace
import pytest
from scripts.jarvis_snapshot import snapshot,render
from integrations.cybergeneos.jarvis_adapter import install,patch


def test_read_only_shared_record_preserves_unknown_and_expired(tmp_path):
    path=tmp_path/'ledger'
    with sqlite3.connect(path) as db:db.executescript("CREATE TABLE approval_records(approval_id,status,expires_at,archived_at,created_at);INSERT INTO approval_records VALUES('expired','pending',90,NULL,1);INSERT INTO approval_records VALUES('current','pending',200,NULL,2);")
    before=path.read_bytes()
    data=snapshot(path,lambda:{'open_count':1,'items':[{'request_id':'unknown','status':'OUTCOME_UNKNOWN','outcome_verified':False,'params':'private fixture'}],'next_offset':None},100)
    assert data['approvals']['pending']==1 and data['approvals']['expired_visible']==1
    assert not data['work']['items'][0]['outcome_verified'] and 'private' not in json.dumps(data)
    assert 'doğrulanmadı' in render(data) and path.read_bytes()==before


def test_missing_sources_never_render_zero(tmp_path):
    data=snapshot(tmp_path/'missing',lambda:(_ for _ in ()).throw(OSError()),100)
    assert data['work']['open'] is None and data['approvals']['pending'] is None
    assert 'okunamadı' in render(data) and not (tmp_path/'missing').exists()


def test_partial_list_and_approved_not_success(tmp_path):
    data=snapshot(tmp_path/'missing',lambda:{'open_count':2,'items':[{'request_id':'approved','status':'APPROVED'}],'next_offset':1},100)
    assert not data['work']['complete_list'] and not data['work']['items'][0]['outcome_verified']
    assert 'liste kısmi' in render(data)


def test_panel_state_chat_and_voice_share_same_reader_without_model_call():
    calls=[];sample={'version':1,'work':{'open':13},'approvals':{'pending':0}}
    def reader():calls.append('read');return sample
    def model(*args):raise AssertionError('Status cannot require a model')
    app=SimpleNamespace(build_state=lambda:{'business':'unchanged'},briefing=SimpleNamespace(jeff_context=lambda store:'business context'),jeff=SimpleNamespace(stream_reply=model,VOICE_RULES='voice',FALLBACK_SYSTEM='fallback'))
    install(app,reader,lambda data:'same canonical status')
    assert app.build_state()=={'business':'unchanged','jarvis':sample}
    assert json.dumps(sample) in app.briefing.jeff_context(None)
    assert list(app.jeff.stream_reply('/durum','context'))==['same canonical status'] and len(calls)==3
    install(app,reader,lambda data:'changed');assert app.jeff.VOICE_RULES.count('known false')==1


def test_patch_requires_exact_anchor_and_is_idempotent():
    original='    install_approval_adapter(sys.modules[__name__])\n'
    assert patch(patch(original))==patch(original)
    with pytest.raises(ValueError):patch('changed app')


def test_panel_uses_existing_agent_key_without_privileged_shell(tmp_path,monkeypatch):
    from scripts import jarvis_snapshot
    (tmp_path/'approval-gateway.json').write_text(json.dumps({'auth_token':'fixture-agent','approval_decision_key':'fixture-owner'}))
    observed=[]
    def work(key=None):
        assert key=='fixture-agent';observed.append(key)
        return {'open_count':0,'items':[],'next_offset':None,'automatic_replay':False}
    monkeypatch.setattr(jarvis_snapshot,'read_work',work)
    app=SimpleNamespace(DATA=tmp_path,build_state=lambda:{},briefing=SimpleNamespace(jeff_context=lambda store:''),jeff=SimpleNamespace(stream_reply=lambda *a:iter(()),VOICE_RULES='',FALLBACK_SYSTEM=''))
    install(app)
    result=app.build_state()['jarvis']
    assert result['work']['known'] and result['work']['open']==0 and observed==['fixture-agent']
    assert 'fixture-agent' not in json.dumps(result) and 'fixture-owner' not in json.dumps(result)
