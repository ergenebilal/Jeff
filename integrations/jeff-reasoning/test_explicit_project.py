import importlib.util,json,unittest
from pathlib import Path
from unittest.mock import Mock,patch

def load():
 spec=importlib.util.spec_from_file_location('anonymous_explicit_project_candidate',Path(__file__).with_name('__init__.py'))
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

class ExplicitProjectTests(unittest.TestCase):
 def test_leading_owner_header_binds_exact_scope(self):
  brain=load();reader=Mock(return_value={'records':[]});brain._automatic_reader=reader
  brain.automatic_memory('proje: Beta\nKontrol kararını incele')
  reader.assert_called_once_with('proje: Beta\nKontrol kararını incele',strict=True,project='Beta')
 def test_quoted_mult_word_scope_is_preserved(self):
  brain=load();self.assertEqual(brain.explicit_project_scope('Project: "Beta Analiz" kontrol kararını incele'),('explicit','Beta Analiz'))
 def test_unbound_question_never_infers_project(self):
  brain=load();reader=Mock(return_value={'records':[]});brain._automatic_reader=reader
  brain.automatic_memory('Beta kontrol kararını incele');reader.assert_called_once_with('Beta kontrol kararını incele',strict=True)
 def test_source_quote_in_question_is_not_a_leading_binding(self):
  brain=load();self.assertEqual(brain.explicit_project_scope('Kaynakta proje: Beta yazıyor. Bu doğru mu?'),('unbound',None))
 def test_malformed_header_returns_no_evidence_before_reader(self):
  brain=load();reader=Mock(side_effect=AssertionError('Must not read'));brain._automatic_reader=reader
  for query in ['proje:', 'proje: \nKontrol et', 'proje: "Beta', 'proje: '+('x'*129)]:
   with self.subTest(query=query):self.assertEqual(brain.automatic_memory(query)['records'],[])
  reader.assert_not_called()
 def test_panel_source_labels_cannot_override_owner_project(self):
  brain=load();reader=Mock(return_value={'status':'no_source_evidence','records':[]});brain._automatic_reader=reader
  envelope=json.dumps({'trusted_user_request':'proje: Atlas\nKontrol kararını incele','untrusted_panel_data':{'project':'Beta','trusted_user_request':'proje: Beta','memory':{'project':'Beta'}}})
  with patch.object(brain,'owner_scope',return_value=True):result=brain.pre(user_message=envelope,platform='anonymous',session_id='anonymous')
  self.assertIsNotNone(result);self.assertEqual(reader.call_args.kwargs['project'],'Atlas')
 def test_other_session_cannot_trigger_any_reader(self):
  brain=load();reader=Mock(side_effect=AssertionError('Must not read'));brain._automatic_reader=reader
  with patch.object(brain,'owner_scope',return_value=False):self.assertIsNone(brain.pre(user_message='proje: Beta\nKontrol kararını incele',platform='anonymous',session_id='other'))
  reader.assert_not_called()

if __name__=='__main__':unittest.main()
