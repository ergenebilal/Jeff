#!/usr/bin/env python3
"""Episodic Memory — test suite."""
import json
import os
import sys
import tempfile
import unittest

import episodic_memory as em

# Test için geçici dosya
em.EPISODIC_PATH = tempfile.mktemp(suffix="-episodic.jsonl")


class TestEpisodicMemory(unittest.TestCase):
    """Episodic memory testleri."""

    def setUp(self):
        if os.path.exists(em.EPISODIC_PATH):
            os.unlink(em.EPISODIC_PATH)

    def tearDown(self):
        if os.path.exists(em.EPISODIC_PATH):
            os.unlink(em.EPISODIC_PATH)

    def test_record_creates_entry(self):
        """record() geçerli bir giriş oluşturmalı."""
        result = em.record("test", "deneme kaydı", sonuc="başarılı")
        self.assertIn("timestamp", result)
        self.assertEqual(result["olay_tipi"], "test")
        self.assertEqual(result["ozet"], "deneme kaydı")

    def test_recall_returns_recent(self):
        """recall() son kayıtları dönmeli."""
        em.record("olay_a", "ilk olay")
        em.record("olay_b", "ikinci olay")
        results = em.recall(limit=5)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["ozet"], "ikinci olay")  # reverse chronological

    def test_recall_filter_by_type(self):
        """recall() tip filtresiyle çalışmalı."""
        em.record("hata", "bir hata")
        em.record("basarı", "bir başarı")
        results = em.recall(olay_tipi="hata")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["olay_tipi"], "hata")

    def test_recall_limit(self):
        """recall() limit parametresine uymalı."""
        for i in range(5):
            em.record("test", f"olay {i}")
        results = em.recall(limit=3)
        self.assertEqual(len(results), 3)

    def test_recall_since(self):
        """recall() since filtresiyle çalışmalı."""
        em.record("eski", "çok eski")
        results_eski = em.recall(since="2100-01-01")
        self.assertEqual(len(results_eski), 0)

    def test_empty_file(self):
        """Boş dosyada recall çağrısı boş liste dönmeli."""
        results = em.recall()
        self.assertEqual(results, [])

    def test_get_recent_summary(self):
        """get_recent_summary() metin dönmeli."""
        em.record("sistem", "kontrol tamam", sonuc="başarılı")
        summary = em.get_recent_summary(days=7)
        self.assertIn("1 olay", summary)
        self.assertIn("sistem", summary)

    def test_count_by_type(self):
        """count_by_type() doğru dağılım dönmeli."""
        em.record("hata", "hata 1")
        em.record("hata", "hata 2")
        em.record("basarı", "başarı 1")
        counts = em.count_by_type()
        self.assertEqual(counts.get("hata"), 2)
        self.assertEqual(counts.get("basarı"), 1)

    def test_record_with_metadata(self):
        """record() metadata ile çalışmalı."""
        result = em.record("test", "meta test", metadata={"kritik": True, "puan": 95})
        self.assertEqual(result["metadata"]["kritik"], True)
        self.assertEqual(result["metadata"]["puan"], 95)


if __name__ == "__main__":
    print(f"🧪 Episodic Memory Test Suite")
    print(f"   Test file: {em.EPISODIC_PATH}")
    print()
    unittest.main(verbosity=2)
