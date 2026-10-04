import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch
from scripts import jeff_backup as backup
from scripts.system_watchdog import backup_fresh


class BackupReceiptTests(unittest.TestCase):
    def test_metadata_cannot_replace_content_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);archive=root/'jeff-backup-20261004-170000.tar.gz';archive.write_bytes(b'fixture')
            now=time.time();core={'fixture':'a'*64}
            with patch.object(backup,'core_sources',return_value=core):
                self.assertFalse(backup_fresh(root,now=lambda:now)()[0])
                receipt=backup.verification_receipt(archive,core,True,'archive_core_crc_and_consistent_database_snapshots',now=lambda:now)
                self.assertTrue(backup_fresh(root,now=lambda:now)()[0])
                for changed in ({'ok':'true'},{'verified_at':now+1},{'verified_at':float('nan')},
                                {'core_sources':{}},{'archive':'../fixture'},{'archive_bytes':0},{'archive_sha256':'bad'},{'method':'invented'}):
                    (root/'.verified-backup.json').write_text(json.dumps(receipt|changed))
                    self.assertFalse(backup.read_verification_receipt(root,now=now)[0])
                (root/'.verified-backup.json').write_text(json.dumps(receipt))
                archive.write_bytes(b'corrupted')
                self.assertFalse(backup.read_verification_receipt(root,now=now)[0])

    def test_new_core_or_unverified_newer_archive_invalidates_old_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);archive=root/'jeff-backup-20261004-170000.tar.gz';archive.write_bytes(b'fixture')
            now=time.time();core={'fixture':'a'*64};backup.verification_receipt(archive,core,True,'archive_core_crc_and_consistent_database_snapshots',now=lambda:now)
            with patch.object(backup,'core_sources',return_value={'fixture':'b'*64}):self.assertFalse(backup.read_verification_receipt(root,now=now)[0])
            (root/'jeff-backup-20261004-180000.tar.gz').write_bytes(b'new unverified')
            with patch.object(backup,'core_sources',return_value=core):self.assertFalse(backup.read_verification_receipt(root,now=now)[0])
