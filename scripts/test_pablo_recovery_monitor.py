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
        for key in ('local_retention','remote_retention'):
            self.assertFalse(report_ok(report|{key:{'ok':False}},100,expected))
            self.assertFalse(report_ok(report|{key:{'current_image_preserved':False}},100,expected))
            self.assertTrue(report_ok(report|{key:{'current_image_preserved':True}},100,expected))

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
            self.assertFalse(result['ok']);self.assertEqual(result['failure_class'],'ValueError');self.assertEqual(result['failure_phase'],'snapshot')
            self.assertNotIn('private fixture secret',report.read_text());self.assertEqual(ssh.call_count,1)
            self.assertNotIn('windows-snapshot.zip',ssh.call_args.args[0])


class TransferFailureTests(unittest.TestCase):
    def verify_failure(self, timeout, response=None):
        import hashlib
        import sqlite3
        import subprocess
        from contextlib import closing
        from types import SimpleNamespace
        import pablo_recovery
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);live=root/'live';live.mkdir()
            for name in set(pablo_recovery.CORE)|set(LOADED):
                p=live/name
                if name.endswith('.sqlite3'):
                    with closing(sqlite3.connect(p)) as db:
                        db.execute('CREATE TABLE anonymous_fixture(id INTEGER)');db.commit()
                else:p.write_text('# anonymous fixture\n' if name.endswith('.py') else '{}')
            (live/'deployment.json').write_text(json.dumps({'commit':'a'*40}))
            loaded={n:hashlib.sha256((live/n).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for n in LOADED}
            ping={'ok':True,'result':'pong','source_commit':'a'*40,'loaded_source_sha256':loaded,'process_started_at':100}
            before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in live.iterdir()}
            actual_snapshot=pablo_recovery.snapshot
            def make_private(p):p.mkdir(mode=0o700);return p
            def transfer(*args,**kwargs):
                self.assertEqual(args[0][0],'scp')
                if timeout is True:raise subprocess.TimeoutExpired('anonymous-transfer',kwargs['timeout'])
                return SimpleNamespace(returncode=0 if timeout=='verification' else 1)
            with patch.object(pablo_recovery,'private_directory',side_effect=make_private),patch.object(pablo_recovery,'snapshot',side_effect=lambda a,b:actual_snapshot(a,b,collect_packages=False)),patch('scripts.pablo_recovery_monitor.remote') as ssh,patch('scripts.pablo_recovery_monitor.urllib.request.urlopen') as http,patch('scripts.pablo_recovery_monitor.subprocess.run',side_effect=transfer) as copy:
                http.return_value.__enter__.return_value.read.return_value=json.dumps(ping).encode()
                if timeout=='verification':ssh.side_effect=[None,response,None]
                result=run(live,root/'storage',root/'report.json')
            self.assertFalse(result['ok'])
            self.assertEqual(result['failure_phase'],'remote_archive_verification' if timeout=='verification' else 'archive_transfer')
            self.assertEqual(result['failure_class'],'TimeoutExpired' if timeout is True else 'RuntimeError')
            self.assertGreaterEqual(result['archive_transfer_seconds'],0)
            self.assertEqual(copy.call_count,1)
            self.assertEqual(ssh.call_count,3 if timeout=='verification' else 2)
            self.assertFalse(result['workers_started'])
            images=list((root/'storage').glob('*/windows-snapshot.zip'))
            self.assertEqual(len(images),1)
            self.assertEqual(images[0].stat().st_size,result['archive_bytes'])
            self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in live.iterdir()})

    def test_timeout_preserves_local_archive_and_cannot_get_success(self):
        self.verify_failure(True)

    def test_failed_transfer_is_not_retried_or_verified(self):
        self.verify_failure(False)

    def test_empty_verification_cannot_crash_failure_reporting(self):
        self.verify_failure('verification',None)

    def test_foreign_verification_type_cannot_get_success(self):
        self.verify_failure('verification',['foreign receipt'])
