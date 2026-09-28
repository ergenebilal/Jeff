"""The secret gate catches a synthetic token without printing its value."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ci_secret_scan import findings


class SecretScanTests(unittest.TestCase):
    def test_synthetic_secret_is_detected(self):
        synthetic = b'123456789:' + b'A' * 36
        self.assertEqual(findings(b'TOKEN=' + synthetic), [(1, 'telegram_bot_token')])

    def test_placeholder_is_ignored(self):
        self.assertEqual(findings(b'API_KEY="fixture-api-key"'), [])


if __name__ == '__main__':
    unittest.main()
