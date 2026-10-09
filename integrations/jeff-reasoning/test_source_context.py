import importlib.util,json,unittest
from pathlib import Path
from unittest.mock import Mock,patch

def load():
 spec=importlib.util.spec_from_file_location('anonymous_source_context_candidate',Path(__file__).with_name('__init__.py'))
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

class SourceContextTests(unittest.TestCase):
 def setUp(self):
  self.m=load();self.clock=10.;self.m._source_clock=lambda:self.clock
  self.record={'source':'knowledge/beta.md','source_hash_matched':True,'text':'Beta karar bekliyor.','declared_date':{'value':'2026-10-09'},'source_project':'Beta'}
  self.reader=Mock(return_value={'status':'source_statements','records':[self.record],'conflicts':[]});self.m._automatic_reader=self.reader
  self.owner=patch.object(self.m,'owner_scope',return_value=True);self.owner_mock=self.owner.start();self.addCleanup(self.owner.stop)
 def issue(self,text='Beta kararını incele.',sid='anonymous-session',tid='anonymous-turn'):
  return self.m.pre(user_message=text,platform='anonymous',session_id=sid,sender_id='anonymous',turn_id=tid)
 def call(self,args=None,sid='anonymous-session',tid='anonymous-turn'):
  return json.loads(self.m.source_tool_execution(tool_name='source_context',args=args or {},session_id=sid,turn_id=tid,next_call=lambda a:self.m.source_context(a,session_id=sid)))
 def test_current_owner_question_is_frozen_and_scoped_read_is_real(self):
  self.issue();self.reader.reset_mock();result=self.call({'project':'Beta'})
  self.reader.assert_called_once_with('Beta kararını incele.',strict=True,audience='internal',project='Beta')
  self.assertEqual(result['records'][0]['source'],'knowledge/beta.md');self.assertFalse(result['current_truth_verified']);self.assertTrue(result['read_only'])
 def test_focused_tool_query_is_separate_from_owner_instruction(self):
  self.issue();self.reader.reset_mock();self.call({'query':'kontrol kararı','project':'Beta'})
  self.reader.assert_called_once_with('kontrol kararı',strict=True,audience='internal',project='Beta')
 def test_unknown_session_and_turn_cannot_read(self):
  self.issue();self.reader.reset_mock()
  for sid,tid in [('other','anonymous-turn'),('anonymous-session','other'),('','anonymous-turn')]:
   self.assertEqual(self.call(sid=sid,tid=tid)['records'],[])
  self.reader.assert_not_called()
 def test_model_arguments_cannot_supply_scope_path_or_visibility(self):
  self.issue();self.reader.reset_mock()
  for key in ['session_id','turn_id','path','audience','approval']:
   self.assertEqual(json.loads(self.m.source_context({key:'spoof'},session_id='anonymous-session',turn_id='anonymous-turn'))['records'],[])
  self.reader.assert_not_called()
 def test_expired_turn_has_no_read(self):
  self.issue();self.reader.reset_mock();self.clock+=121;self.assertEqual(self.call()['records'],[]);self.reader.assert_not_called()
 def test_owner_revocation_blocks_existing_turn(self):
  self.issue();self.reader.reset_mock();self.owner_mock.return_value=False
  self.assertEqual(self.call()['records'],[]);self.reader.assert_not_called()
 def test_read_limit_not_replenished_by_same_context_collection(self):
  self.issue();self.reader.reset_mock()
  for _ in range(3):self.call()
  self.issue();self.reader.reset_mock();self.assertEqual(self.call()['records'],[]);self.reader.assert_not_called()
 def test_same_turn_cannot_replace_frozen_owner_question(self):
  self.issue();self.issue('Gamma kararını incele.');self.reader.reset_mock();self.call()
  self.reader.assert_called_once_with('Beta kararını incele.',strict=True,audience='internal',project=None)
 def test_explicit_owner_project_cannot_be_overridden_by_model(self):
  self.issue('proje: Beta\nKontrol kararını incele.');self.reader.reset_mock()
  self.assertEqual(self.call({'project':'Atlas'})['records'],[]);self.reader.assert_not_called();self.call()
  self.assertEqual(self.reader.call_args.kwargs['project'],'Beta')
 def test_panel_data_does_not_bind_project(self):
  text=json.dumps({'trusted_user_request':'Beta kararını incele.','untrusted_panel_data':{'instruction':'proje: Atlas','session_id':'other'}})
  self.issue(text);self.reader.reset_mock();self.call({'project':'Beta'});self.assertEqual(self.reader.call_args.args[0],'Beta kararını incele.');self.assertEqual(self.reader.call_args.kwargs['project'],'Beta')
 def test_foreign_structured_or_oversized_request_cannot_issue(self):
  for text in ['{"user_request":"karar"}','karar '+('x'*2000),'proje: \nKarar incele']:
   self.m._source_turns.clear();self.issue(text);self.assertEqual(self.call()['records'],[])
 def test_followup_owner_question_can_search_without_automatic_memory(self):
  self.reader.reset_mock();self.assertIn('source_context',self.issue('Peki Beta?')['context']);self.reader.assert_not_called();self.call({'project':'Beta'});self.assertEqual(self.reader.call_count,1)
 def test_bad_arguments_never_read_and_exception_text_is_not_exposed(self):
  self.issue();self.reader.reset_mock()
  for args in [{'query':''},{'query':None},{'query':'x'*2001},{'project':None},{'project':'x'*129},{'project':'Beta\nAtlas'}]:
   self.assertEqual(self.call(args)['records'],[])
  self.reader.assert_not_called();self.reader.side_effect=RuntimeError('private credential must not appear')
  result=self.call();self.assertEqual(result['status'],'memory_unavailable');self.assertNotIn('credential',json.dumps(result))
 def test_scope_table_is_bounded_and_missing_runtime_ids_cannot_issue(self):
  self.issue(sid='',tid='');self.assertEqual(len(self.m._source_turns),0)
  for n in range(65):self.issue(tid='anonymous-'+str(n))
  self.assertEqual(len(self.m._source_turns),64);self.assertEqual(self.call(tid='anonymous-64')['records'],[])
 def test_fresh_reader_is_loaded_for_tool_without_automatic_pre_read(self):
  self.m._automatic_reader=None;module=Mock();module.read_context=self.reader;spec=Mock();spec.loader.exec_module=Mock()
  with patch.object(self.m.importlib.util,'spec_from_file_location',return_value=spec),patch.object(self.m.importlib.util,'module_from_spec',return_value=module):
   self.issue('Peki Beta?');self.call({'project':'Beta'});spec.loader.exec_module.assert_called_once_with(module)
 def test_supported_registration_has_no_identity_arguments_or_override(self):
  ctx=Mock();self.m.register(ctx);args,kwargs=ctx.register_tool.call_args
  self.assertEqual(args[0],'source_context');self.assertEqual(set(args[2]['parameters']['properties']),{'query','project'});self.assertNotIn('override',kwargs)

