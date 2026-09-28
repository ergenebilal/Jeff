#!/usr/bin/env python3
"""Brain v3 — brain-state.py unit testleri (3 senaryo)."""
import json
import os
import sys
import tempfile
import unittest

# Test için state.json'u /tmp/test-brain.json'a yönlendir
TEST_STATE = tempfile.mktemp(suffix="-brain-test.json")

# Modülü import etmeden önce STATE_PATH'i değiştir
import importlib.util
# brain-state.py (hyphen) → importlib ile yükle
_MODULE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brain-state.py")
_spec = importlib.util.spec_from_file_location("brain_state", _MODULE_PATH)
bs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bs)
bs.STATE_PATH = TEST_STATE


class TestBrainState(unittest.TestCase):
    """brain-state.py test suite — 3 senaryo."""

    def setUp(self):
        """Her test öncesi temiz state."""
        bs.save(bs.default_state())

    def tearDown(self):
        """Her test sonrası dosyayı temizle."""
        if os.path.exists(TEST_STATE):
            os.unlink(TEST_STATE)

    # ── Senaryo 1: set_phase ──────────────────────────────────

    def test_set_phase_valid(self):
        """Geçerli faz değişikliği çalışmalı."""
        result = bs.set_phase("execute")
        self.assertTrue(result)
        state = bs.load()
        self.assertEqual(state["phase"], "execute")
        self.assertIsNotNone(state["phase_started"])

    def test_set_phase_same_phase(self):
        """Aynı faz tekrar set edilince state değişmemeli."""
        bs.set_phase("discover")
        bs.set_phase("discover")  # tekrar
        state = bs.load()
        self.assertEqual(state["phase"], "discover")

    def test_set_phase_invalid(self):
        """Geçersiz fazda False dönmeli ve state değişmemeli."""
        result = bs.set_phase("invalid-phase")
        self.assertFalse(result)
        state = bs.load()
        self.assertEqual(state["phase"], "discover")

    def test_set_phase_resets_errors(self):
        """Faz değişince error sayacı sıfırlanmalı."""
        bs.add_error()
        bs.add_error()
        bs.set_phase("execute")
        state = bs.load()
        self.assertEqual(state["errors_turn"], 0)
        self.assertEqual(state["errors_session"], 2)  # session total korunur

    # ── Senaryo 2: add_error ───────────────────────────────────

    def test_add_error_increments(self):
        """add_error turn ve session sayaçlarını artırmalı."""
        count = bs.add_error()
        self.assertEqual(count, 1)
        state = bs.load()
        self.assertEqual(state["errors_turn"], 1)
        self.assertEqual(state["errors_session"], 1)

    def test_add_error_multiple(self):
        """3 hata art arda turn=3, session=3 olmalı."""
        for _ in range(3):
            bs.add_error()
        state = bs.load()
        self.assertEqual(state["errors_turn"], 3)
        self.assertEqual(state["errors_session"], 3)

    def test_add_error_after_reset(self):
        """reset_turn sonrası turn sıfırlanır, session korunur."""
        bs.add_error()
        bs.add_error()
        bs.reset_turn()
        bs.add_error()
        state = bs.load()
        self.assertEqual(state["errors_turn"], 1)
        self.assertEqual(state["errors_session"], 3)

    # ── Senaryo 3: add_decision ────────────────────────────────

    def test_add_decision_basic(self):
        """Temel karar ekleme çalışmalı."""
        bs.add_decision("test karar", "deneme")
        state = bs.load()
        self.assertEqual(len(state["decisions"]), 1)
        self.assertEqual(state["decisions"][0]["decision"], "test karar")
        self.assertEqual(state["decisions"][0]["reason"], "deneme")

    def test_add_decision_with_alternatives(self):
        """Alternatifli karar ekleme."""
        bs.add_decision("seçim A", "çünkü X", alternatives="seçenek B, seçenek C")
        state = bs.load()
        self.assertEqual(len(state["decisions"]), 1)
        self.assertEqual(state["decisions"][0]["alternatives"], "seçenek B, seçenek C")

    def test_add_decision_multiple(self):
        """Birden çok karar eklenebilmeli."""
        bs.add_decision("karar 1", "sebep 1")
        bs.add_decision("karar 2", "sebep 2")
        bs.add_decision("karar 3", "sebep 3")
        state = bs.load()
        self.assertEqual(len(state["decisions"]), 3)
        self.assertEqual(state["decisions"][-1]["decision"], "karar 3")

    def test_add_decision_has_timestamp(self):
        """Her kararda timestamp olmalı."""
        bs.add_decision("zaman testi", "şimdi")
        state = bs.load()
        self.assertIsNotNone(state["decisions"][0].get("timestamp"))

    # ── Ek: get_summary ──────────────────────────────────────

    def test_get_summary_format(self):
        """get_summary doğru formatta çıktı üretmeli."""
        bs.set_phase("execute")
        summary = bs.get_summary()
        self.assertIn("EXECUTE", summary)
        self.assertIn("hata:0", summary)
        self.assertIn("$", summary)

    def test_get_summary_with_task(self):
        """Task set edildiğinde özette görünmeli."""
        state = bs.load()
        state["current_task"] = "test-gorev"
        bs.save(state)
        summary = bs.get_summary()
        self.assertIn("test-gorev", summary)


if __name__ == "__main__":
    print("🧪 Brain v3 — brain-state.py test suite")
    print(f"   Test state: {TEST_STATE}")
    print()
    unittest.main(verbosity=2)
