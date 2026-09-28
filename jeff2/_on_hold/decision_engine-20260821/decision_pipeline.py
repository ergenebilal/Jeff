#!/usr/bin/env python3
"""Jeff 3.0 — Decision Pipeline
Structured karar mekanizması.
Problem → Alternatifler → Risk → Maliyet → Getiri → Karar → Günlük
"""
import json, os, sqlite3, uuid
from datetime import datetime

DB_PATH = os.path.expanduser("~/jeff2/decision_engine/decisions.db")

def _init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id TEXT PRIMARY KEY,
            problem TEXT NOT NULL,
            alternatives TEXT,
            risk_level TEXT,
            cost_estimate REAL,
            expected_return REAL,
            decision TEXT,
            rationale TEXT,
            status TEXT DEFAULT 'active',
            outcome TEXT DEFAULT 'beklemede',
            created_at TEXT,
            resolved_at TEXT,
            tags TEXT
        )
    """)
    conn.commit()
    return conn

def create_decision(problem, alternatives=None, risk_level="orta", 
                    cost_estimate=0, expected_return=0, tags=None):
    """Yeni karar kaydı"""
    conn = _init_db()
    decision_id = str(uuid.uuid4())[:8]
    now = datetime.now().isoformat()
    
    conn.execute("""
        INSERT INTO decisions (id, problem, alternatives, risk_level, 
            cost_estimate, expected_return, created_at, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (decision_id, problem, json.dumps(alternatives or []), 
          risk_level, cost_estimate, expected_return, now, 
          json.dumps(tags or [])))
    conn.commit()
    conn.close()
    return decision_id

def resolve_decision(decision_id, decision, rationale, outcome="basarili"):
    """Kararı çözümle"""
    conn = _init_db()
    now = datetime.now().isoformat()
    conn.execute("""
        UPDATE decisions SET decision=?, rationale=?, outcome=?,
            status='resolved', resolved_at=?
        WHERE id=?
    """, (decision, rationale, outcome, now, decision_id))
    conn.commit()
    conn.close()

def list_decisions(status=None, limit=20):
    """Kararları listele"""
    conn = _init_db()
    if status:
        rows = conn.execute(
            "SELECT * FROM decisions WHERE status=? ORDER BY created_at DESC LIMIT ?",
            (status, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM decisions ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    
    cols = ["id","problem","alternatives","risk_level","cost_estimate",
            "expected_return","decision","rationale","status","outcome",
            "created_at","resolved_at","tags"]
    return [dict(zip(cols, row)) for row in rows]

def get_stats():
    """Karar istatistikleri"""
    conn = _init_db()
    total = conn.execute("SELECT COUNT(*) FROM decisions").fetchone()[0]
    active = conn.execute("SELECT COUNT(*) FROM decisions WHERE status='active'").fetchone()[0]
    resolved = conn.execute("SELECT COUNT(*) FROM decisions WHERE status='resolved'").fetchone()[0]
    success = conn.execute("SELECT COUNT(*) FROM decisions WHERE outcome='basarili'").fetchone()[0]
    failed = conn.execute("SELECT COUNT(*) FROM decisions WHERE outcome='basarisiz'").fetchone()[0]
    conn.close()
    
    return {
        "total": total, "active": active, "resolved": resolved,
        "success": success, "failed": failed,
        "success_rate": round(success / resolved * 100, 1) if resolved else 0
    }

def print_report():
    stats = get_stats()
    active_decisions = list_decisions(status='active')
    
    report = f"""
## 🧠 Decision Engine — Karar Raporu
**Toplam:** {stats['total']} · **Aktif:** {stats['active']} · **Çözülen:** {stats['resolved']}
**Başarı:** {stats['success']} · **Başarısız:** {stats['failed']} · **Başarı Oranı:** %{stats['success_rate']}

"""
    if active_decisions:
        report += "### Bekleyen Kararlar\n\n"
        for d in active_decisions:
            risk_icon = {"dusuk": "🟢", "orta": "🟡", "yuksek": "🟠", "kritik": "🔴"}
            icon = risk_icon.get(d['risk_level'], '⚪')
            report += f"{icon} **{d['problem'][:60]}** | Maliyet: ${d['cost_estimate']} | Getiri: ${d['expected_return']}\n"
    
    return report

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        print(print_report())
    else:
        print("✅ Decision Engine hazır. Kullanım: python3 decision_pipeline.py report")
