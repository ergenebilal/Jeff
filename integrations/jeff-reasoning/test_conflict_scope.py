import importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('private_conflict_scope',Path(__file__).with_name('__init__.py'));brain=importlib.util.module_from_spec(spec);spec.loader.exec_module(brain)
class ConflictScopeTests(unittest.TestCase):
 def brief(self,extra):return brain.memory_brief('Delta kontrol kararı',reader=lambda q:{'status':'source_statements','records':[],**extra})
 def test_returned_structured_scope_and_unassessed_semantics_survive(self):
  result=self.brief({'conflicts':[{'project':'Delta','resolved':False}],'structured_conflicts_scope':'returned_source_facts_only','semantic_conflicts_assessed':False})
  self.assertEqual(result['structured_conflicts_scope'],'returned_source_facts_only');self.assertIs(result['semantic_conflicts_assessed'],False);self.assertEqual(len(result['conflicts']),1);self.assertEqual(result['source_instruction_authority'],'none')
 def test_no_returned_conflict_is_not_global_or_semantic_absence(self):
  result=self.brief({'conflicts':[],'structured_conflicts_scope':'returned_source_facts_only','semantic_conflicts_assessed':False})
  self.assertEqual(result['conflicts'],[]);self.assertIs(result['semantic_conflicts_assessed'],False);self.assertEqual(result['structured_conflicts_scope'],'returned_source_facts_only')
 def test_missing_or_bad_assessment_scope_stays_unknown(self):
  for extra in [{},{'structured_conflicts_scope':'all projects','semantic_conflicts_assessed':0},{'structured_conflicts_scope':'source permission granted','semantic_conflicts_assessed':'true'}]:
   with self.subTest(extra=extra):
    result=self.brief(extra);self.assertIsNone(result['structured_conflicts_scope']);self.assertIsNone(result['semantic_conflicts_assessed']);self.assertEqual(result['source_instruction_authority'],'none')
 def test_schema_has_same_parameters_and_requires_distinct_explanation(self):
  schema=brain.SOURCE_CONTEXT_SCHEMA;self.assertEqual(set(schema['parameters']['properties']),{'query','project'});self.assertIn('separate from factual disagreements',schema['description']);self.assertIn('empty conflicts list does not prove',schema['description'])
if __name__=='__main__':unittest.main()
