import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('surgery_reflect', ROOT/'integrations/evey/reflect/__init__.py')
reflect = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reflect)

class ReflectTruthTests(unittest.TestCase):
    def result(self, response=None, error=None, draft='fixture draft'):
        with patch.object(reflect, 'call_llm', return_value=response, side_effect=error):
            return json.loads(reflect.handler({'task':'review fixture', 'draft':draft}))

    def test_unavailable_never_passes(self):
        for response in (None, '', '   '):
            with self.subTest(response=response):
                self.assertEqual(self.result(response)['status'], 'unavailable')

    def test_exception_is_sanitized_and_unavailable(self):
        result=self.result(error=RuntimeError('SECRET fixture must not leak'))
        self.assertEqual(result['status'], 'unavailable')
        self.assertNotIn('SECRET', json.dumps(result))

    def test_timeout_is_unavailable(self):
        self.assertEqual(self.result(error=TimeoutError())['status'], 'unavailable')

    def test_invalid_and_contradictory_verdicts_need_review(self):
        for response in ({'verdict':'pass'}, 'PASS', 'PASSING: good', 'The word PASS is present',
                         'PASS: good\nFIX: wrong', 'PASS: Critique unavailable', 'FIX: contains PASS'):
            with self.subTest(response=response):
                self.assertNotEqual(self.result(response)['status'], 'pass')

    def test_valid_positive_and_negative(self):
        self.assertEqual(self.result('PASS: Meets the requested criteria.')['status'], 'pass')
        self.assertEqual(self.result('FIX: Missing the required evidence.')['status'], 'needs_improvement')

    def test_entire_draft_is_reviewed_and_bound(self):
        draft='x'*1600+' tail claim'
        with patch.object(reflect, 'call_llm', return_value='PASS: Complete.') as model:
            result=json.loads(reflect.handler({'task':'review','draft':draft}))
        self.assertIn('tail claim',model.call_args.args[1])
        self.assertEqual(len(result['draft_sha256']),64)
        self.assertIn('evaluated_at',result)

    def test_oversize_or_invalid_input_does_not_call_model(self):
        with patch.object(reflect,'call_llm') as model:
            for args in ({'draft':'x'*30001,'task':'review'}, None, {'draft':17}, {'draft':'x'}):
                self.assertEqual(json.loads(reflect.handler(args))['status'],'needs_review')
        model.assert_not_called()
