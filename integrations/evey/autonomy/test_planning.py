import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('planning', Path(__file__).with_name('__init__.py'))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class PlanningTests(unittest.TestCase):
    def plan(self, args, registered=True):
        with patch.object(m, '_registered_tool', return_value=registered), patch.object(m, '_time_context', return_value={}):
            return json.loads(m.plan_handler(args))

    def test_unknown_cost_cannot_satisfy_free_only_even_for_configured_models(self):
        result = self.plan({'goal': 'research sources'})
        self.assertIsNone(result['free_only_satisfied'])
        for step in result['steps']:
            self.assertEqual(step['cost'], 'unknown')
            self.assertFalse(step['cost_measured']); self.assertIsNone(step['information_gain'])
            self.assertTrue(any('extra fee' in p for p in step['prerequisites']))

    def test_limits_include_reflection_and_truncation_is_visible(self):
        for cap in (1, 2, 3, 12):
            result = self.plan({'goal': 'fix code', 'constraints': 'thorough', 'max_steps': cap})
            self.assertLessEqual(len(result['steps']), cap)
            self.assertEqual(result['plan_truncated'], cap < 5)
        self.assertEqual(self.plan({'goal':'research', 'constraints':'fast'})['total_steps'], 2)

    def test_invalid_requests_do_not_probe_tools_or_execute(self):
        invalid = [None, {}, {'goal':1}, {'goal':' '}, {'goal':'x'*4001},
                   {'goal':'x','constraints':'paid'}, {'goal':'x','acceptance_criteria':['']},
                   {'goal':'x','acceptance_criteria':'done'}]
        invalid += [{'goal':'x','max_steps':v} for v in (True, 0, -1, 13, 1.5, '2')]
        with patch.object(m, '_registered_tool') as probe, patch.object(m, '_run') as execute:
            for args in invalid:
                with self.subTest(args=args):
                    self.assertEqual(json.loads(m.plan_handler(args))['status'], 'error')
            probe.assert_not_called(); execute.assert_not_called()

    def test_missing_registry_or_skill_name_is_never_presented_as_callable(self):
        for registered in (None, False):
            result = self.plan({'goal':'fix code'}, registered)
            self.assertTrue(all(s['tool'] is None for s in result['steps']))
            self.assertTrue(any(s['proposed_tool']=='github-pr-workflow' for s in result['steps']))

    def test_registered_is_not_transport_availability_or_authorization(self):
        result = self.plan({'goal':'health check'})
        self.assertFalse(result['execution_authorized']); self.assertFalse(result['outcome_verified'])
        self.assertTrue(all(s['tool_registered'] is True and s['tool_available_in_current_transport'] is None for s in result['steps']))
        self.assertEqual(result['status'], 'draft')

    def test_criteria_survive_exactly_without_becoming_verified(self):
        result = self.plan({'goal':'read fixture', 'acceptance_criteria':['SHA256 equals fixture value']})
        self.assertEqual(result['acceptance_criteria'], ['SHA256 equals fixture value'])
        self.assertFalse(result['acceptance_criteria_verified'])
        self.assertIn('independently', result['completion_rule'])
        self.assertFalse(result['template_is_goal_specific'])

    def test_missing_criteria_and_dependencies_are_explicit(self):
        result = self.plan({'goal':'araştır kaynakları'})
        self.assertEqual(result['criteria_origin'], 'unknown')
        self.assertIn('Define goal acceptance criteria', result['evidence_gaps'])
        self.assertEqual([s['depends_on'] for s in result['steps']], [[], [1], [2]])
        self.assertTrue(all('unknown or completed' in ' '.join(s['prerequisites']) for s in result['steps']))

    def test_turkish_goal_and_substring_classifier_regression(self):
        self.assertEqual(self.plan({'goal':'Hafıza kayıtlarını incele'})['template'], 'memory')
        self.assertEqual(self.plan({'goal':'Kod hatasını düzelt'})['template'], 'code')
        self.assertEqual(self.plan({'goal':'Find appropriate research sources'})['template'], 'research')

    def test_score_cannot_verify_plausible_but_false_text_or_trigger_next_work(self):
        task = 'fixture accepted artifact hash'
        plausible = ('fixture accepted artifact hash is correct and completed. '*4)
        with patch.object(m, '_log_decision') as log:
            result = json.loads(m.reflect_handler({'task_description':task,'result_text':plausible}))
        self.assertGreaterEqual(result['score'], 8)
        self.assertFalse(result['outcome_verified']); self.assertFalse(result['semantic_quality_verified'])
        self.assertEqual(result['label'], 'heuristic_only')
        self.assertNotIn('Run autonomous_decide', result['suggestion'])
        self.assertFalse(log.call_args.args[0]['outcome_verified'])

if __name__ == '__main__': unittest.main()
