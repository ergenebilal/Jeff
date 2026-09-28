# Decision Engine — Structured Karar Mekanizması
> **v1.0 SPEC | Jeff 3.0 Faz 1**

---

## 1. Business Case

Kararlar dağınık: decisions.jsonl var ama structured pipeline yok. 
Her önemli karar aynı süreçten geçmeli, kayıt altına alınmalı, sonuçları takip edilmeli.

---

## 2. SPEC

### Dosya Yapısı
```
decision_engine/
├── SPEC.md                ← Bu dosya
├── decision_pipeline.py   ← Karar pipeline'ı
└── decisions.db           ← SQLite karar veritabanı
```

### Karar Pipeline'ı
```
Problem → Alternatifler → Risk → Maliyet → Getiri → Karar → Günlük
```

### decision_pipeline.py
```python
def create_decision(problem, alternatives, risk_level, cost, expected_return):
    """Yeni karar kaydı oluştur"""
    
def list_decisions(status=None, limit=20):
    """Kararları listele"""
    
def resolve_decision(decision_id, outcome, notes=""):
    """Kararı çözümle (başarılı/başarısız)"""
    
def get_stats():
    """Karar istatistikleri"""
```

### decisions.db Şeması
```sql
CREATE TABLE decisions (
    id TEXT PRIMARY KEY,
    problem TEXT NOT NULL,
    alternatives TEXT,       -- JSON array
    risk_level TEXT,         -- dusuk/orta/yuksek/kritik
    cost_estimate REAL,
    expected_return REAL,
    decision TEXT,           -- secilen alternatif
    rationale TEXT,
    status TEXT,             -- active/resolved/cancelled
    outcome TEXT,            -- basarili/basarisiz/beklemede
    created_at TEXT,
    resolved_at TEXT,
    tags TEXT
);
```
