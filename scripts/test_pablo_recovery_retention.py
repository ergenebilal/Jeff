import hashlib
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
import zipfile
from pablo.pablo_recovery import CORE, snapshot, validate
from scripts.pablo_recovery_retention import record_verified, prune, safe_path, RECEIPT


class RecoveryRetentionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.live = self.root/'live'; self.live.mkdir()
        self.storage = self.root/'storage'; self.storage.mkdir()
        for name in CORE:
            target = self.live/name
            if name.endswith('.sqlite3'):
                with closing(sqlite3.connect(target)) as db: db.execute('CREATE TABLE fixture (id INTEGER)'); db.commit()
            else: target.write_text('# inert source\n' if name.endswith('.py') else '{}')
        (self.live/'deployment.json').write_text(json.dumps({'commit':'a'*40}))

    def capsule(self, index, layout='local'):
        name = '20261004T000000Z-'+format(index,'032x'); base = self.storage/name
        image = base
        if layout == 'remote': base.mkdir(); image = base/'snapshot'
        snapshot(self.live, image, collect_packages=False)
        manifest = validate(image); archive = base/'windows-snapshot.zip'
        with zipfile.ZipFile(archive,'w') as bundle:
            for member in ['manifest.json']+[e['path'] for e in manifest['entries']]: bundle.write(image/member,arcname=member)
        proof = {'ok':True,'remote_manifest_verified':True,'archive_bytes':archive.stat().st_size,
                 'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'source_release':'a'*40,'verified_at':100+index}
        record_verified(base, self.storage, layout, proof, validate)
        return base

    def test_real_capsules_bound_to_fourteen_and_manual_history_preserved(self):
        images = [self.capsule(i) for i in range(16)]
        historical = self.storage/'P25-20261004'; historical.mkdir(); (historical/'keep').write_text('manual history')
        result = prune(self.storage, images[-1].name, validate)
        self.assertEqual(result['removed_verified_images'],2)
        self.assertEqual(result['retained_verified_images'],14)
        self.assertTrue(historical.is_dir()); self.assertFalse(images[0].exists()); self.assertTrue(images[-1].is_dir())
        self.assertEqual(prune(self.storage,images[-1].name,validate)['removed_verified_images'],0)

    def test_current_preserved_even_if_not_newest(self):
        images = [self.capsule(i) for i in range(16)]
        result = prune(self.storage,images[0].name,validate)
        self.assertTrue(images[0].exists()); self.assertEqual(result['retained_verified_images'],15)

    def test_bad_current_cannot_delete_previous_good_capsules(self):
        images = [self.capsule(i) for i in range(3)]
        (images[-1]/'files/config.json').write_text('damaged')
        with self.assertRaises(ValueError): prune(self.storage,images[-1].name,validate,keep=1)
        self.assertTrue(all(image.exists() for image in images))

    def test_damaged_old_archive_and_unknown_content_are_preserved(self):
        images = [self.capsule(i) for i in range(5)]
        (images[0]/'windows-snapshot.zip').write_bytes(b'corrupt archive')
        (images[1]/'unknown-private-file').write_text('never delete this')
        (images[2]/'unknown-empty-directory').mkdir()
        result = prune(self.storage,images[-1].name,validate,keep=1)
        self.assertEqual(result['unmanaged_or_invalid_generated_images_preserved'],3)
        self.assertTrue(all(image.exists() for image in images[:3]))
        self.assertFalse(images[3].exists())

    def test_remote_layout_and_unverified_receipt(self):
        images = [self.capsule(i,'remote') for i in range(3)]
        receipt = json.loads((images[0]/RECEIPT).read_text()); receipt['remote_manifest_verified']='true'
        (images[0]/RECEIPT).write_text(json.dumps(receipt))
        result = prune(self.storage,images[-1].name,validate,keep=1)
        self.assertTrue(images[0].exists()); self.assertFalse(images[1].exists())
        self.assertEqual(result['unmanaged_or_invalid_generated_images_preserved'],1)

    def test_redirect_and_escape_cannot_be_removed(self):
        current = self.capsule(2); outside = self.root/'outside'; outside.mkdir(); (outside/'keep').write_text('safe')
        with self.assertRaises(ValueError): safe_path(outside,self.storage)
        if os.name == 'nt':
            import subprocess
            link = self.storage/('20261004T000000Z-'+format(1,'032x'))
            command = "New-Item -ItemType Junction -Path '"+str(link)+"' -Target '"+str(outside)+"' | Out-Null"
            subprocess.run(['powershell','-NoProfile','-Command',command],check=True,capture_output=True)
        else:
            link = self.storage/('20261004T000000Z-'+format(1,'032x')); link.symlink_to(outside,target_is_directory=True)
        with self.assertRaises(ValueError): safe_path(link,self.storage)
        result = prune(self.storage,current.name,validate,keep=1)
        self.assertTrue((outside/'keep').exists()); self.assertEqual(result['removed_verified_images'],0)
        # Remove only the verified link itself so temporary-directory cleanup cannot traverse it.
        if os.name == 'nt': link.rmdir()
        else: link.unlink()

    def test_future_receipt_and_invalid_limits_preserve_everything(self):
        image = self.capsule(1)
        receipt = json.loads((image/RECEIPT).read_text()); receipt['verified_at']=float('nan')
        (image/RECEIPT).write_text(json.dumps(receipt))
        for limit in (True,0,31):
            with self.assertRaises(ValueError): prune(self.storage,image.name,validate,keep=limit)
        with self.assertRaises(ValueError): prune(self.storage,image.name,validate)
        self.assertTrue(image.is_dir())
