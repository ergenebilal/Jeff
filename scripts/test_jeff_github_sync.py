"""Independent local Git-remote checks; no model, customer identity or live work."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from jeff_github_sync import (Blocked, allowed, capture, cycle, git, public_bytes, secret, private_settings, checked_sources)
from collect_windows_source import collect


class PrivacyTests(unittest.TestCase):
    def test_private_files_and_escape_paths_are_excluded(self):
        for name in ['SOUL.md', 'SOUL-old.md', 'jeff2/SOUL.md', 'USER.md', 'MEMORY.md',
                     '.env', 'gateway.env', 'config.yaml', 'source.py.bak-2026',
                     'evidence/proof.json', 'reports/personal.md', 'a.sqlite3',
                     '../outside.py', '/outside.py', 'C:\\private.py', 'screenshots/screen.png']:
            self.assertFalse(allowed(name), name)

    def test_source_files_are_in_scope(self):
        for name in ['scripts/source.py', 'pablo/new.py', 'integrations/tool/plugin.yaml',
                     'docs/operations/sync.md', '.gitignore', 'scripts/task.ps1']:
            self.assertTrue(allowed(name), name)

    def test_secret_patterns_and_literal_assignments_fail_closed(self):
        for data in [b'TOKEN=' + b'123456789:' + b'A' * 36,
                     b'KEY=' + b'sk-' + b'X' * 30,
                     b'auth_token = "' + b'not-a-safe-' + b'literal-value"',
                     b'{"password": "' + b'not-a-safe-' + b'literal-value"}',
                     b'-----BEGIN ' + b'PRIVATE KEY-----']:
            self.assertTrue(secret(data))
            with self.assertRaises(Blocked):
                public_bytes('script.py', data)

    def test_synthetic_placeholders_do_not_pass_as_real_keys(self):
        self.assertFalse(secret(b'API_KEY="fixture-key"'))
        self.assertFalse(secret(b'PASSWORD=os.environ["PASSWORD"]'))

    def test_private_adviser_context_is_omitted_only_in_public_copy(self):
        raw = 'DANISMAN_SABLON = """MÜKELLEF\nprivate fixture\nDÖRT KOVA\nvalues"""'.encode()
        result = public_bytes('jeff2/bridge/jeff_bridge_api.py', raw)
        self.assertNotIn(b'private fixture', result)
        self.assertIn('BAĞLAM'.encode(), result)
        self.assertIn(b'private fixture', raw)

    def test_changed_private_template_shape_is_blocked(self):
        with self.assertRaises(Blocked):
            public_bytes('jeff2/bridge/jeff_bridge_api.py', b'DANISMAN_SABLON = "changed"')

    def test_public_owner_setting_reads_environment_without_altering_original(self):
        identifier = b'123456789'
        raw = b'from __future__ import annotations\nowner = "123456789"\nnumber = 123456789\n'
        result = private_settings('source.py', raw, [identifier])
        self.assertNotIn(identifier, result)
        self.assertIn(identifier, raw)
        with patch.dict('os.environ', {'TELEGRAM_OWNER_CHAT_ID': 'anonymous-fixture'}):
            # Integer settings require numeric configuration; independently check string behavior.
            ns = {}
            exec(result.split(b'number =')[0], ns)
            self.assertEqual(ns['owner'], 'anonymous-fixture')

    def test_public_owner_setting_keeps_numeric_and_embedded_string_behavior(self):
        raw = b'number = 123456789\nurl = "prefix-123456789-suffix"\n'
        result = private_settings('source.py', raw, [b'123456789'])
        with patch.dict('os.environ', {'TELEGRAM_OWNER_CHAT_ID': '456'}):
            ns = {};exec(result, ns)
            self.assertEqual(ns['number'], 456)
            self.assertEqual(ns['url'], 'prefix-456-suffix')

    def test_unknown_private_setting_form_is_blocked(self):
        with self.assertRaises(Blocked):
            private_settings('source.py', b'url = f"prefix-123456789-{other}"', [b'123456789'])

    def test_only_exact_intentionally_invalid_fixture_can_be_exempted(self):
        fixture = b'def intentionally_broken(\n'
        digest = hashlib.sha256(fixture).hexdigest()
        checked_sources({'invalid_fixture.py': fixture}, {}, {'invalid_fixture.py': digest})
        with self.assertRaises(SyntaxError):
            checked_sources({'invalid_fixture.py': b'def changed_broken(\n'}, {}, {'invalid_fixture.py': digest})


class GitFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source'
        self.source.mkdir()
        self.remote = self.root / 'remote.git'
        subprocess.run(['git', 'init', '--bare', str(self.remote)], check=True, capture_output=True)
        git(self.source, 'init')
        git(self.source, 'config', 'user.name', 'Anonymous Fixture')
        git(self.source, 'config', 'user.email', 'fixture@example.invalid')
        (self.source / 'source.py').write_text('value = 1\n')
        git(self.source, 'add', 'source.py')
        git(self.source, 'commit', '-m', 'fixture seed')
        git(self.source, 'remote', 'add', 'origin', str(self.remote))
        git(self.source, 'push', 'origin', 'HEAD:refs/heads/seed')
        self.config = {'source_repo': str(self.source), 'mirror_repo': str(self.root / 'mirror'),
                       'remote': str(self.remote), 'seed_branch': 'seed', 'branch': 'codex/fixture-sync',
                       'state': str(self.root / 'state.json'), 'status': str(self.root / 'status.json'),
                       'settle_seconds': 10}

    def publish(self, first=100):
        self.assertEqual(cycle(self.config, now=first)['status'], 'waiting_stable')
        return cycle(self.config, now=first + 11)

    def test_uncommitted_changes_arrive_at_real_remote_without_changing_source_index(self):
        initial_index = (self.source / '.git/index').read_bytes()
        (self.source / 'source.py').write_text('value = 2\n')
        original_source_bytes = (self.source / 'source.py').read_bytes()
        result = self.publish()
        self.assertEqual(result['status'], 'published')
        data = git(self.remote, 'show', 'refs/heads/codex/fixture-sync:source.py')
        self.assertEqual(data, b'value = 2\n')
        self.assertEqual((self.source / '.git/index').read_bytes(), initial_index)
        self.assertEqual((self.source / 'source.py').read_bytes(), original_source_bytes)

    def test_two_different_editors_and_committed_edits_are_published(self):
        self.assertEqual(self.publish()['status'], 'published')
        (self.source / 'source.py').write_text('value = 3\n')
        self.assertEqual(self.publish(200)['status'], 'published')
        (self.source / 'tool.py').write_text('from pathlib import Path\n')
        git(self.source, 'add', 'tool.py')
        git(self.source, 'commit', '-m', 'other tool')
        self.assertEqual(self.publish(300)['status'], 'published')
        self.assertEqual(git(self.remote, 'show', 'refs/heads/codex/fixture-sync:tool.py'),
                         b'from pathlib import Path\n')

    def test_private_note_and_ignored_key_never_reach_remote(self):
        (self.source / 'SOUL.md').write_text('private fixture note')
        (self.source / '.env').write_text('TOKEN=' + 'sk-' + 'X' * 30)
        result = self.publish()
        self.assertEqual(result['status'], 'published')
        names = git(self.remote, 'ls-tree', '-r', '--name-only', 'refs/heads/codex/fixture-sync')
        self.assertNotIn(b'SOUL.md', names)
        self.assertNotIn(b'.env', names)

    def test_secret_in_new_source_blocks_publication(self):
        (self.source / 'bad.py').write_text('API_KEY="' + 'sk-' + 'X' * 30 + '"\n')
        result = cycle(self.config, now=100)
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['failure_class'], 'credential_gate')
        self.assertFalse(git(self.remote, 'show-ref', '--heads').find(b'codex/fixture-sync') >= 0)

    def test_broken_syntax_cannot_publish(self):
        (self.source / 'source.py').write_text('def broken(\n')
        result = self.publish()
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['failure_class'], 'SyntaxError')

    def test_edits_must_remain_stable_before_publication(self):
        self.assertEqual(cycle(self.config, now=100)['status'], 'waiting_stable')
        (self.source / 'source.py').write_text('value = 2\n')
        self.assertEqual(cycle(self.config, now=109)['status'], 'waiting_stable')
        self.assertEqual(cycle(self.config, now=110)['status'], 'waiting_stable')
        self.assertEqual(cycle(self.config, now=120)['status'], 'published')

    def test_source_change_during_capture_does_not_publish(self):
        cycle(self.config, now=100)
        original = capture
        calls = []
        def racing(config):
            if calls:
                (self.source / 'source.py').write_text('value = 99\n')
            calls.append(True)
            return original(config)
        with patch('jeff_github_sync.capture', side_effect=racing):
            result = cycle(self.config, now=111)
        self.assertEqual(result['failure_class'], 'source_changed_during_capture')

    def test_no_change_does_not_create_another_commit(self):
        first = self.publish()
        second = cycle(self.config, now=200)
        self.assertEqual(second['status'], 'no_change')
        self.assertEqual(second['last_success']['remote_commit'], first['remote_commit'])

    def test_unreachable_remote_preserves_retry_and_success_is_not_claimed(self):
        source_before = (self.source / 'source.py').read_bytes()
        self.config['remote'] = str(self.root / 'absent.git')
        result = self.publish()
        self.assertEqual(result['status'], 'blocked')
        self.assertIsNone(result['last_success'])
        # The original source remains recoverable and unmodified.
        self.assertEqual((self.source / 'source.py').read_bytes(), source_before)

    def test_personal_identifier_is_blocked_without_printing_value(self):
        self.config['private_identifiers'] = ['fixture-private-account']
        (self.source / 'source.py').write_text('account = "fixture-private-account"\n')
        result = cycle(self.config, now=100)
        self.assertEqual(result['failure_class'], 'personal_identifier_gate')
        self.assertNotIn('fixture-private-account', json.dumps(result))

    def test_missing_installed_source_is_a_coverage_failure(self):
        self.config['installed_sources'] = [{'source': str(self.root / 'missing.py'),
                                            'target': 'runtime-source/server/missing.py'}]
        self.assertEqual(cycle(self.config, now=100)['failure_class'], 'installed_source_missing')

    def test_windows_packet_is_verified_and_published(self):
        installed = self.root / 'installed'
        installed.mkdir()
        (installed / 'node.py').write_bytes(b'answer = 42\r\n')
        (installed / 'config.json').write_text('{"private":true}')
        (installed / 'pablo_human_behavior.py').write_text('private_fixture = True\n')
        packet = collect(installed)
        inbox = self.root / 'windows.json'
        inbox.write_text(json.dumps(packet))
        self.config['windows_inbox'] = str(inbox)
        result = self.publish()
        self.assertEqual(result['status'], 'published')
        self.assertEqual(git(self.remote, 'show', 'refs/heads/codex/fixture-sync:runtime-source/windows/node.py'),
                         b'answer = 42\n')
        self.assertNotIn('config.json', packet['files'])
        self.assertNotIn('pablo_human_behavior.py', packet['files'])

    def test_tampered_windows_packet_is_rejected(self):
        inbox = self.root / 'windows.json'
        inbox.write_text(json.dumps({'version': 1, 'files': {'node.py':
            {'content': 'dmFsdWUgPSAxCg==', 'sha256': '0' * 64}}}))
        self.config['windows_inbox'] = str(inbox)
        self.assertEqual(cycle(self.config, now=100)['failure_class'], 'windows_digest_invalid')

    def test_diverged_remote_never_gets_forced_overwritten(self):
        first = self.publish()
        external = self.root / 'external'
        subprocess.run(['git', 'clone', str(self.remote), str(external)], check=True, capture_output=True)
        git(external, 'checkout', '-b', 'external', 'origin/codex/fixture-sync')
        git(external, 'config', 'user.name', 'Anonymous Fixture')
        git(external, 'config', 'user.email', 'fixture@example.invalid')
        (external / 'external.py').write_bytes(b'value = 7\n')
        git(external, 'add', 'external.py');git(external, 'commit', '-m', 'external edit')
        git(external, 'push', 'origin', 'HEAD:refs/heads/codex/fixture-sync')
        other_head = git(external, 'rev-parse', 'HEAD').strip()
        mirror = Path(self.config['mirror_repo'])
        (mirror / 'local.py').write_bytes(b'value = 8\n')
        git(mirror, 'add', 'local.py');git(mirror, 'commit', '-m', 'unpublished edit')
        (self.source / 'source.py').write_bytes(b'value = 2\n')
        result = self.publish(200)
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(result['failure_class'], 'publication_history_diverged')
        self.assertEqual(git(self.remote, 'rev-parse', 'refs/heads/codex/fixture-sync').strip(), other_head)

    def test_source_deletion_is_recorded_only_in_public_copy(self):
        self.publish()
        (self.source / 'source.py').unlink()
        (self.source / 'replacement.py').write_bytes(b'value = 2\n')
        result = self.publish(200)
        self.assertEqual(result['status'], 'published')
        names = git(self.remote, 'ls-tree', '-r', '--name-only', 'refs/heads/codex/fixture-sync')
        self.assertNotIn(b'source.py', names)
        self.assertIn(b'replacement.py', names)
        self.assertFalse((self.source / 'source.py').exists())

    def test_legacy_seed_link_is_removed_from_public_copy_without_following_target(self):
        try:
            os.symlink('missing-outside-target', self.source / 'legacy-link.sh')
        except OSError:
            self.skipTest('Native symlink creation unavailable in this Windows session')
        git(self.source, 'add', 'legacy-link.sh');git(self.source, 'commit', '-m', 'legacy broken link')
        git(self.source, 'push', 'origin', 'HEAD:refs/heads/seed')
        result = self.publish()
        self.assertEqual(result['status'], 'published')
        self.assertTrue((self.source / 'legacy-link.sh').is_symlink())
        names = git(self.remote, 'ls-tree', '-r', '--name-only', 'refs/heads/codex/fixture-sync')
        self.assertNotIn(b'legacy-link.sh', names)


if __name__ == '__main__':
    unittest.main()
