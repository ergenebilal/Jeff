# Simulation Engine — Karar Simülasyonu
> **v1.0 SPEC | Jeff 3.0 Faz 4**

---

## 1. Business Case

Karar vermeden önce sonucu görmek isteriz. Simulation Engine, her alternatif için:
- Risk, maliyet, süre, ROI, başarı olasılığı hesaplar
- En uygun senaryoyu önerir

---

## 2. Dosya Yapısı

```
simulation_engine/
├── SPEC.md                  ← Bu dosya
└── scenario_planner.py      ← Senaryo planlayıcı
```

## 3. Örnek

```
Plan A: 5 worker → lead scraping → 100 yeni lead → $0 maliyet → 7 gün
Plan B: Mevcut pipeline → email outreach → 10 dönüşüm → $5 maliyet → 14 gün
Plan C: Dijital ürün lansmanı → pasif gelir → $0 maliyet → 30 gün

Öneri: Plan A + C kombinasyonu (en düşük risk, en yüksek getiri)
```
