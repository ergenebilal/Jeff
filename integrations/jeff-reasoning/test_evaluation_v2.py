import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('evaluation_v2', Path(__file__).with_name('evaluation_v2.py'))
ev = importlib.util.module_from_spec(spec); spec.loader.exec_module(ev)
FROZEN_SHA = '11365da13418b4b44626608dcff72d002e8147bacf1d2bf709ad2416bae6b010'


class NewEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.suite, self.sha = ev.load_suite()

    def answer(self, case):
        return case['expected'] | {'citations': case['required_citations'],
            **{key: 'Review prose separately; this is only a parser fixture.' for key in
               ('rationale', 'counterargument', 'minimal_check', 'stop_condition')}}

    def test_frozen_cases_include_positive_and_do_not_accept_all_unknown(self):
        self.assertEqual(self.sha, FROZEN_SHA)
        self.assertEqual(len(self.suite['cases']), 9)
        self.assertTrue(any(c['expected']['new_task_outcome'] == 'matched_at_observation' for c in self.suite['cases']))
        for case in self.suite['cases']:
            with self.subTest(case=case['id']):
                raw = json.dumps(self.answer(case))
                row = ev.inspect_raw(case, raw)
                self.assertTrue(row['structured_pass']); self.assertFalse(row['semantic_prose_checked'])
                self.assertEqual(row['raw_answer'], raw)
                answer = self.answer(case); answer['new_task_outcome'] = 'unknown'
                if case['expected']['new_task_outcome'] != 'unknown':
                    self.assertFalse(ev.inspect_raw(case, json.dumps(answer))['structured_pass'])

    def test_raw_duplicate_keys_cut_output_and_wrong_types_are_preserved_and_rejected(self):
        case = self.suite['cases'][0]
        for raw in ('{"new_task_outcome":"not_run","new_task_outcome":"unknown"}',
                    '{"nested":{"x":1,"x":2}}', '{"x":NaN}', '{"new_task_outcome":'):
            row = ev.inspect_raw(case, raw)
            self.assertFalse(row['structured_pass']); self.assertEqual(row['raw_answer'], raw)
        answer = self.answer(case); answer['reexecution_authorized'] = 0
        self.assertFalse(ev.inspect_raw(case, json.dumps(answer))['structured_pass'])

    def rows(self):
        return [ev.inspect_raw(case, json.dumps(self.answer(case))) |
                {'case_id': case['id'], 'arm': arm, 'completion_verified': True,
                 'manual_review': {'reviewed': True, 'semantic_pass': True}}
                for case in self.suite['cases'] for arm in ('baseline', 'candidate')]

    def test_missing_failed_unreviewed_or_duplicate_pairs_cannot_show_improvement(self):
        self.assertFalse(ev.summarize(self.suite, [])['development_suite_improvement_only'])
        rows = self.rows(); self.assertTrue(ev.summarize(self.suite, rows)['paired_suite_complete'])
        self.assertFalse(ev.summarize(self.suite, rows)['development_suite_improvement_only'])
        for mutation in ({'completion_verified': False}, {'completion_verified': 1},
                         {'raw_answer': None}, {'manual_review': {'reviewed': False}}):
            altered = self.rows(); altered[0].update(mutation)
            result = ev.summarize(self.suite, altered)
            self.assertFalse(result['paired_suite_complete']); self.assertFalse(result['development_suite_improvement_only'])
        with self.assertRaises(ValueError): ev.summarize(self.suite, rows + [rows[0]])
        with self.assertRaises(ValueError): ev.summarize(self.suite, [{'case_id': 'foreign', 'arm': 'baseline'}])

    def test_regression_blocks_superiority_and_generalization_stays_open(self):
        rows = self.rows()
        rows[0]['structured_pass'] = False
        result = ev.summarize(self.suite, rows)
        self.assertTrue(result['development_suite_improvement_only'])
        self.assertFalse(result['generalization_proven'])
        rows[3]['structured_pass'] = False
        result = ev.summarize(self.suite, rows)
        self.assertEqual(result['regressions'], 1); self.assertFalse(result['development_suite_improvement_only'])


if __name__ == '__main__': unittest.main()
