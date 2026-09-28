# Jeff 2.0 — Otonom İşletim Sistemi

Jeff 2.0, AI işçilerini yöneten, gelir motorlarını çalıştıran ve her çıktıyı denetleyen otonom bir yönetim katmanıdır.

---

## Mimarı

```
SOUL.md (Anayasa)
    │
├── departments/       (5 yönetici departmanı)
├── engines/          (4 gelir motoru)
├── governance/       (verifier kapısı)
├── workers/          (işçi atama planı)
└── reports/          (günlük/haftalık/aylık raporlar)
```

---

## 5 Departman

| Departman | Görev | İşçi Sayısı |
|-----------|-------|-------------|
| **Büyüme** | Lead akışı, outbound/inbound, fırsat keşfi | 6 |
| **Ürün ve İçerik** | Dijital ürün, görsel+metin, içerik takvimi | 4 |
| **Teslimat ve Sistem** | Kod, deploy, altyapı, otomasyon | 3 |
| **Finans ve Risk** | Marj, maliyet, risk, token limit | 3 |
| **Hafıza ve Öğrenme** | SOP, içgörü, desen kaydı, arşiv | 3 |

---

## 4 Gelir Motoru

| Motor | Gelir Türü | İşleyiş |
|-------|-----------|---------|
| **Hizmet** | Proje/outsource | Lead → kapanış pipeline |
| **Fırsat Deney** | Yeni niş/test | Hipotez → deney → SOP |
| **İçerik ve Talep** | İnbound/güven | İçerik → talep → satış |
| **Dijital Ürün** | Pasif satış | Fikir → paket → lansman |

---

## Verifier Kapısı

Governance katmanı. Dışarı giden her şey denetlenir:

- **Serbest:** Araştırma, taslak, iç rapor
- **Jeff Onayı:** Kampanya, lansman, yeni motor testi
- **Bilal Onayı:** Fiyat, hukuk, yüksek harcama, marka riski

---

## İşleyiş

1. **Planla** — Departman hedef koyar
2. **Üret** — İşçi çalışır
3. **Denetle** — Verifier kapısından geçer
4. **Raporla** — Günlük/haftalık/aylık raporlanır
5. **Öğren** — Hafızaya yazılır, SOP'ye dönüşür

---

## Hızlı Başlangıç

```bash
ls ~/jeff2/departments/   # Departman charters
ls ~/jeff2/engines/        # Gelir motoru tanımları
ls ~/jeff2/governance/     # Verifier kuralları
ls ~/jeff2/reports/        # Rapor şablonları
```

Her dosya bağımsız okunabilir. Sıra önemli değil — yapı modülerdir.
