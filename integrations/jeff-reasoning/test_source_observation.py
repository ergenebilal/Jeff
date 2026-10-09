import hashlib,importlib.util,json,tempfile,time,unittest
from pathlib import Path

def module(path,name):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class SourceObservationTests(unittest.TestCase):
 def setUp(self):
  self.brain=module(Path(__file__).with_name('__init__.py'),'anonymous_p89_brain')
  self.helper=module(Path(__file__).parents[2]/'scripts/jeff_memory_context.py','anonymous_p89_helper')
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.vault=Path(self.temp.name);(self.vault/'knowledge').mkdir()
 def checked(self,body='Beta kontrol kararı taslak.',date='2026-10-09',count=None):
  raw='---\n'+json.dumps({'project':'Beta','visibility':'internal','date':date})+'\n---\n'+body
  path=self.vault/'knowledge/beta.md';path.write_bytes(raw.encode());record={'source':'knowledge/beta.md','source_sha256':hashlib.sha256(raw.encode()).hexdigest(),'text':body,'visibility':'internal'}
  def parse(text):_,header,source=text.split('---',2);return json.loads(header),source.lstrip('\n')
  context={'records':[record],**({'stale_count':count} if count is not None else {})};stamp=time.time()
  return self.helper.examine(self.vault,context,parse,lambda text:(text,0),stamp,project='Beta')
 def brief(self,result):return self.brain.memory_brief('Beta kontrol kararı',reader=lambda q:result)
 def test_real_file_read_scope_confirms_only_observation_bytes(self):
  result=self.checked();brief=self.brief(result);scope=brief['records'][0]['verification_scope']
  self.assertTrue(scope['source_bytes_matched_at_observation']);self.assertEqual(scope['observed_at'],result['observed_at']);self.assertEqual(scope['operational_claims'],'not_independently_checked');self.assertEqual(scope['subsequent_source_changes'],'not_checked');self.assertFalse(brief['current_truth_verified'])
 def test_missing_bad_or_unknown_observation_time_is_not_invented(self):
  result=self.checked()
  for stamp in [None,True,0,-1,float('nan'),float('inf'),'private fixture string']:
   with self.subTest(kind=type(stamp).__name__):
    brief=self.brief({**result,'observed_at':stamp});self.assertIsNone(brief['observed_at']);self.assertIsNone(brief['records'][0]['verification_scope']['source_bytes_matched_at_observation']);self.assertNotIn('private fixture',json.dumps(brief))
 def test_source_declaration_never_becomes_independent_date_evidence(self):
  for date in [None,'yesterday','2027-01-01','2026-10-09']:
   with self.subTest(date=date):
    scope=self.brief(self.checked(date=date))['records'][0]['verification_scope'];self.assertEqual(scope['source_date'],'source_declaration_only');self.assertEqual(scope['operational_claims'],'not_independently_checked')
 def test_missing_search_count_is_unknown_and_real_zero_is_kept(self):
  for count in [None,0,2]:
   brief=self.brief(self.checked(count=count));self.assertEqual(brief['backend_stale_count'],count);self.assertEqual(brief['backend_stale_count_scope'],'this_search_backend_only')
 def test_source_changes_are_not_covered_by_previous_observation(self):
  old=self.brief(self.checked());(self.vault/'knowledge/beta.md').write_bytes(b'changed after observation')
  self.assertEqual(old['records'][0]['verification_scope']['subsequent_source_changes'],'not_checked');self.assertNotEqual(old['records'][0]['source_sha256'],hashlib.sha256((self.vault/'knowledge/beta.md').read_bytes()).hexdigest())
 def test_unverified_record_gets_no_positive_scope_and_budget_stays_bounded(self):
  result=self.checked();result['records'][0]['source_hash_matched']=False;self.assertEqual(self.brief(result)['records'],[])
  result=self.checked('Beta kontrol kararı '+('veri '*1200));result['records']*=20;brief=self.brief(result);self.assertTrue(brief['retrieval_truncated']);self.assertLessEqual(len(self.brain.dump(brief)),5000)

 def test_unverified_operational_state_establishes_neither_presence_nor_absence(self):
  scope=self.brief(self.checked())['records'][0]['verification_scope']
  self.assertEqual(scope['operational_presence'],'unknown');self.assertEqual(scope['operational_absence'],'unknown');self.assertTrue(scope['source_bytes_matched_at_observation'])

if __name__=='__main__':unittest.main()
