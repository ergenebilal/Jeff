import io
import json
import tarfile
from pathlib import Path

from scripts import jeff_backup as jb


def manifests(tmp_path, db=None, etc=None):
    for area, value in [('db', db or {}), ('etc', etc or {})]:
        (tmp_path / area).mkdir(exist_ok=True)
        (tmp_path / area / 'MANIFEST.json').write_text(json.dumps(value))


def test_all_sources_checked_before_any_restore(tmp_path):
    stage=tmp_path/'stage'; stage.mkdir(); manifests(stage, {'first.db':'/data/first.db', 'missing.db':'/data/missing.db'})
    (stage/'db/first.db').write_bytes(b'first')
    target=tmp_path/'root'
    assert jb.restore(stage,target,apply=True,log=lambda _:None)==1
    assert not target.exists()


def test_manifest_cannot_escape_root_or_source(tmp_path):
    for name,original in [('../escape','/safe'), ('ok.db','/safe/../../escape'), ('ok.db',r'C:\safe\..\escape')]:
        stage=tmp_path/('stage'+str(len(list(tmp_path.iterdir()))));stage.mkdir();manifests(stage,{name:original})
        (stage/'db/ok.db').write_bytes(b'x')
        assert jb.restore(stage,tmp_path/'root',apply=True,log=lambda _:None)==1
    assert not (tmp_path/'root').exists()


def test_core_archive_hash_detects_same_name_wrong_code(tmp_path):
    archive=tmp_path/'a.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        for name,data in [('etc/CORE-SOURCES.json',json.dumps({'home/hermes/code.py':'0'*64}).encode()),('home/hermes/code.py',b'wrong code')]:
            info=tarfile.TarInfo(name);info.size=len(data);tar.addfile(info,io.BytesIO(data))
    assert jb.verify_core_sources(archive)==['core source hash mismatch: home/hermes/code.py']


def test_backups_include_active_repo_beyin_state_and_runtime(tmp_path):
    roots=jb.trees(tmp_path,opt_trees=())
    assert tmp_path/'jeff_repo' in roots
    assert tmp_path/'.local/share/beyin-v3' in roots
    assert tmp_path/'jeff-v0.21.5/site' in roots
