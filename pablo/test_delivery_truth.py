"""No live sender, browser, desktop or production database is used by these tests."""
import ast
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import pablo_marketing_playbooks as playbooks


class DeliveryTruthTests(unittest.TestCase):
    def setUp(self):
        self.pipeline = mock.Mock()
        self.pipeline.get_campaign.return_value = {
            'status': 'APPROVED', 'channel': 'email', 'recipient_target': 'fixture@example.invalid',
            'subject': 'Fixture', 'message_body': 'Fixture draft',
        }
        self.pipeline_patch = mock.patch.object(playbooks, 'MarketingPipeline', self.pipeline)
        self.pipeline_patch.start()
        self.addCleanup(self.pipeline_patch.stop)
        self.browser = mock.patch.object(playbooks.PabloBrowserGrounding, 'get_instance').start()
        self.addCleanup(mock.patch.stopall)

    def test_simulation_does_not_send_change_status_or_claim_proof(self):
        result = playbooks.MarketingPlaybooks.execute_campaign_delivery(1, simulated=True)
        self.assertTrue(result['ok'])
        self.assertEqual(result['status'], 'SIMULATED')
        self.assertFalse(result['verified'])
        self.assertFalse(result['delivered'])
        self.assertEqual(result['screenshot_path'], '')
        self.pipeline.update_campaign_status.assert_not_called()
        self.browser.assert_not_called()
        self.assertEqual(self.pipeline.log_execution.call_args.kwargs['status'], 'SIMULATED')

    def test_unimplemented_live_channels_never_claim_sent(self):
        for channel in ('email', 'web_form', 'instagram', 'linkedin', 'unknown'):
            self.pipeline.get_campaign.return_value['channel'] = channel
            result = playbooks.MarketingPlaybooks.execute_campaign_delivery(1, simulated=False)
            self.assertFalse(result['ok'], channel)
            self.assertEqual(result['status'], 'UNSUPPORTED')
            self.assertFalse(result['verified'])
            self.assertFalse(result['delivered'])
        self.pipeline.update_campaign_status.assert_not_called()
        self.browser.assert_not_called()

    def test_unapproved_draft_and_missing_inputs_are_refused(self):
        for state in ('DRAFTED', 'PENDING_APPROVAL', 'REJECTED', 'SENT'):
            self.pipeline.get_campaign.return_value['status'] = state
            self.assertEqual(playbooks.MarketingPlaybooks.execute_campaign_delivery(1, True)['status'], 'NOT_APPROVED')
        self.pipeline.get_campaign.return_value = None
        self.assertEqual(playbooks.MarketingPlaybooks.execute_campaign_delivery(1, True)['status'], 'NOT_FOUND')
        for missing in ('message_body', 'recipient_target'):
            self.pipeline.get_campaign.return_value = {'status': 'APPROVED', 'message_body': 'fixture', 'recipient_target': 'fixture'}
            self.pipeline.get_campaign.return_value[missing] = ''
            self.assertEqual(playbooks.MarketingPlaybooks.execute_campaign_delivery(1, True)['status'], 'INVALID_DRAFT')
        self.pipeline.log_execution.assert_not_called()
        self.browser.assert_not_called()

    def test_legacy_social_publish_handler_returns_unsupported(self):
        # Isolate just the pure compatibility function instead of importing the Windows node.
        source = Path(__file__).with_name('hermes_node.py').read_text(encoding='utf-8')
        node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'action_social_post')
        namespace = {}
        exec(compile(ast.Module(body=[node], type_ignores=[]), 'publish-fixture', 'exec'), namespace)
        result = namespace['action_social_post']({'text': 'fixture'})
        self.assertFalse(result['ok'])
        self.assertFalse(result['result']['posted'])
        self.assertEqual(result['status'], 'UNSUPPORTED')


class BackupCoverageTests(unittest.TestCase):
    def test_new_working_data_is_included_as_consistent_snapshots(self):
        from scripts import jeff_backup as backup
        import sqlite3
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            expected = []
            for relative in ('jeff-beyin/state.sqlite3', 'cybergeneos-data/cgos.db'):
                path = home / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                db = sqlite3.connect(path)
                try:
                    db.execute('CREATE TABLE fixture (x INTEGER)')
                    db.commit()
                finally:
                    db.close()
                expected.append(path)
            self.assertEqual(backup.find_databases(home, opt_trees=()), sorted(expected))
            copied, errors = backup.snapshot_databases(expected, home / 'snapshots', lambda _: None)
            self.assertFalse(errors)
            self.assertEqual(set(copied), {str(path) for path in expected})
            for snapshot in copied.values():
                self.assertEqual(backup._integrity(snapshot), 'ok')
            roots = backup.trees(home, opt_trees=())
            for name in ('jeff-beyin', 'cybergeneos-data', 'cybergeneos'):
                self.assertIn(home / name, roots)


if __name__ == '__main__':
    unittest.main()
