import os
import sqlite3
import tarfile
import tempfile
import time
import unittest
from pathlib import Path

from scripts import jeff_backup as jb


def make_db(path, rows=3):
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path)
    db.execute('CREATE TABLE t (x INTEGER)')
    db.executemany('INSERT INTO t VALUES (?)', [(i,) for i in range(rows)])
    db.commit()
    db.close()


class Fixture:
    """A miniature Jeff home directory."""

    def __init__(self, root):
        self.home = Path(root) / 'home'
        self.dest = Path(root) / 'backups'
        h = self.home / '.hermes'
        (h).mkdir(parents=True)
        (h / 'config.yaml').write_text('model: x\n')
        (h / 'gateway.env').write_text('TELEGRAM_BOT_TOKEN=secret\n')
        make_db(h / 'state.db', rows=5)
        make_db(h / 'profiles' / 'critic' / 'state.db')
        (h / 'skills').mkdir()
        (h / 'skills' / 'note.md').write_text('skill')
        for heavy in ('node', 'hermes-agent', 'logs', 'cache', 'backups'):
            (h / heavy).mkdir()
            (h / heavy / 'big.bin').write_bytes(b'x' * 100)
        (h / 'debug.log').write_text('noise')
        (self.home / 'jeff_cognitive').mkdir()
        (self.home / 'jeff_cognitive' / 'core.py').write_text('print(1)')

    def run(self, **kw):
        logs = []
        code = jb.run(self.home, self.dest, log=logs.append, opt_trees=(), **kw)
        return code, logs

    def latest(self):
        return sorted(self.dest.glob('jeff-backup-*.tar.gz'))[-1]

    def names(self):
        with tarfile.open(self.latest()) as tar:
            return set(tar.getnames())


