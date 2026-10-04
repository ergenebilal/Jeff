import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest import mock
from scripts.jeff_memory_context import examine,declared_date,main,read_context

def parse(raw):
    _,header,body=raw.split('---',2);return json.loads(header),body.lstrip('\n')

class MemoryTruthTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);(self.root/'knowledge').mkdir()
    def record(self,name='one',metadata=None,text='Do not repeat a finished step.'):
        meta={'visibility':'internal','updated_at':'2026-01-01','facts':{'policy':'verify'}}| (metadata or {})
        source='knowledge/'+name+'.md';raw='---\n'+json.dumps(meta)+'\n---\n'+text
        (self.root/source).write_bytes(raw.encode('utf-8'))
        return {'source':source,'visibility':meta['visibility'],'text':text,'source_sha256':hashlib.sha256(raw.encode()).hexdigest()}
    def check(self,records,**kw):return examine(self.root,{'records':records},parse,lambda text:(text,0),1791110000,**kw)
    def test_old_statement_keeps_source_date_and_never_claims_current_truth(self):
        result=self.check([self.record()]);item=result['records'][0]
        self.assertEqual(item['assessment'],'old_source_statement');self.assertEqual(item['declared_date']['value'],'2026-01-01')
        self.assertFalse(item['current_truth_verified']);self.assertTrue(item['source_hash_matched'])
    def test_unknown_invalid_and_future_dates_are_not_invented_from_mtime(self):
        for value,state in [(None,'unknown'),('yesterday','invalid'),('2027-01-01','future_invalid'),('2026-10-04T12:00:00','invalid')]:
            with self.subTest(state=state):self.assertEqual(self.check([self.record(metadata={'updated_at':value})])['records'][0]['declared_date']['state'],state)
    def test_changed_missing_forged_or_oversized_source_excerpts_are_withheld(self):
        r=self.record();(self.root/r['source']).write_text('changed')
        self.assertEqual(self.check([r])['records'],[])
        r=self.record();r['text']='fabricated';self.assertEqual(self.check([r])['records'],[])
        (self.root/r['source']).unlink();self.assertEqual(self.check([r])['records'],[])
    def test_private_source_cannot_be_reclassified_by_cache(self):
        r=self.record(metadata={'visibility':'private'});r['visibility']='internal'
        self.assertEqual(self.check([r])['records'],[])
    def test_companion_traversal_absolute_and_untrusted_sources_are_withheld_without_reading(self):
        for change in [{'source':'companion/Core.md'},{'source':'knowledge/../../private/a.md'},{'source':'/tmp/a'},{'trust':'untrusted'},{'validity':'rejected'}]:
            with self.subTest(change=change):self.assertEqual(self.check([self.record()|change])['records'],[])
    def test_conflicting_facts_are_reported_and_newer_date_does_not_win(self):
        a=self.record();b=self.record('two',{'updated_at':'2026-10-01','facts':{'policy':'guess'}})
        result=self.check([a,b]);self.assertEqual(len(result['conflicts']),1)
        self.assertFalse(result['conflicts'][0]['resolved']);self.assertTrue(all(r['assessment']=='conflicting_source_statements' for r in result['records']))
    def test_cache_facts_do_not_override_source_metadata(self):
        r=self.record();r['facts']={'policy':'invented'}
        self.assertEqual(self.check([r])['records'][0]['facts'],{'policy':'verify'})
    def test_independent_projects_are_not_called_conflicting(self):
        first=self.record(metadata={'project':'one'})
        second=self.record('two',{'project':'two','facts':{'policy':'guess'}})
        self.assertEqual(self.check([first,second])['conflicts'],[])
    def test_public_audience_excludes_internal_and_preserves_public(self):
        result=self.check([self.record(),self.record('two',{'visibility':'public'})],audience='public')
        self.assertEqual([r['source'] for r in result['records']],['knowledge/two.md'])
    def test_truncated_excerpt_requires_exact_source_prefix(self):
        r=self.record(text='abcdef');r.update(text='abc [truncated]',text_truncated=True)
        self.assertEqual(self.check([r])['records'][0]['text'],'abc')
        r['text']='xyz [truncated]';self.assertEqual(self.check([r])['records'],[])
    def test_secret_filter_applies_to_whole_result_and_failure_does_not_return_raw(self):
        r=self.record(text='fixture-secret')
        result=examine(self.root,{'records':[r]},parse,lambda text:(text.replace('fixture-secret','[REDACTED]'),text.count('fixture-secret')),1791110000)
        self.assertNotIn('fixture-secret',json.dumps(result));self.assertEqual(result['secret_matches_redacted'],1)
        with self.assertRaises(ValueError):examine(self.root,{'records':[r]},parse,mock.Mock(side_effect=ValueError()),1791110000)
    def test_failure_and_no_results_are_never_successful_recall(self):
        self.assertEqual(self.check([])['status'],'no_source_evidence')
        with mock.patch('scripts.jeff_memory_context.read_context',side_effect=RuntimeError('private secret')),mock.patch('builtins.print') as printed:
            self.assertEqual(main(['fixture']),1);self.assertNotIn('private secret',printed.call_args[0][0])
    def test_bad_queries_reject_before_vault_reads(self):
        for query in ('','x'*2001,None):
            with self.subTest(query_type=type(query).__name__),self.assertRaises(ValueError):read_context(query,vault=self.root)

if __name__=='__main__':unittest.main()
