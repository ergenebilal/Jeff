# Jeff 4.0 — Üst Seviye Multi-Agent Sistem Spec'i

**Tarih:** 10.08.2026
**Mevcut:** Jeff 3.0 (5 agent, Redis bus, 8 worker)
**Hedef:** Production-grade multi-agent orchestration

---

## 1. MEVCUT DURUM ANALİZİ

### Çalışan Bileşenler
- 5 Director Agent (gelisim, kreatif, sistem, finans, bilgi)
- 3 Worker Pool (kreatif, gelisim, shared)
- Redis message bus (pub/sub + queue)
- Health monitor (5 dk cron)
- Evidence gate (verify sistemi)

### Bilinen Kritik Bug'lar
| # | Bug | Etki | Durum |
|---|-----|------|-------|
| 1 | Redis LREM wildcard — processing queue temizlenmiyor | Queue sonsuza büyür | ⚠️ Aktif risk |
| 2 | Gateway timeout — 117K token context injection | Tüm LLM planları timeout | ✅ Partial fix (direkt API) |
| 3 | Health ping blindness — zombi agent tespit edilemiyor | Agent çalışırken hiçbir iş yapmayabilir | ⚠️ Aktif risk |
| 4 | EvidenceGate false PASS — 0 task → PASS | Boş çıktı = başarılı görünür | ⚠️ Aktif risk |
| 5 | Dead letter queue birikimi | Disk dolar, log boğulur | ⚠️ Aktif risk |
| 6 | Growth agent monoton döngü | Aynı sorguyu tekrar tekrar dener | ⚠️ Aktif risk |
| 7 | Worker content gateway timeout | İçerik üretimi çalışmaz | ⚠️ Aktif risk |

### Eksikler (Dünya Standardına Göre)
- Model tiering yok (tek model = tek nokta başarısızlık)
- Inter-agent communication sınırlı (sadece Redis pub/sub)
- Task routing akıllı değil (manuel/keyword)
- QA gate otomatik değil
- Self-healing yetersiz (3-strike ama düzeltme yok)
- Monitoring sadece health ping — iş metrikleri yok
- A2A (Agent-to-Agent) protokolü yok

---

## 2. JEFF 4.0 MİMARİSİ

### 2.1 Yeni Agent Yapısı

```
┌─────────────────────────────────────────────────────┐
│                  JEFF 4.0 CORE                       │
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  ORCHESTRATOR │  │   ROUTER    │  │   QA GATE   │ │
│  │  (Jeff CEO)   │  │  (Akıllı    │  │  (Otomatik  │ │
│  │               │  │   Dağıtıcı) │  │   Denetim)  │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
│         │                │                │         │
│  ┌──────┴────────────────┴────────────────┴──────┐  │
│  │              AGENT POOL (8 Agent)              │  │
│  │                                               │  │
│  │  🔵 Growth    — Lead bulma, pipeline          │  │
│  │  🟢 Kreatif   — İçerik, görsel, marka         │  │
│  │  🔴 Sistem    — Kod, deploy, altyapı          │  │
│  │  🟡 Finans    — Bütçe, maliyet, ROI           │  │
│  │  🟣 Bilgi     — Araştırma, SOP, arşiv         │  │
│  │  🟠 Satış     — Pitch, müzakere, kapanış      │  │
│  │  ⚪ Veri      — Analiz, rapor, metrik         │  │
│  │  🟤 Operasyon — Otomasyon, cron, iş akışı     │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │           WORKER POOL (12 Worker)            │    │
│  │                                             │    │
│  │  web_search | content | code | shell        │    │
│  │  python | file_read | file_write | deploy   │    │
│  │  research | design | email | notify         │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │         INFRASTRUCTURE LAYER                 │    │
│  │                                             │    │
│  │  Redis Bus | SQLite State | File Memory     │    │
│  │  Health Monitor | Metrics Collector         │    │
│  │  Event Logger | Dead Letter Handler         │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

### 2.2 Yeni Bileşenler

#### A) Intelligent Router
```python
class IntelligentRouter:
    """Görevi otomatik olarak doğru agent'a yönlendirir."""
    
    ROUTING_RULES = {
        "lead": ["gelisim", "satis"],
        "content": ["kreatif"],
        "code": ["sistem"],
        "budget": ["finans"],
        "research": ["bilgi", "veri"],
        "deploy": ["sistem", "operasyon"],
        "pitch": ["satis", "kreatif"],
        "metric": ["veri", "finans"],
    }
    
    def route(self, task: Task) -> Agent:
        # 1. Keyword matching
        # 2. Context analysis (LLM ile)
        # 3. Agent availability check
        # 4. Load balancing (en az yüklenen)
        # 5. Fallback: orchestrator