class BackupTests(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.fx = Fixture(self._d.name)
        self.prefix = str(self.fx.home).lstrip('/').replace('\\', '/').replace(':', '')

    def tearDown(self):
        self._d.cleanup()

    def test_brain_is_in_the_backup(self):
        code, _ = self.fx.run()
        self.assertEqual(code, 0)
        names = {n.replace('\\', '/') for n in self.fx.names()}
        joined = '\n'.join(names)
        for needle in ('.hermes/config.yaml', '.hermes/gateway.env', '.hermes/skills/note.md', 'jeff_cognitive/core.py'):
            self.assertIn(needle, joined)

    def test_databases_are_snapshotted_and_readable(self):
        self.fx.run()
        with tarfile.open(self.fx.latest()) as tar, tempfile.TemporaryDirectory() as out:
            dbs = [n for n in tar.getnames() if n.startswith('db/') and n.endswith('state.db')]
            self.assertEqual(len(dbs), 2)
            tar.extractall(out)
            for name in dbs:
                conn = sqlite3.connect(Path(out) / name)
                self.assertEqual(conn.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
                self.assertGreater(conn.execute('SELECT count(*) FROM t').fetchone()[0], 0)
                conn.close()

    def test_live_database_files_are_not_copied_raw(self):
        self.fx.run()
        raw = [n for n in self.fx.names() if n.endswith('.db') and not n.startswith('db/')]
        self.assertEqual(raw, [])

    def test_heavy_reinstallable_things_and_logs_are_skipped(self):
        self.fx.run()
        joined = '\n'.join(self.fx.names())
        for skipped in ('/node/', '/hermes-agent/', '/logs/', '/cache/', '/backups/', 'debug.log'):
            self.assertNotIn(skipped, joined)

    def test_missing_required_file_fails_and_leaves_no_archive(self):
        (self.fx.home / '.hermes' / 'gateway.env').unlink()
        code, logs = self.fx.run()
        self.assertEqual(code, 1)
        self.assertEqual(list(self.fx.dest.glob('jeff-backup-*.tar.gz')), [])
        self.assertTrue(any('missing required' in m for m in logs))
        self.assertEqual([p for p in self.fx.dest.iterdir() if p.name.startswith('.')], [])   # temp files cleaned

    def test_corrupt_database_is_reported_but_the_rest_is_still_saved(self):
        (self.fx.home / '.hermes' / 'profiles' / 'critic' / 'state.db').write_bytes(b'not a database' * 50)
        code, logs = self.fx.run()
        self.assertEqual(code, 3)
        self.assertTrue(self.fx.latest().exists())
        self.assertTrue(any('1 failed' in m for m in logs))

    def test_damaged_index_is_kept_and_reported_not_dropped(self):
        # The real-world case: the data is fine but an FTS index is malformed. The copy must still be saved.
        real = jb._integrity
        jb._integrity = lambda path: 'malformed inverted index for FTS5 table main.x' if 'state' in str(path) else real(path)
        try:
            code, logs = self.fx.run()
        finally:
            jb._integrity = real
        self.assertEqual(code, 3)
        self.assertIn('db/' + jb.flat_name(self.fx.home / '.hermes' / 'state.db'), self.fx.names())
        self.assertTrue(any(m.startswith('WARNING:') and 'malformed' in m for m in logs))

    def test_package_inventory_is_stored_and_a_missing_tool_is_not_fatal(self):
        from types import SimpleNamespace
        fake = lambda cmd, **kw: SimpleNamespace(stdout='mcp==1.29.1\n' if 'freeze' in cmd else '')  # noqa: E731
        inv = jb.package_inventory(self.fx.home, runner=fake)
        self.assertIn('mcp==1.29.1', inv['etc/pip-freeze-jeff-site.txt'])
        self.assertNotIn('etc/node-global.txt', inv)                      # empty output is simply skipped
        boom = lambda cmd, **kw: (_ for _ in ()).throw(FileNotFoundError('npm'))  # noqa: E731
        self.assertEqual(jb.package_inventory(self.fx.home, runner=boom), {})

    def test_retention_keeps_only_the_newest(self):
        base = time.time()
        for i in range(4):
            self.fx.run(keep=2) if False else jb.run(self.fx.home, self.fx.dest, keep=2, log=lambda m: None,
                                                    opt_trees=(), now=lambda i=i: base + i * 100)
        self.assertEqual(len(list(self.fx.dest.glob('jeff-backup-*.tar.gz'))), 2)

    @unittest.skipIf(os.name == 'nt', 'POSIX permissions')
    def test_archive_and_folder_are_private(self):
        self.fx.run()
        self.assertEqual(oct(self.fx.latest().stat().st_mode & 0o777), '0o600')
        self.assertEqual(oct(self.fx.dest.stat().st_mode & 0o777), '0o700')


class RestoreDrillTests(BackupTests):
    def drill(self, **kw):
        logs = []
        return jb.verify_latest(self.fx.dest, self.fx.home, log=logs.append, **kw), logs

    def test_good_backup_passes_the_drill(self):
        self.fx.run()
        code, logs = self.drill()
        self.assertEqual(code, 0)
        self.assertIn('2 databases restored and checked', ' '.join(logs))

    def test_no_backup_fails(self):
        self.fx.dest.mkdir(parents=True)
        self.assertEqual(self.drill()[0], 1)

    def test_old_backup_is_flagged(self):
        self.fx.run()
        code, logs = self.drill(now=lambda: time.time() + 72 * 3600)
        self.assertEqual(code, 1)
        self.assertTrue(any('hours old' in m for m in logs))

    def test_archive_missing_the_brain_fails_the_drill(self):
        self.fx.run()
        arc = self.fx.latest()
        stripped = arc.with_name('jeff-backup-99990101-000000.tar.gz')
        with tarfile.open(arc) as src, tarfile.open(stripped, 'w:gz') as dst:
            for m in src.getmembers():
                if 'gateway.env' not in m.name:
                    dst.addfile(m, src.extractfile(m) if m.isfile() else None)
        code, logs = self.drill()
        self.assertEqual(code, 1)
        self.assertTrue(any('gateway.env' in m for m in logs))

    def test_unreadable_archive_fails(self):
        self.fx.dest.mkdir(parents=True)
        (self.fx.dest / 'jeff-backup-20260101-000000.tar.gz').write_bytes(b'garbage')
        self.assertEqual(self.drill()[0], 1)


if __name__ == '__main__':
    unittest.main()
