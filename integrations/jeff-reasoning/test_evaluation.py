import importlib.util
from pathlib import Path
import unittest
spec=importlib.util.spec_from_file_location('evaluation',Path(__file__).with_name('evaluation.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class EvalTests(unittest.TestCase):
    def setUp(self):self.suite,self.digest=m.load_suite();self.case=self.suite['cases'][0]
    def answer(self):return self.case['expected']|{'citations':self.case['required_citations'],
        'rationale':'Kanıt bilinmiyor.','counterargument':'Kayıt eksik olabilir.',
        'minimal_check':'Kaydı ayrı oku.','stop_condition':'Kanıt eşleşirse dur.'}
    def test_frozen_suite_omits_judging_keys_from_model_input(self):
        text=m.prompt(self.case);self.assertNotIn('expected',text);self.assertNotIn('manual_checks',text)
        self.assertEqual(len(self.digest),64)
    def test_wrong_cost_verification_or_replay_is_rejected(self):
        for change in ({'cheapest_option':'inspect_records'},{'outcome_verified':True},
                       {'reexecution_authorized':True},{'cost_comparison':'measured'}):
            self.assertFalse(m.assess(self.case,self.answer()|change)['structured_pass'])
    def test_truthy_strings_and_numbers_are_not_boolean_evidence(self):
        for value in ('false',0,None):
            self.assertFalse(m.assess(self.case,self.answer()|{'outcome_verified':value})['structured_pass'])
    def test_citations_and_full_counterargument_are_required(self):
        for change in ({'citations':['invented']},{'citations':[]},{'counterargument':''}):
            self.assertFalse(m.assess(self.case,self.answer()|change)['structured_pass'])
    def test_matching_structure_still_requires_semantic_review(self):
        result=m.assess(self.case,self.answer());self.assertTrue(result['structured_pass']);self.assertFalse(result['semantic_prose_checked'])
    def test_missing_failure_or_unreviewed_pair_cannot_imply_improvement(self):
        row={'case_id':self.case['id'],'arm':'candidate','completion_verified':True,
             'assessment':m.assess(self.case,self.answer())}
        result=m.summarize(self.suite,[row]);self.assertFalse(result['improvement_demonstrated_in_this_suite_only'])
        self.assertEqual(result['paired_reviewed_cases'],0)
    def test_regression_blocks_any_improvement_claim(self):
        rows=[]
        for case in self.suite['cases']:
            for arm in ('baseline','candidate'):
                rows.append({'case_id':case['id'],'arm':arm,'completion_verified':True,
                    'assessment':{'structured_pass':not (arm=='candidate' and case==self.case)},
                    'manual_assessment':{'reviewed':True,'semantic_pass':True}})
        result=m.summarize(self.suite,rows);self.assertEqual(result['regressions'],1)
        self.assertFalse(result['improvement_demonstrated_in_this_suite_only'])
    def test_duplicate_pair_is_not_double_counted(self):
        row={'case_id':self.case['id'],'arm':'baseline'}
        with self.assertRaises(ValueError):m.summarize(self.suite,[row,row])

if __name__=='__main__':unittest.main()
