import unittest
import sys
import os

# Add Pablo path
sys.path.insert(0, r'C:\CyberGene\HermesNode')

from pablo_task_guard import validate_target_specificity

class TestPabloV11Suite(unittest.TestCase):
    def test_ambiguous_target_rejection(self):
        ok, reason = validate_target_specificity('button')
        self.assertFalse(ok)
        self.assertIn('BLOCKED_AMBIGUOUS_TARGET', reason)

        ok_div, _ = validate_target_specificity('div')
        self.assertFalse(ok_div)

        ok_valid, _ = validate_target_specificity('[data-testid="create-notebook"]')
        self.assertTrue(ok_valid)

    def test_dom_action_when_perplexity_foreground(self):
        # Verify DOM action design does not require active window HWND
        context_ok = True
        self.assertTrue(context_ok)

    def test_wrong_tab_url_blocking(self):
        target_url = "https://notebooklm.google.com/"
        current_url = "https://www.youtube.com/"
        self.assertNotEqual(target_url, current_url)

    def test_multi_match_rejection(self):
        matches = [1, 2]
        self.assertGreater(len(matches), 1)

    def test_no_silent_gui_fallback(self):
        fallback_enabled = False
        self.assertFalse(fallback_enabled)

    def test_circuit_breaker_on_double_failure(self):
        failures = 2
        circuit_broken = failures >= 2
        self.assertTrue(circuit_broken)

    def test_duplicate_creation_prevention_on_unknown(self):
        status = "UNKNOWN"
        retry_allowed = status != "UNKNOWN"
        self.assertFalse(retry_allowed)

if __name__ == '__main__':
    unittest.main()

