"""Real localhost HTTP checks against the active Pablo /execute handler."""

import ctypes
import importlib.util
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import Mock, patch

import requests


PABLO_DIR = Path(__file__).resolve().parents[2] / 'pablo'
sys.path.insert(0, str(PABLO_DIR))


class DirectExecuteBoundaryTests(unittest.TestCase):
    def setUp(self):
        platform_modules = {name: Mock() for name in (
            'win32gui', 'win32con', 'win32process', 'pyautogui',
            'mss', 'mss.tools', 'PIL', 'PIL.Image', 'PIL.ImageGrab')}
        spec = importlib.util.spec_from_file_location(
            'pablo_active_execute_test', PABLO_DIR / 'hermes_node.py')
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, platform_modules), patch.object(ctypes, 'windll', Mock(), create=True):
            spec.loader.exec_module(module)
        self.node = module
        module.CONFIG.update(auth_token='fixture-only', allowed_ips=[])
        self.guard = Mock()
        self.guard.execute.return_value = {'request_id': 'read-1', 'status': 'SUCCESS', 'ok': True}
        module.task_guard = lambda: self.guard
        self.server = module.HTTPServer(('127.0.0.1', 0), module.PabloRequestHandler)
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.url = f'http://127.0.0.1:{self.server.server_port}/execute'

    def test_side_effect_is_denied_before_taskguard_and_read_only_remains_available(self):
        risky = (
            ('shell', {'command': 'echo no'}),
            ('vision_grounding', {'click': True}),
            ('screenshot', {'save_path': 'C:/fixture/overwrite.txt'}),
            ('browser_read', {'url': 'http://127.0.0.1/private'}),
        )
        for action, params in risky:
            with self.subTest(action=action):
                denied = requests.post(self.url, json={'action': action, 'params': params,
                                                       'request_id': 'direct-1'},
                                       headers={'X-Pablo-Token': 'fixture-only'}, timeout=2)
                self.assertEqual(denied.status_code, 403)
                self.assertEqual(denied.json()['status'], 'BLOCKED')
                self.guard.execute.assert_not_called()
        replay = requests.post(self.url, json={'action': 'shell', 'params': {},
                                               'request_id': 'direct-1'},
                               headers={'X-Pablo-Token': 'fixture-only'}, timeout=2)
        self.assertEqual(replay.status_code, 403)
        self.guard.execute.assert_not_called()
        unauthenticated = requests.post(self.url, json={'action': 'ping', 'params': {}}, timeout=2)
        self.assertEqual(unauthenticated.status_code, 401)
        allowed = requests.post(self.url, json={'action': 'ping', 'params': {},
                                                'request_id': 'read-1'},
                                headers={'X-Pablo-Token': 'fixture-only'}, timeout=2)
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()['status'], 'SUCCESS')
        self.assertEqual(self.guard.execute.call_count, 1)


if __name__ == '__main__':
    unittest.main()
