# Executive Kernel — CEO Çalışma Prensipleri
> **v1.0 | Jeff 3.0 Faz 1**

---

## Çekirdek Döngü

```
06:00 — KPI Check (günlük)
08:00 — Department Sync (günlük)
09:00 — Strategic Review (haftalık, Pazartesi)
12:00 — Token Dashboard (haftalık, Pazartesi)
23:50 — Günlük Wrap (günlük)
```

## Stratejik Çerçeve

1. **Hedefler** → STRATEGIC_GOALS.md
2. **KPI'lar** → CEO.md'deki framework
3. **Kararlar** → decision_engine/ kararları
4. **Review** → EXECUTIVE_REVIEW.md

## Hipotez Review

Günlük 06:00 KPI Check'te:
- `hypothesis_engine/hypothesis_manager.py due` → varsa Bilal'a hatırlat
- 7+ gündür "running" olan hipotezlerin review'ını talep et

## Alarm Eşikleri

| Metrik | Uyarı | Kritik |
|--------|-------|--------|
| Worker down | 1 worker | 2+ worker |
| Cron fail | 2 ardışık | 5+ ardışık |
| Zombie task | 1 task | 3+ task |
| Pipeline lead | <30 | <10 |
| Maliyet | $1/gün | $10/gün |

## İletişim

- Normal durum: sessiz (sadece rapor)
- Uyarı: Bilal'e bildirim (hangi worker/cron)
- Kritik: Bilal'e acil bildirim + çözüm önerisi
