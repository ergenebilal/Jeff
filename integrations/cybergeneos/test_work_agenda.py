import json
import sqlite3
from pathlib import Path
import pytest
from integrations.cybergeneos.work_agenda import read, render


class Store:
    def __init__(self):
        raise AssertionError('Agenda must never initialize or migrate live store')
    def q(self, sql, args=()):
        with self.lock:
            return [dict(row) for row in self.db.execute(sql, args).fetchall()]
    def leads(self):
        return self.q('SELECT * FROM leads')


def fixture(tmp_path):
    path=tmp_path/'panel.db'
    with sqlite3.connect(path) as db:
        db.executescript("CREATE TABLE leads(id,name);CREATE TABLE jobs(title,status,created_at);INSERT INTO leads VALUES('a','Alpha'),('b','Beta');INSERT INTO jobs VALUES('Private draft','done',1),('Existing scan','running',2);")
    store=object.__new__(Store);store.path=str(path)
    plan=tmp_path/'plan.md';plan.write_text('**Sıradaki adım:** Ses bağlamını doğrula.\n',encoding='utf-8')
    return store,plan,path


def test_actual_panel_order_and_steps_without_constructor_or_worker(tmp_path):
    store,plan,path=fixture(tmp_path);before=path.read_bytes()
    def steps(view,leads):
        assert view is not store
        return {'a':{'list':'sira','rank':4,'text':'Taslağı incele'},'b':{'list':'sira','rank':0,'text':'Gelen yanıtı oku'}}
    result=read(store,steps,plan);answer=render(result)
    assert result['panel']['known'] and result['panel']['actionable_count']==2
    assert result['panel']['items'][0]['name']=='Beta'
    assert answer.index('Gelen yanıtı oku')<answer.index('Taslağı incele')
    assert 'Private draft' not in answer and 'tamamlandığını doğrulamaz' in answer
    assert 'Ses bağlamını doğrula' in answer and 'Pablo' not in answer
    assert path.read_bytes()==before


def test_accidental_write_is_denied_and_not_converted_to_empty_agenda(tmp_path):
    store,plan,path=fixture(tmp_path);before=path.read_bytes()
    def malicious(view,leads):
        view.db.execute('DELETE FROM leads')
    result=read(store,malicious,plan)
    assert not result['panel']['known'] and path.read_bytes()==before
    assert 'erişemiyorum' in render(result) and 'Ses bağlamını doğrula' in render(result)
    assert 'kayıt görünmüyor' not in render(result)


def test_missing_database_not_created_and_plan_still_useful(tmp_path):
    store=object.__new__(Store);store.path=str(tmp_path/'missing')
    plan=tmp_path/'plan';plan.write_text('**Sıradaki adım:** Görüşme bağlamını kontrol et.',encoding='utf-8')
    result=read(store,lambda *_:pytest.fail('Missing source cannot call steps'),plan)
    assert not result['panel']['known'] and result['plan']['known']
    assert not Path(store.path).exists() and 'Görüşme bağlamını kontrol et' in render(result)


def test_known_empty_is_scoped_not_global_no_work(tmp_path):
    store,plan,path=fixture(tmp_path)
    result=read(store,lambda *_:{'a':{'list':'bekle'},'b':{'list':'arsiv'}},plan)
    assert result['panel']['known'] and result['panel']['actionable_count']==0
    assert 'Panelde senden bir adım bekleyen kayıt görünmüyor.' in render(result)
    assert 'Jarvis planında' in render(result) and 'iş yok' not in render(result)


def test_unknown_sources_never_claim_nothing_new(tmp_path):
    store=object.__new__(Store);store.path=str(tmp_path/'missing')
    answer=render(read(store,lambda *_:None,tmp_path/'missing-plan'))
    assert 'sana iş yok diyemem' in answer and 'yeni bir şey yok' not in answer


def test_no_private_contact_or_draft_fields_escape(tmp_path):
    store,plan,path=fixture(tmp_path)
    result=read(store,lambda *_:{'a':{'list':'sira','text':'Taslağı incele','email':'secret@example.com'},'b':{'list':'bekle'}},plan)
    assert 'secret@example.com' not in json.dumps(result)
