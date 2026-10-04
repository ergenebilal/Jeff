import json
import hashlib
from pathlib import Path
import tempfile
import unittest
from scripts.system_watchdog import marker_fresh


class OffsiteReceiptTests(unittest.TestCase):
    def test_only_recent_literal_hash_receipt_bound_to_real_archive_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);archive=root/'jeff-backup-20261004-170000.tar.gz';archive.write_bytes(b'fixture')
            now=archive.stat().st_mtime+1
            data={'version':1,'client_hash_verified':True,'archive':archive.name,'archive_sha256':hashlib.sha256(b'fixture').hexdigest(),
                  'archive_bytes':7,'server_mtime_seconds':int(archive.stat().st_mtime),'verified_at':now}
            marker=root/'.offsite-copy-ok';marker.write_text(json.dumps(data))
            (root/'.verified-backup.json').write_text(json.dumps({'version':1,'ok':True,'archive':archive.name,
                'archive_sha256':data['archive_sha256'],'archive_bytes':7,'archive_mtime_ns':archive.stat().st_mtime_ns}))
            self.assertTrue(marker_fresh(marker,now=lambda:now)()[0])
            for change in ({'client_hash_verified':'true'},{'verified_at':now+1},{'verified_at':float('nan')},
                           {'archive':'../outside'},{'archive_bytes':False},{'server_mtime_seconds':0},{'archive_sha256':'bad'},{'archive_sha256':'0'*64}):
                marker.write_text(json.dumps(data|change));self.assertFalse(marker_fresh(marker,now=lambda:now)()[0])
            marker.write_text(json.dumps(data));archive.write_bytes(b'changed-size')
            self.assertFalse(marker_fresh(marker,now=lambda:now)()[0])

    def test_marker_file_date_or_new_symlink_is_not_content_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);marker=root/'.offsite-copy-ok';marker.write_text('fresh filename')
            self.assertFalse(marker_fresh(marker)()[0])
            archive=root/'jeff-backup-20261004-170000.tar.gz';archive.write_bytes(b'fixture');mtime=archive.stat().st_mtime
            marker.write_text(json.dumps({'version':1,'client_hash_verified':True,'archive':archive.name,'archive_sha256':'a'*64,
                                         'archive_bytes':7,'server_mtime_seconds':int(mtime),'verified_at':mtime}))
            archive.unlink();self.assertFalse(marker_fresh(marker)()[0])
