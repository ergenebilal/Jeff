"""Packaged qualifier CI with real SQLite and minimal, stubbed panel adapters.

Official HTTP readers / actual Jeff responses / complete panel UI are verified
separately. These tests assert persistence and the admission boundary.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sqlite3
import sys
import threading
import types
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit


def load_module():
    package = types.ModuleType('_qualification_fixture')
    package.__path__ = []
    sys.modules[package.__name__] = package
    for name in ('analysis', 'contact', 'gate', 'marketing', 'outreach', 'reach', 'sitecheck', 'store'):
        mod = types.ModuleType(package.__name__ + '.' + name)
        sys.modules[mod.__name__] = mod
        setattr(package, name, mod)
    package.store.now = lambda: 1000
    package.marketing._json = lambda d: json.dumps(d, sort_keys=True)
    package.marketing.digest = lambda d: hashlib.sha256(package.marketing._json(d).encode()).hexdigest()
    package.marketing.Conflict = type('Conflict', (Exception,), {})
    package.contact.opted_out = lambda s, lid: bool(s.one('SELECT 1 FROM optout WHERE lead_id=?', (lid,)))
    package.gate.TARGET = {'Diş kliniği'}
    package.gate.PUBLIC = re.compile('devlet')
    package.gate._n = lambda s: s.lower()
    package.reach.own_domain = lambda s: urlsplit(s or '').hostname
    package.reach.rank_emails = lambda e, s: list(dict.fromkeys(e))
    package.outreach.argument = lambda aid: {'id': aid} if aid == 'randevu-dusmesin' else None
    package.outreach.arguments = lambda: {'arguments': [{'id': 'randevu-dusmesin'}]}
    package.outreach.short_name = lambda s: s
    package.analysis._flat = lambda s: ' '.join(s.lower().split())
    package.analysis.quote_in = lambda q, t: len(q) >= 12 and q in t
    package.analysis.same_site = lambda a, b: urlsplit(a).hostname == urlsplit(b).hostname
    package.sitecheck._norm = lambda s: s.lower()
    package.sitecheck.INSTRUCTION_LIKE = re.compile('ignore previous instructions')
    path = Path(__file__).parent/'lead_qualification/server/qualification.py'
    spec = importlib.util.spec_from_file_location(package.__name__+'.qualification', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


q = load_module()


class Adapter:
    def __init__(self):
        self.lock = threading.RLock()
        self.db = sqlite3.connect(':memory:', check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('CREATE TABLE leads(id TEXT PRIMARY KEY,'+','.join(k+' TEXT' for k in q.FIELDS)+',stage TEXT);'
                             'CREATE TABLE optout(lead_id);'
                             'CREATE TABLE jobs(id TEXT PRIMARY KEY,kind,title,params,status,progress,note,log,result,created_by,created_at,finished_at);')
        self.x("INSERT INTO leads(id,name,website,category,stage) VALUES('lead','Fixture','https://fixture.example','Diş kliniği','Yeni')")
        q.init(self)

    def one(self, sql, args=()):
        rows = self.q(sql, args)
        return rows[0] if rows else None

    def q(self, sql, args=()):
        return [dict(r) for r in self.db.execute(sql, args)]

    def x(self, sql, args=()):
        result = self.db.execute(sql, args)
        self.db.commit()
        return result

    def lead(self, lid):
        return self.one('SELECT * FROM leads WHERE id=?', (lid,))

    def leads(self):
        return self.q('SELECT * FROM leads')

    def update_job(self, jid, **fields):
        self.x('UPDATE jobs SET '+','.join(k+'=?' for k in fields)+' WHERE id=?', (*fields.values(), jid))


class QualificationBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.s = Adapter()
        self.addCleanup(self.s.db.close)
        self.jid, _ = q.start(self.s, ['lead'], 'fixture-request')
        self.lead = self.s.lead('lead')
        self.pages = [{'url': 'https://fixture.example', 'text': 'info@fixture.example Official clinic workflow with international coordination. '
                       'Official cancellation waiting list requires callbacks.', 'links': [], 'observed_at': 1000, 'text_sha256': 'fixture'}]
        self.research = {'argument_id': 'randevu-dusmesin', 'facts': [
            {'kind': 'operations', 'signal': 'international_patient_coordination', 'quote': 'Official clinic workflow with international coordination.', 'url': 'https://fixture.example'},
            {'kind': 'operations', 'signal': 'rescheduling_waitlist', 'quote': 'Official cancellation waiting list requires callbacks.', 'url': 'https://fixture.example'}]}
        self.audit = {'supported_ids': [0, 1], 'distinct_operations': [0, 1], 'explicit_need_ids': [], 'trigger_ids': [],
                      'blocking_counter_ids': [], 'fit': True, 'unresolved': True, 'hypothesis': 'Potential administrative coordination workload.',
                      'discovery_question': 'How do you manage these two workflows?', 'unknowns': [], 'reason': 'Two workflows need investigation.'}
        self.handle = types.SimpleNamespace(id=self.jid, step=lambda *a, **k: None)

    def run_job(self):
        with patch.object(q, 'collect', return_value=(self.pages, [])), patch.object(q, 'model', side_effect=[self.research, self.audit]):
            q.run(self.s, self.handle, {})

    def test_same_request_survives_publication_without_duplicate_report(self):
        self.run_job()
        self.assertEqual(q.start(self.s, ['lead'], 'fixture-request'), (self.jid, False))
        with patch.object(q, 'model') as model:
            q.run(self.s, self.handle, {})
            model.assert_not_called()
        self.assertEqual(self.s.one('SELECT count(*) n FROM qualification_reports')['n'], 1)
        self.assertEqual(self.s.lead('lead'), self.lead)

    def test_shortlist_does_not_pad_and_excludes_changed_or_opted_out_firms(self):
        self.run_job()
        self.assertEqual(q.board(self.s)['shortfall'], 9)
        self.s.x("UPDATE leads SET website='https://other.example'")
        self.assertFalse(q.board(self.s)['ids'])
        self.s.x("UPDATE leads SET website='https://fixture.example'")
        self.s.x("INSERT INTO optout VALUES('lead')")
        self.assertFalse(q.board(self.s)['ids'])

    def test_generic_duplicate_workflow_cannot_qualify(self):
        self.research['facts'][1]['signal'] = self.research['facts'][0]['signal']
        self.run_job()
        self.assertFalse(q.board(self.s)['ids'])

    def test_restart_fails_unknown_call_without_replaying_it(self):
        self.s.x('UPDATE qualification_runs SET checkpoint=?', (json.dumps({'lead': {'state': 'calling'}}),))
        with patch.object(q, 'model') as model:
            self.assertEqual(q.recover(self.s), [self.jid])
            q.run(self.s, self.handle, {})
            model.assert_not_called()
        self.assertEqual(json.loads(self.s.one('SELECT checkpoint FROM qualification_runs')['checkpoint'])['lead']['state'], 'uncertain')

    def test_completed_report_and_checkpoint_are_atomic_when_company_changes(self):
        def response(*args):
            if args[0] == q.RESEARCH:
                return self.research
            self.s.x("UPDATE leads SET name='Owner edited company'")
            return self.audit
        with patch.object(q, 'collect', return_value=(self.pages, [])), patch.object(q, 'model', side_effect=response):
            with self.assertRaises(q.marketing.Conflict):
                q.run(self.s, self.handle, {})
        self.assertEqual(self.s.one('SELECT count(*) n FROM qualification_reports')['n'], 0)
        cp = json.loads(self.s.one('SELECT checkpoint FROM qualification_runs')['checkpoint'])
        self.assertEqual(cp['lead']['state'], 'uncertain')
