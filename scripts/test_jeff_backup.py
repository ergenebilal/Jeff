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
        for name in jb.CORE_SOURCE_PATHS:
            path = self.home / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('fixture core source ' + name)
        for name in jb.CORE_DATABASE_PATHS:
            make_db(self.home / name)

    def run(self, **kw):
        logs = []
        # Fixture backups test archive/database logic; installed-package discovery has its own tests.
        from unittest.mock import patch
        with patch.object(jb, 'package_inventory', return_value={}):
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

    def test_extra_dropin_files_keep_their_folder_in_the_archive_name(self):
        dropin = self.fx.home / 'x.service.d' / '10-a.conf'
        dropin.parent.mkdir()
        dropin.write_text('[Service]\n')
        plain = self.fx.home / 'jeff-bridge.env'
        plain.write_text('K=1\n')
        code, _ = self.fx.run(extra_files=[dropin, plain])
        names = self.fx.names()
        self.assertIn('etc/x.service.d__10-a.conf', names)
        self.assertIn('etc/jeff-bridge.env', names)

    def test_crontab_is_part_of_the_inventory(self):
        from types import SimpleNamespace
        fake = lambda cmd, **kw: SimpleNamespace(stdout='0 3 * * * job\n' if cmd[0] == 'crontab' else '')  # noqa: E731
        self.assertEqual(jb.package_inventory(self.fx.home, runner=fake)['etc/crontab-hermes.txt'], '0 3 * * * job\n')

    def test_manifests_let_restore_put_everything_back(self):
        etc_file = self.fx.home / 'etc-demo' / 'svc.service'
        etc_file.parent.mkdir()
        etc_file.write_text('[Unit]' + chr(10))
        code, _ = self.fx.run(extra_files=[etc_file])
        self.assertEqual(code, 0)
        stage, target = Path(self._d.name) / 'stage', Path(self._d.name) / 'newroot'
        with tarfile.open(self.fx.latest()) as tar:
            tar.extractall(stage)
        logs = []
        self.assertEqual(jb.restore(stage, target, apply=False, log=logs.append), 0)    # rehearsal writes nothing
        self.assertFalse(target.exists())
        self.assertEqual(jb.restore(stage, target, apply=True, log=logs.append), 0)
        self.assertTrue(any(p.name == 'state.db' for p in target.rglob('state.db')))
        self.assertTrue(any(p.name == 'svc.service' for p in target.rglob('svc.service')))
        before = sorted(str(p) for p in target.rglob('*'))
        self.assertEqual(jb.restore(stage, target, apply=True, log=logs.append), 0)     # second run leaves everything alone
        self.assertEqual(before, sorted(str(p) for p in target.rglob('*')))
        self.assertTrue(any('exists, left alone' in m for m in logs))

    def test_restore_refuses_a_folder_that_is_not_an_unpacked_archive(self):
        self.assertEqual(jb.restore(Path(self._d.name) / 'nothing', Path(self._d.name) / 'r', log=lambda m: None), 1)

    def test_etc_names_keep_their_full_location(self):
        self.assertEqual(jb.etc_arcname('/etc/systemd/system/hermes-gateway.service.d/10-v0215.conf'),
                         'etc/systemd__system__hermes-gateway.service.d__10-v0215.conf')
        self.assertEqual(jb.etc_arcname('/etc/fail2ban/jail.local'), 'etc/fail2ban__jail.local')
        self.assertEqual(jb.etc_arcname('/etc/jeff-bridge.env'), 'etc/jeff-bridge.env')

    def test_backup_and_restore_ignore_editor_backup_files(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / 'a.env').write_text('x')
            (Path(d) / 'a.env.bak-2026').write_text('x')
            self.assertEqual([Path(f).name for f in jb.etc_files([str(Path(d) / 'a.env*')])], ['a.env'])

    def test_unreadable_system_file_does_not_kill_the_backup(self):
        import io as _io
        from types import SimpleNamespace
        logs = []
        buf = _io.BytesIO()
        with tarfile.open(fileobj=buf, mode='w:gz') as tar:
            # a path that cannot be added and where sudo also fails
            ok = jb.add_system_file(tar, '/nonexistent/secret.conf', lambda: 0, logs.append,
                                    runner=lambda *a, **k: SimpleNamespace(returncode=1, stdout=b''))
        self.assertFalse(ok)
        self.assertTrue(any('could not read' in m for m in logs))

    def test_sudo_fallback_reads_a_root_only_file(self):
        import io as _io
        from types import SimpleNamespace
        buf = _io.BytesIO()
        with tarfile.open(fileobj=buf, mode='w:gz') as tar:
            self.assertTrue(jb.add_system_file(tar, '/nonexistent/root-only.conf', lambda: 5, lambda m: None,
                                               runner=lambda *a, **k: SimpleNamespace(returncode=0, stdout=b'secret')))
        buf.seek(0)
        with tarfile.open(fileobj=buf) as tar:
            self.assertEqual(tar.extractfile('etc/root-only.conf').read(), b'secret')

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
        self.assertIn('4 databases restored and checked', ' '.join(logs))

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
