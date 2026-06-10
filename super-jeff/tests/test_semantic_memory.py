#!/usr/bin/env python3
"""Semantic Memory — test suite."""
import json
import os
import tempfile
import unittest

import semantic_memory as sm

sm.SEMANTIC_PATH = tempfile.mktemp(suffix="-semantic.json")


class TestSemanticMemory(unittest.TestCase):

    def setUp(self):
        if os.path.exists(sm.SEMANTIC_PATH):
            os.unlink(sm.SEMANTIC_PATH)

    def tearDown(self):
        if os.path.exists(sm.SEMANTIC_PATH):
            os.unlink(sm.SEMANTIC_PATH)

    def test_learn_new(self):
        """learn() yeni kavram oluşturmalı."""
        r = sm.learn("MCP", "Model Context Protocol", kategori="teknik", onem=9)
        self.assertEqual(r["kavram"], "MCP")
        self.assertEqual(r["onem"], 9)

    def test_learn_update(self):
        """learn() var olan kavramı güncellemeli."""
        sm.learn("test", "eski açıklama")
        r = sm.learn("test", "yeni açıklama")
        self.assertEqual(r["aciklama"], "yeni açıklama")

    def test_recall_found(self):
        """recall() var olan kavramı bulmalı."""
        sm.learn("DeepSeek", "AI modeli", kategori="AI")
        r = sm.recall("DeepSeek")
        self.assertIsNotNone(r)
        self.assertEqual(r["kavram"], "DeepSeek")

    def test_recall_not_found(self):
        """recall() olmayan kavram için None dönmeli."""
        r = sm.recall("varolmayan_kavram_12345")
        self.assertIsNone(r)

    def test_recall_increments_visit(self):
        """recall() ziyaret sayısını artırmalı."""
        sm.learn("visit_test", "test")
        r1 = sm.recall("visit_test")
        r2 = sm.recall("visit_test")
        self.assertEqual(r2["ziyaret_sayisi"], 2)

    def test_search(self):
        """search() kavram ve açıklamada arama yapmalı."""
        sm.learn("PostgreSQL", "veritabanı", kategori="teknik")
        sm.learn("Python", "programlama dili", kategori="teknik")
        results = sm.search("veritabanı")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["kavram"], "PostgreSQL")

    def test_search_by_kategori(self):
        """search() kategori filtresiyle çalışmalı."""
        sm.learn("a", "x", kategori="finans")
        sm.learn("b", "x", kategori="teknik")
        results = sm.search("x", kategori="finans")
        self.assertEqual(len(results), 1)

    def test_get_unvisited(self):
        """get_unvisited() yeni kavramları döndürmemeli."""
        sm.learn("yeni", "yeni kavram")
        uv = sm.get_unvisited(days=0)  # 0 gün = hemen unutulmuş
        self.assertEqual(len(uv), 1)

    def test_get_stats(self):
        """get_stats() doğru sayılar dönmeli."""
        sm.learn("a", "1", kategori="x")
        sm.learn("b", "2", kategori="y")
        stats = sm.get_stats()
        self.assertEqual(stats["toplam_kavram"], 2)


if __name__ == "__main__":
    print(f"🧪 Semantic Memory Test Suite")
    unittest.main(verbosity=2)
