import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from scripts.jeff_backup import verify_core_sources


class StreamVerificationTests(unittest.TestCase):
    def archive(self,root,wrong=False,duplicate=False,link=False,late=False):
        path=Path(root)/'fixture.tar.gz';content=b'bounded core fixture'
        manifest=json.dumps({'core.py':hashlib.sha256(content).hexdigest()}).encode()
        with tarfile.open(path,'w:gz') as tar:
            def write(name,data):
                info=tarfile.TarInfo(name);info.size=len(data);tar.addfile(info,io.BytesIO(data))
            if not late:write('etc/CORE-SOURCES.json',manifest)
            if link:
                info=tarfile.TarInfo('core.py');info.type=tarfile.SYMTYPE;info.linkname='/outside';tar.addfile(info)
            else:write('core.py',b'wrong' if wrong else content)
            if duplicate:write('core.py',content)
            if late:write('etc/CORE-SOURCES.json',manifest)
        return path

    def test_correct_sources_verified_without_random_seeks(self):
        with tempfile.TemporaryDirectory() as root:
            path=self.archive(root);opener=tarfile.open
            with patch('scripts.jeff_backup.tarfile.open',wraps=opener) as opened:self.assertEqual(verify_core_sources(path),[])
            self.assertEqual(opened.call_args.args[1],'r|gz')

    def test_wrong_or_duplicate_or_link_cannot_pass(self):
        for options in ({'wrong':True},{'duplicate':True},{'link':True}):
            with tempfile.TemporaryDirectory() as root:self.assertTrue(verify_core_sources(self.archive(root,**options)))

    def test_missing_or_late_manifest_and_truncated_archive_do_not_pass(self):
        with tempfile.TemporaryDirectory() as root:
            path=self.archive(root,late=True);self.assertTrue(verify_core_sources(path))
            path.write_bytes(b'invalid gzip');self.assertTrue(verify_core_sources(path))
