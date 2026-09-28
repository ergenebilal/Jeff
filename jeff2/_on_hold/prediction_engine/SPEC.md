# Prediction Engine — Geçmişten Geleceğe
> **v1.0 SPEC | Jeff 3.0 Faz 4**

---

## 1. Business Case

Veri var ama geleceği tahmin edemiyoruz. Pipeline'daki 206 lead'den kaçı satışa dönüşecek? 
Hangi worker bu hafta boşta kalacak? Prediction Engine bu soruları cevaplar.

---

## 2. Dosya Yapısı

```
prediction_engine/
├── SPEC.md                  ← Bu dosya
├── trend_predictor.py       ← Trend tahmini
└── risk_predictor.py        ← Risk tahmini
```

## 3. Tahminler

| Tahmin | Kaynak | Yöntem |
|--------|--------|--------|
| Lead dönüşüm oranı | Pipeline geçmişi | Weighted average |
| Worker yükü | Board geçmişi | Simple trending |
| Hata riski | Circuit breaker log | Threshold scoring |
| Maliyet | Token tüketimi | Linear projection |
| İçerik performansı | Engagement metrikleri | Baseline comparison |

Her tahmin: `confidence score` + `risk level` + `recommended action`
