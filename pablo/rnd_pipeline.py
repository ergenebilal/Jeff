#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CYBERGENE AUTONOMOUS R&D PIPELINE & DATABASE
--------------------------------------------
7/24 Otonom AR-GE ve İnovasyon Katmanı:
- research_topics: Küresel AI & Klinik otomasyonu araştırmaları, pazar zekası
- experiments: İzole sandbox kod deneyleri, benchmarklar ve performans testleri
- daily_digests: Bilal Ergene için her sabah üretilen yönetici brifingleri
"""

import sqlite3
import json
import time
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, Any, List, Optional

RND_DIR = Path(r"C:\CyberGene\RnD")
DB_PATH = RND_DIR / "rnd_pipeline.db"
RND_DIR.mkdir(parents=True, exist_ok=True)

@contextmanager
def get_rnd_db():
    conn = sqlite3.connect(str(DB_PATH), timeout=15.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    try:
        yield conn
    finally:
        conn.close()

def init_rnd_db():
    """AR-GE tablolarını ve indekslerini oluşturur."""
    with get_rnd_db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS research_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,      -- 'TECH_WATCH', 'CLINIC_INTELLIGENCE', 'EXPERIMENT', 'REGULATION'
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            findings_json TEXT,          -- Yapısal bulgular, promptlar, mimariler (JSON)
            source_urls TEXT,            -- Kaynak bağlantıları (JSON array)
            impact_score INTEGER DEFAULT 3, -- 1-5 arası etki derecesi
            status TEXT DEFAULT 'COMPLETED',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic_id INTEGER,
            title TEXT NOT NULL,
            hypothesis TEXT NOT NULL,
            code_path TEXT,
            execution_status TEXT DEFAULT 'PENDING', -- 'PENDING', 'RUNNING', 'SUCCESS', 'FAILED'
            benchmark_result_json TEXT,
            duration_ms INTEGER DEFAULT 0,
            is_promoted_to_core INTEGER DEFAULT 0, -- 1 ise canlı koda aktarıldı
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (topic_id) REFERENCES research_topics (id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS daily_digests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            digest_date TEXT NOT NULL UNIQUE, -- 'YYYY-MM-DD'
            title TEXT NOT NULL,
            tech_highlight TEXT NOT NULL,
            clinic_highlight TEXT NOT NULL,
            experiment_highlight TEXT NOT NULL,
            full_report_path TEXT,
            sent_to_telegram INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_research_cat ON research_topics (category);
        CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments (execution_status);
        CREATE INDEX IF NOT EXISTS idx_digests_date ON daily_digests (digest_date);
        """)
        conn.commit()

class RnDPipeline:

    @staticmethod
    def add_research_topic(
        category: str,
        title: str,
        summary: str,
        findings: Dict[str, Any] = None,
        source_urls: List[str] = None,
        impact_score: int = 3
    ) -> int:
        findings_json = json.dumps(findings or {}, ensure_ascii=False)
        sources_json = json.dumps(source_urls or [], ensure_ascii=False)
        with get_rnd_db() as conn:
            cur = conn.execute("""
            INSERT INTO research_topics (category, title, summary, findings_json, source_urls, impact_score)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (category, title, summary, findings_json, sources_json, impact_score))
            conn.commit()
            return cur.lastrowid

    @staticmethod
    def list_topics(category: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        with get_rnd_db() as conn:
            if category:
                rows = conn.execute("SELECT * FROM research_topics WHERE category = ? ORDER BY id DESC LIMIT ?", (category, limit)).fetchall()
            else:
                rows = conn.execute("SELECT * FROM research_topics ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    def record_experiment(
        title: str,
        hypothesis: str,
        code_path: str = "",
        topic_id: Optional[int] = None,
        execution_status: str = "SUCCESS",
        benchmark_results: Dict[str, Any] = None,
        duration_ms: int = 0,
        is_promoted: bool = False
    ) -> int:
        bench_json = json.dumps(benchmark_results or {}, ensure_ascii=False)
        with get_rnd_db() as conn:
            cur = conn.execute("""
            INSERT INTO experiments (topic_id, title, hypothesis, code_path, execution_status, benchmark_result_json, duration_ms, is_promoted_to_core)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (topic_id, title, hypothesis, code_path, execution_status, bench_json, duration_ms, 1 if is_promoted else 0))
            conn.commit()
            return cur.lastrowid

    @staticmethod
    def create_daily_digest(
        digest_date: str,
        title: str,
        tech_highlight: str,
        clinic_highlight: str,
        experiment_highlight: str,
        full_report_path: str = ""
    ) -> int:
        with get_rnd_db() as conn:
            cur = conn.execute("""
            INSERT INTO daily_digests (digest_date, title, tech_highlight, clinic_highlight, experiment_highlight, full_report_path)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(digest_date) DO UPDATE SET
                title=excluded.title,
                tech_highlight=excluded.tech_highlight,
                clinic_highlight=excluded.clinic_highlight,
                experiment_highlight=excluded.experiment_highlight,
                full_report_path=excluded.full_report_path
            """, (digest_date, title, tech_highlight, clinic_highlight, experiment_highlight, full_report_path))
            conn.commit()
            return cur.lastrowid

    @staticmethod
    def mark_digest_sent(digest_date: str):
        with get_rnd_db() as conn:
            conn.execute("UPDATE daily_digests SET sent_to_telegram = 1 WHERE digest_date = ?", (digest_date,))
            conn.commit()

    @staticmethod
    def get_latest_digest() -> Optional[Dict[str, Any]]:
        with get_rnd_db() as conn:
            row = conn.execute("SELECT * FROM daily_digests ORDER BY id DESC LIMIT 1").fetchone()
            return dict(row) if row else None

if __name__ == "__main__":
    init_rnd_db()
    print("RnD Database initialized at:", DB_PATH)
