"""Regression checks for the Jeff server migration."""

import importlib
import os
import unittest
from unittest.mock import patch

from scripts import alfred_daemon


class JeffServerAddressTests(unittest.TestCase):
    def test_alfred_uses_new_server_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            module = importlib.reload(alfred_daemon)
            self.assertEqual(module.JEFF_HOST, "13.140.183.88")
            self.assertEqual(module.JEFF_RESPONSE_URL, "http://13.140.183.88:7789/response")

    def test_alfred_environment_override_remains_supported(self):
        with patch.dict(os.environ, {"JEFF_HOST": "127.0.0.1"}):
            module = importlib.reload(alfred_daemon)
            self.assertEqual(module.JEFF_RESPONSE_URL, "http://127.0.0.1:7789/response")
        importlib.reload(alfred_daemon)


if __name__ == "__main__":
    unittest.main()
