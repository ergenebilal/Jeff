import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.pablo_recovery_monitor import LOADED,report_ok,check_runtime,run


class RecoveryMonitorTests(unittest.TestCase):
    def test_only_current_complete_recent_remote_verified_report_passes(self):
        expected={n:'a'*64 for n in LOADED}
        report={'version':1,'ok':True,'remote_manifest_verified':True,'verified_at':100,'loaded_source_sha256':expected}
        self.assertTrue(report_ok(report,100,expected))
        for change in ({'ok':'true'},{'remote_manifest_verified':False},{'verified_at':101},{'verified_at':-200000},
                       {'verified_at':float('nan')},{'loaded_source_sha256':{}},{'version':2}):
            self.assertFalse(report_ok(report|change,100,expected))
        self.assertFalse(report_ok(report,100,expected|{LOADED[0]:'b'*64}))

    def test_runtime_release_and_coverage_cannot_be_assumed(self):
        manifest={'source_release':'a'*40};ping={'ok':True,'result':'pong','source_commit':'a'*40,'loaded_source_sha256':{n:'b'*64 for n in LOADED}}
        self.assertEqual(check_runtime(manifest,ping),ping['loaded_source_sha256'])
        for change in ({'source_commit':'c'*40},{'loaded_source_sha256':{}},{'ok':False}):
            with self.assertRaises(ValueError):check_runtime(manifest,ping|change)

    def test_failed_local_snapshot_never_uploads_archive_or_claims_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);report=root/'report.json'
            with patch('pablo_recovery.snapshot',side_effect=ValueError('private fixture secret')),patch('scripts.pablo_recovery_monitor.remote') as ssh,patch('scripts.pablo_recovery_monitor.urllib.request.urlopen') as ping:
                ping.return_value.__enter__.return_value.read.return_value=b'{}'
                result=run(root,root/'storage',report)
            self.assertFalse(result['ok']);self.assertEqual(result['failure_class'],'ValueError')
            self.assertNotIn('private fixture secret',report.read_text());self.assertEqual(ssh.call_count,1)
            self.assertNotIn('windows-snapshot.zip',ssh.call_args.args[0])
