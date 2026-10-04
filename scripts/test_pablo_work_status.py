"""The Jeff-facing helper must not submit or replay an action."""
import contextlib
import io
import json
import unittest
from unittest import mock
from scripts.pablo_work_status import main


class WorkStatusHelperTests(unittest.TestCase):
    def test_list_and_reconcile_use_only_work_endpoints(self):
        for args, ending, method in [([], '/work?offset=0', 'GET'),
                                     (['--task-id', 'fixture'], '/work/fixture', 'GET'),
                                     (['--task-id', 'fixture', '--reconcile'], '/work/fixture/reconcile', 'POST')]:
            with self.subTest(method=method, ending=ending), mock.patch('scripts.pablo_work_status.bridge_key', return_value='fixture'):
                response = mock.MagicMock()
                response.__enter__.return_value = io.BytesIO(json.dumps({'request_id': 'fixture', 'phase': 'needs_review', 'open': True}).encode())
                with mock.patch('scripts.pablo_work_status.urlopen', return_value=response) as call, contextlib.redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(main(args), 0)
                req = call.call_args.args[0]
                self.assertTrue(req.full_url.endswith(ending))
                self.assertEqual(req.get_method(), method)
                self.assertTrue(json.loads(output.getvalue())['open'])

    def test_connection_failure_does_not_retry(self):
        with mock.patch('scripts.pablo_work_status.bridge_key', return_value='fixture'), mock.patch('scripts.pablo_work_status.urlopen', side_effect=TimeoutError()) as call, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['--task-id', 'fixture', '--reconcile']), 1)
            self.assertEqual(call.call_count, 1)


if __name__ == '__main__':
    unittest.main()
