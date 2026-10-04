import json
import hashlib
import pytest
from scripts.pablo_drift_monitor import LOADED,compare_sources,read_report


def source(tmp_path):
    files={}
    for name in LOADED:
        (tmp_path/name).write_bytes(b'fixture\r\n');files[name]=hashlib.sha256(b'fixture\n').hexdigest()
    expected={'commit':'a'*40,'files':files};ping={'ok':True,'result':'pong','loaded_source_sha256':dict(files)}
    return expected,ping


def test_loaded_old_source_detected_even_with_clean_disk(tmp_path):
    expected,ping=source(tmp_path);assert compare_sources(tmp_path,expected,ping)['ok']
    ping['loaded_source_sha256'][LOADED[0]]='0'*64
    result=compare_sources(tmp_path,expected,ping);assert not result['ok'] and result['runtime_changed']==[LOADED[0]]


def test_missing_extra_changed_and_private_exclusion(tmp_path):
    expected,ping=source(tmp_path)
    (tmp_path/LOADED[0]).unlink();(tmp_path/LOADED[1]).write_text('changed');(tmp_path/'extra.py').write_text('extra')
    (tmp_path/'pablo_human_behavior.py').write_text('private');(tmp_path/'config.json').write_text('secret fixture')
    result=compare_sources(tmp_path,expected,ping)
    assert not result['ok'] and result['missing']==[LOADED[0]] and result['changed']==[LOADED[1]] and result['extra']==['extra.py']


def test_absent_runtime_and_incomplete_manifest_cannot_pass(tmp_path):
    expected,ping=source(tmp_path)
    with pytest.raises(ValueError):compare_sources(tmp_path,expected,{'ok':True})
    expected['files'].pop(LOADED[0])
    with pytest.raises(ValueError):compare_sources(tmp_path,expected,ping)


def test_stale_future_and_failed_observation_not_pass(tmp_path):
    expected,ping=source(tmp_path);result=compare_sources(tmp_path,expected,ping)
    path=tmp_path/'report';result.update(version=1,observed_at=100)
    path.write_text(json.dumps(result));assert read_report(path,now=100)[0]
    assert not read_report(path,now=99)[0] and not read_report(path,now=4601)[0]
    result['ok']=False;path.write_text(json.dumps(result));assert not read_report(path,now=100)[0]


def test_contradictory_success_not_pass(tmp_path):
    expected,ping=source(tmp_path);result=compare_sources(tmp_path,expected,ping)
    result.update(version=1,observed_at=100,missing=['critical.py'])
    path=tmp_path/'report';path.write_text(json.dumps(result));assert not read_report(path,now=100)[0]
