import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from scripts.pablo_work_plan import main


class PlanHelperTests(unittest.TestCase):
    def test_create_advance_and_signal_use_correct_bound_endpoints(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/'plan.json';file.write_text(json.dumps({'goal':'fixture','steps':[{'name':'one','draft':{'content':'x'}}]}))
            cases=[(['--file',str(file)],'/execute','local_draft_plan'),(['--advance'],'/work/fixture/advance',None),(['--cancel'],'/work/fixture/cancel',None),
                   (['--signal','one','--key','ready','--source','input receipt'],'/work/fixture/signal',None)]
            for args,path,action in cases:
                response=mock.MagicMock();response.__enter__.return_value=io.BytesIO(b'{"status":"WAITING_FOR_EVENT","outcome_verified":false}')
                with self.subTest(path=path),mock.patch('scripts.pablo_work_plan.bridge_key',return_value='fixture'),mock.patch('scripts.pablo_work_plan.urlopen',return_value=response) as call,contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(main(['--task-id','fixture',*args]),0)
                req=call.call_args.args[0];self.assertTrue(req.full_url.endswith(path));self.assertEqual(req.get_method(),'POST')
                body=json.loads(req.data)
                if action:self.assertEqual(body['action'],action);self.assertEqual(body['request_id'],'fixture')

    def test_timeout_does_not_blindly_resubmit(self):
        with mock.patch('scripts.pablo_work_plan.bridge_key',return_value='fixture'),mock.patch('scripts.pablo_work_plan.urlopen',side_effect=TimeoutError()) as call,contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(['--task-id','fixture','--advance']),1);self.assertEqual(call.call_count,1)


if __name__=='__main__':unittest.main()