```

#### B) Enhanced QA Gate
```python
class QAGate:
    """Otomatik kalite denetimi — her çıkış denetlenir."""
    
    def verify(self, output, task) -> QAResult:
        checks = [
            self.check_completeness(output, task),    # Tamamlandı mı?
            self.check_accuracy(output, task),         # Doğru mu?
            self.check_quality(output, task),          # Kaliteli mi?
            self.check_safety(output, task),           # Güvenli mi?
            self.check_cost(output, task),             # Bütçe dahilinde mi?
        ]
        return QAGateResult(
            passed=all(c.passed for c in checks),
            checks=checks,
            score=sum(c.score for c in checks) / len(checks)
        )
```

#### C) Model Tiering
```python
MODEL_CONFIG = {
    "fast": {          # Basit işler: routing, filler, kontrol
        "model": "mi-v2.5",
        "cost": "$0",
        "use_for": ["routing", "triage", "simple_qa"]
    },
    "standard": {      # Orta işler: içerik, araştırma, analiz
        "model": "deepseek-v4-flash",
        "cost": "$0.27/M tokens",
        "use_for": ["content", "research", "analysis"]
    },
    "premium": {       # Zor işler: strateji, kod, karmaşık reasoning
        "model": "deepseek-v4-pro",
        "cost": "$1.10/M tokens",
        "use_for": ["strategy", "coding", "complex_reasoning"]
    }
}
```

#### D) Inter-Agent Communication (A2A)
```python
class AgentProtocol:
    """Agent'lar arası iletişimi standardize eder."""
    
    # Her agent şunları yapabilir:
    def request_help(self, from_agent, task, context):
        """Başka bir agent'tan yardım iste"""
        
    def share_insight(self, insight, target_agents):
        """Tespitini diğer agent'larla paylaş"""
    
    def handoff(self, task, to_agent, reason):
        """Görevi başka bir agent'a devret"""
    
    def broadcast(self, event):
        """Tüm agent'lara olay bildir"""
```

#### E) Metrics Collector
```python
class MetricsCollector:
    """İş metriklerini toplar ve raporlar."""
    
    METRICS = {
        "tasks_completed": counter,
        "tasks_failed": counter,
        "avg_completion_time": gauge,
        "revenue_generated": gauge,
        "leads_found": counter,
        "content_produced": counter,
        "cost_per_task": gauge,
        "agent_utilization": gauge,
        "error_rate": gauge,
    }
```

---

## 3. UYGULAMA PLANI

### Faz 0: Bug Fix (1 gün)
- [ ] Redis LREM wildcard fix
- [ ] Dead letter queue vacuum
- [ ] Growth agent rotation fix
- [ ] Worker content API redirect

### Faz 1: Altyapı (2 gün)
- [ ] Metrics collector oluştur
- [ ] Enhanced QA gate
- [ ] Model tiering config
- [ ] Event logger (JSONL)

### Faz 2: Agent Upgrade (3 gün)
- [ ] Yeni 3 agent ekle (satış, veri, operasyon)
- [ ] Intelligent router
- [ ] Inter-agent protocol
- [ ] Agent health scoring (ping değil, gerçek metrik)

### Faz 3: Orchestration (2 gün)
- [ ] Task priority queue
- [ ] Dependency resolution
- [ ] Parallel execution planner
- [ ] Rollback mechanism

### Faz 4: Self-Healing (1 gün)
- [ ] Auto-restart (3-strike → restart, sadece bildirim değil)
- [ ] Circuit breaker (LLM down → fallback model)
- [ ] Resource monitor (RAM/disk alarm)

### Faz 5: Dashboard (1 gün)
- [ ] Real-time agent status
- [ ] Task pipeline view
- [ ] Revenue tracker
- [ ] Error log viewer

---

## 4. BAŞARI KRİTERLERİ

| Metrik | Mevcut | Hedef |
|--------|--------|-------|
| Agent sayısı | 5 | 8 |
| Worker sayısı | 8 | 12 |
| Task completion rate | ~%60 | >%90 |
| Avg completion time | ~5 dk | <2 dk |
| Error recovery | Manuel | Otomatik |
| Monitoring | Health ping | Gerçek metrikler |
| Model maliyeti | $0 (tek model) | $0-5/ay (tiering) |
| Self-healing | 3-strike + bildirim | Otomatik restart + fallback |

---

## 5. RİSKLER

| Risk | Olasılık | Etki | Mitigasyon |
|------|----------|------|------------|
| Yeni agent'lar uyumsuz | Orta | Yüksek | Fazlı rollout, her faz test |
| Redis overload | Düşük | Yüksek | Queue limitleri, monitoring |
| Model maliyet artışı | Orta | Orta | Budget alerts, auto-downgrade |
| Karmaşıklık artışı | Yüksek | Orta | Dokümantasyon, modular tasarım |

---

## 6. ONAY

- [ ] Bilal onayı (bu spec)
- [ ] Faz 0 başlangıç
- [ ] Her faz sonrası demo
