import json
import sqlite3
import os
import pytest
from pablo.pablo_recovery import CORE,snapshot,restore,validate


def fixture(tmp_path):
    live=tmp_path/'live';live.mkdir()
    for name in CORE:
        if name.endswith('.sqlite3'):
            with sqlite3.connect(live/name) as db:
                db.execute('CREATE TABLE actions(id TEXT PRIMARY KEY,status TEXT)');db.execute("INSERT INTO actions VALUES('known','OUTCOME_UNKNOWN')")
        else:(live/name).write_text(json.dumps({'commit':'fixture'}) if name=='deployment.json' else 'fixture')
    return live


def test_consistent_unknown_record_restored_without_workers_or_overwrite(tmp_path):
    live=fixture(tmp_path);snap=tmp_path/'snapshot';snapshot(live,snap,collect_packages=False)
    root=tmp_path/'root';result=restore(snap,root)
    assert result['verified'] and not result['workers_started']
    with sqlite3.connect(root/'task-journal.sqlite3') as db:assert db.execute('SELECT status FROM actions').fetchone()[0]=='OUTCOME_UNKNOWN'
    with pytest.raises(FileExistsError):restore(snap,root)


def test_tampered_bytes_rejected_before_any_destination(tmp_path):
    snap=tmp_path/'snapshot';snapshot(fixture(tmp_path),snap,collect_packages=False)
    (snap/'files/config.json').write_text('changed')
    with pytest.raises(ValueError):restore(snap,tmp_path/'root')
    assert not (tmp_path/'root').exists()


def test_manifest_traversal_and_omitted_database_are_rejected(tmp_path):
    snap=tmp_path/'snapshot';snapshot(fixture(tmp_path),snap,collect_packages=False)
    path=snap/'manifest.json';original=json.loads(path.read_text());unsafe=json.loads(path.read_text())
    unsafe['entries'][0]['path']='files/../../escape';path.write_text(json.dumps(unsafe))
    with pytest.raises(ValueError):validate(snap)
    original['entries']=[e for e in original['entries'] if e['path']!='files/task-journal.sqlite3'];path.write_text(json.dumps(original))
    with pytest.raises(ValueError):validate(snap)


def test_snapshot_missing_live_database_cannot_pass(tmp_path):
    live=fixture(tmp_path);(live/'intent_guard.sqlite3').unlink()
    with pytest.raises(FileNotFoundError):snapshot(live,tmp_path/'snapshot',collect_packages=False)
    assert not (tmp_path/'snapshot').exists()


def test_new_runtime_policy_required_but_previous_runtime_restorable(tmp_path):
    live=fixture(tmp_path)
    snapshot(live,tmp_path/'previous',collect_packages=False)
    assert restore(tmp_path/'previous',tmp_path/'previous-root')['verified']
    (live/'hermes_node.py').write_text('from pablo_capability_policy import admission')
    with pytest.raises(ValueError):snapshot(live,tmp_path/'missing-policy',collect_packages=False)
    (live/'pablo_capability_policy.py').write_text('def admission(name): return {}')
    snapshot(live,tmp_path/'current',collect_packages=False)
    assert restore(tmp_path/'current',tmp_path/'current-root')['verified']


@pytest.mark.skipif(os.name=='nt',reason='POSIX permission boundary')
def test_nested_private_directories_and_restored_files(tmp_path):
    live=fixture(tmp_path);draft=live/'verified-drafts'/'child'
    draft.mkdir(parents=True);(draft/'result.txt').write_text('private fixture')
    snap=tmp_path/'snapshot';snapshot(live,snap,collect_packages=False)
    root=tmp_path/'root';restore(snap,root)
    for base in (snap,root):
        assert base.stat().st_mode&0o777==0o700
        assert all(p.stat().st_mode&0o077==0 for p in base.rglob('*'))
