import tempfile
import unittest
from pathlib import Path

from scripts import pablo_drift as pd


def write(root, name, text):
    path = Path(root) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


class DriftTests(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.live, self.repo = Path(self._d.name) / 'live', Path(self._d.name) / 'repo'
        self.live.mkdir()
        self.repo.mkdir()

    def tearDown(self):
        self._d.cleanup()

    def test_identical_folders_report_no_difference_and_line_endings_do_not_count(self):
        (self.live / 'a.py').write_bytes(b'x = 1' + bytes([13, 10]))      # bytes: no platform newline translation
        (self.repo / 'a.py').write_bytes(b'x = 1' + bytes([10]))
        result = pd.compare(self.live, self.repo)
        self.assertEqual((result['changed'], result['live_only'], result['repo_only'], result['same']), ([], [], [], 1))

    def test_changed_and_live_only_files_are_found(self):
        write(self.live, 'a.py', 'x = 2')
        write(self.repo, 'a.py', 'x = 1')
        write(self.live, 'new_feature.py', 'y = 1')
        result = pd.compare(self.live, self.repo)
        self.assertEqual(result['changed'], ['a.py'])
        self.assertEqual(result['live_only'], ['new_feature.py'])

    def test_intentional_differences_are_not_reported(self):
        for name in ('hermes_node_workcopy.py', 'patch_guard.py', 'pablo_human_behavior.py'):
            write(self.live, name, 'x = 1')
        write(self.repo, 'test_clinic_pitch.py', 'x = 1')          # a test that exists only in git
        result = pd.compare(self.live, self.repo)
        self.assertEqual((result['live_only'], result['repo_only']), ([], []))

    def test_secrets_and_junk_are_never_read(self):
        for name in ('config.json', '.env', 'node.log', 'x.py.bak_2026', 'data.db'):
            write(self.live, name, 'SECRET')
        write(self.live, 'ok.py', 'x = 1')
        self.assertEqual(sorted(pd.python_files(self.live)), ['ok.py'])

    def test_sync_copies_live_over_repo_only_for_reported_files(self):
        write(self.live, 'a.py', 'x = 2')
        write(self.repo, 'a.py', 'x = 1')
        write(self.live, 'same.py', 's')
        write(self.repo, 'same.py', 's')
        result = pd.compare(self.live, self.repo)
        pd.sync(self.live, self.repo, result['changed'] + result['live_only'])
        self.assertEqual((self.repo / 'a.py').read_text(), 'x = 2')
        self.assertEqual(pd.compare(self.live, self.repo)['changed'], [])

    def test_main_exit_codes(self):
        write(self.live, 'a.py', 'x = 1')
        write(self.repo, 'a.py', 'x = 1')
        self.assertEqual(pd.main(['--live', str(self.live), '--repo', str(self.repo)]), 0)
        write(self.live, 'a.py', 'x = 2')
        self.assertEqual(pd.main(['--live', str(self.live), '--repo', str(self.repo)]), 1)
        self.assertEqual(pd.main(['--live', str(self.live / 'nope'), '--repo', str(self.repo)]), 2)


if __name__ == '__main__':
    unittest.main()
