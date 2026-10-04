"""Watchdog certification requires readable evidence and literal booleans."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock

from scripts import system_watchdog as watchdog


class WatchdogEvidenceIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def test_unreadable_or_failed_journal_is_not_healthy(self):
        def unreadable(*args,**kwargs):raise OSError('SECRET')
        for runner in (unreadable,lambda *a,**k:SimpleNamespace(returncode=1,stdout='',stderr='SECRET')):
            with self.subTest(runner=runner):
                ok,detail=watchdog.telegram_not_fighting(runner=runner)()
                self.assertFalse(ok);self.assertNotIn('SECRET',detail)

    def test_future_backup_timestamp_is_not_fresh(self):
        path=self.root/'jeff-backup-fixture.tar.gz';path.write_bytes(b'fixture')
        now=path.stat().st_mtime-3600
        self.assertFalse(watchdog.backup_fresh(self.root,now=lambda:now)()[0])

    def test_future_offsite_marker_is_not_fresh(self):
        path=self.root/'.offsite-copy-ok';path.write_text('fixture')
        now=path.stat().st_mtime-3600
        self.assertFalse(watchdog.marker_fresh(path,now=lambda:now)()[0])

    def test_directories_cannot_impersonate_backup_or_marker(self):
        (self.root/'jeff-backup-fake.tar.gz').mkdir()
        marker=self.root/'.offsite-copy-ok';marker.mkdir()
        self.assertFalse(watchdog.backup_fresh(self.root)()[0])
        self.assertFalse(watchdog.marker_fresh(marker)()[0])

    def test_nonboolean_probe_cannot_certify_recovery(self):
        for value in ('false',1,[],None):
            with self.subTest(value=value):
                check=watchdog.Check('fixture','fixture','fixture',lambda:(value,'SECRET'))
                state,events=watchdog.evaluate([check],{'fixture':{'ok':False,'since':900,'alerted':True}},1000)
                self.assertIs(state['fixture']['ok'],False)
                self.assertFalse(any(event[0]=='up' for event in events))
                self.assertNotIn('SECRET',state['fixture']['detail'])

    def test_invalid_chat_cache_requires_an_actual_answer(self):
        memo=self.root/'chat.json'
        for timestamp,ok in ((2000,True),(float('nan'),True),(True,True),(1000,'false')):
            with self.subTest(timestamp=timestamp,ok=ok):
                memo.write_text(json.dumps({'ts':timestamp,'ok':ok,'detail':'cached success'}))
                calls=[]
                def opener(*args,**kwargs):
                    calls.append(1)
                    return MagicMock(__enter__=lambda s:SimpleNamespace(read=lambda:b'{"status":"ok","reply":""}'),__exit__=lambda *a:False)
                measured,detail=watchdog.chat_answers(memo=memo,now=lambda:1100,opener=opener)()
                self.assertFalse(measured);self.assertEqual(len(calls),1)
                self.assertNotEqual(detail,'cached success')

    def test_timestamp_only_backup_and_marker_fail_but_chat_cache_passes(self):
        backup=self.root/'jeff-backup-real.tar.gz';backup.write_bytes(b'fixture')
        marker=self.root/'.offsite-copy-ok';marker.write_text('fixture')
        now=max(backup.stat().st_mtime,marker.stat().st_mtime)+1
        self.assertFalse(watchdog.backup_fresh(self.root,now=lambda:now)()[0])
        self.assertFalse(watchdog.marker_fresh(marker,now=lambda:now)()[0], 'Timestamp-only marker is not a hash receipt')
        self.assertTrue(watchdog.telegram_not_fighting(runner=lambda *a,**k:SimpleNamespace(returncode=0,stdout='no conflicts'))()[0])
        memo=self.root/'chat.json';memo.write_text(json.dumps({'ts':1000,'ok':True,'detail':'measured answer'}))
        def unused(*args,**kwargs):raise AssertionError('Cache should avoid a new model call')
        self.assertTrue(watchdog.chat_answers(memo=memo,now=lambda:1100,opener=unused)()[0])


if __name__=='__main__':unittest.main()
