"""CI checks of the real workflow's persistence boundary, with a small SQLite panel adapter.

Full panel, HTTP, source and model adapters are exercised by the packaged
test_marketing.py in the separate cybergene-web checkout (not bundled wholesale).
"""
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import threading
import types
import unittest


def load_workflow():
    package = types.ModuleType('_cgos_marketing_fixture')
    package.__path__ = []
    sys.modules[package.__name__] = package
    for name in ('analysis', 'contact', 'outreach', 'store'):
        module = types.ModuleType(package.__name__ + '.' + name)
        sys.modules[module.__name__] = module
        setattr(package, name, module)
    package.store.now = lambda: 1000
    package.outreach.new_ref = lambda: 'ref-fixture'
    package.contact.opted_out = lambda s, lid: False
    package.contact.check_text = lambda text, link: (text, [])
    path = Path(__file__).parent / 'marketing_workflow/server/marketing.py'
    spec = importlib.util.spec_from_file_location(package.__name__ + '.marketing', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


m = load_workflow()


class PanelAdapter:
    def __init__(self):
        self.lock = threading.RLock()
        self.db = sqlite3.connect(':memory:', check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        columns = ','.join(k + ' TEXT' for k in m.INPUT_FIELDS)
        self.db.executescript('CREATE TABLE leads(id TEXT PRIMARY KEY,updated_at INTEGER,' + columns + ');'
                             'CREATE TABLE jobs(id TEXT PRIMARY KEY,kind,title,params,status,progress,note,log,result,created_by,created_at,finished_at);'
                             'CREATE TABLE approvals(id,status,lead_id,decided_at);'
                             'CREATE TABLE events(lead_id,ts,title,detail);')
        self.db.execute("INSERT INTO leads(id,name,website,gate,stage) VALUES('lead','Fixture','https://fixture.example','geçti','Yeni')")
        self.db.commit()
        m.init(self)

    def q(self, sql, args=()):
        with self.lock:
            return [dict(r) for r in self.db.execute(sql, args)]

    def one(self, sql, args=()):
        rows = self.q(sql, args)
        return rows[0] if rows else None

    def x(self, sql, args=()):
        with self.lock:
            result = self.db.execute(sql, args)
            self.db.commit()
            return result

    def lead(self, lid):
        return self.one('SELECT * FROM leads WHERE id=?', (lid,))

    def update_job(self, jid, **fields):
        self.x('UPDATE jobs SET ' + ','.join(k + '=?' for k in fields) + ' WHERE id=?', (*fields.values(), jid))


class StorageProtocolTests(unittest.TestCase):
    def setUp(self):
        self.s = PanelAdapter()
        self.addCleanup(self.s.db.close)
        self.jid, _ = m.start(self.s, 'lead', 'fixture-request')
        self.report = {'karar': 'bulgu_var', 'bulgular': [{'alinti': 'Fixture verified quotation'}]}
        self.draft = {k: 'Fixture draft with enough characters to be an actual message.' for k in ('whatsapp', 'instagram', 'email_govde')}
        self.draft.update(email_konu='Fixture subject', notes={'whatsapp': []}, link='')
        self.cp = {'research': {'state': 'done', 'output': self.report}, 'draft': {'state': 'done', 'output': self.draft}}

    def test_retry_and_alias_survive_completed_job(self):
        self.assertEqual(m.start(self.s, 'lead', 'second-fixture-request'), (self.jid, False))
        m._save(self.s, self.jid, self.cp)
        m.publish(self.s, self.jid)
        self.s.update_job(self.jid, status='done')
        self.assertEqual(m.start(self.s, 'lead', 'second-fixture-request'), (self.jid, False))
        with self.assertRaises(m.Conflict):
            m.start(self.s, 'other-lead', 'fixture-request')

    def test_publication_is_atomic_idempotent_and_does_not_overwrite_an_edit(self):
        m._save(self.s, self.jid, self.cp)
        self.s.x("UPDATE leads SET draft='Owner changed the record' WHERE id='lead'")
        with self.assertRaises(m.Conflict):
            m.publish(self.s, self.jid)
        self.assertEqual(self.s.lead('lead')['draft'], 'Owner changed the record')
        self.assertEqual(self.s.one('SELECT count(*) n FROM events')['n'], 0)
        self.s.x("UPDATE leads SET draft=NULL WHERE id='lead'")
        m.publish(self.s, self.jid)
        m.publish(self.s, self.jid)
        self.assertEqual(self.s.one('SELECT count(*) n FROM events')['n'], 1)

    def test_restart_resumes_checkpoint_but_never_repeats_an_uncertain_model_call(self):
        m._save(self.s, self.jid, {'research': self.cp['research']})
        self.assertEqual(m.recover(self.s), [self.jid])
        for state in ('calling', 'uncertain'):
            self.s.update_job(self.jid, status='running')
            m._save(self.s, self.jid, {'research': {'state': state}})
            self.assertEqual(m.recover(self.s), [])
            self.assertEqual(self.s.one('SELECT status FROM jobs WHERE id=?', (self.jid,))['status'], 'failed')

    def test_content_change_revokes_owner_decision_and_stale_review(self):
        m._save(self.s, self.jid, self.cp)
        m.publish(self.s, self.jid)
        old = m.content_digest(self.s.lead('lead'))
        m.review(self.s, 'lead', old, 'accepted')
        edited = m.review(self.s, 'lead', old, 'edited', 'The owner edited this fixture message for the next review.')
        self.assertNotEqual(edited['digest'], old)
        self.assertEqual(m.views(self.s)['lead']['review']['decision'], 'edited')
        with self.assertRaises(m.Conflict):
            m.review(self.s, 'lead', old, 'accepted')
        self.assertEqual(self.s.lead('lead')['stage'], 'Taslak hazır')
