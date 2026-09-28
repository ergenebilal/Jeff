# Multi-Tenant Architecture — Çok Müşterili Yapı
> **v1.0 SPEC | Jeff 3.0 Faz 5**

---

## 1. Business Case

Jeff tek bir işletme (ErgeneAI) için çalışıyor. Oysa altyapı, AgencyOS üzerinden 
zaten multi-tenant çalışabiliyor. Jeff tarafında da client izolasyonu yapılırsa
her müşteri için ayrı pipeline, board, worker seti çalıştırılabilir.

---

## 2. Dosya Yapısı

```
clients/
├── _template/               ← Yeni müşteri template'i
│   ├── board/               ← İzole kanban
│   ├── memory/              ← İzole hafıza
│   ├── pipelines/           ← İzole pipeline
│   └── config.yaml          ← Client konfigürasyonu
├── ergeneai/                ← Ana client (mevcut)
└── README.md                ← Client yönetimi
```

## 3. Her Client İçin İzolasyon

| Bileşen | İzolasyon |
|---------|-----------|
| Kanban board | Ayrı SQLite DB |
| Worker state | Ayrı profil |
| Pipeline | Ayrı feed.jsonl |
| Memory | Ayrı EXECUTIVE_MEMORY.md |
| SOP | Ayrı sops/ dizini |
| KPI | Ayrı metrikler |
| Raporlar | Ayrı reports/ dizini |

## 4. Geçiş Planı

1. `clients/_template/` oluştur → template yapısı
2. `clients/ergeneai/` → mevcut yapıyı client klasörüne taşı
3. `client_manager.py` → yeni client aç/kapa script'i