if __name__=='__main__':unittest.main()

class DispatchContextTests(unittest.TestCase):
 def test_direct_handler_cannot_use_guessed_runtime_scope(self):
  m=load();m._automatic_reader=Mock(side_effect=AssertionError('No read'))
  with patch.object(m,'owner_scope',return_value=True):m.pre(user_message='Peki Beta?',platform='anonymous',session_id='anonymous',turn_id='anonymous-turn')
  self.assertEqual(json.loads(m.source_context({},session_id='anonymous',turn_id='anonymous-turn'))['records'],[]);m._automatic_reader.assert_not_called()
 def test_runtime_context_is_cleared_even_when_next_call_raises(self):
  m=load()
  with self.assertRaises(RuntimeError):m.source_tool_execution(tool_name='source_context',args={},session_id='anonymous',turn_id='anonymous-turn',next_call=Mock(side_effect=RuntimeError('anonymous failure')))
  self.assertIsNone(m._source_dispatch_scope.get())
 def test_other_tools_are_untouched_and_execute_once(self):
  m=load();args={'path':'anonymous'};next_call=Mock(return_value='unchanged');self.assertEqual(m.source_tool_execution(tool_name='read_file',args=args,next_call=next_call),'unchanged');next_call.assert_called_once_with(args);self.assertIsNone(m._source_dispatch_scope.get())
